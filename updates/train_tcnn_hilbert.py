from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset


INPUT_COLUMNS = [
    "length of patch",
    "width of patch",
    "height of patch",
    "height of substrate",
    "height of solder resist layer",
    "radius of the probe",
    "c_pad",
    "c_antipad",
    "c_probe",
    "dielectric constant of substrate",
    "dielectric constant of solder resist layer",
]


def build_gaussian_kernel(kernel_size: int, sigma: torch.Tensor, device: torch.device) -> torch.Tensor:
    half = (kernel_size - 1) / 2.0
    x = torch.linspace(-half, half, steps=kernel_size, device=device)
    kernel = torch.exp(-0.5 * (x / sigma.clamp_min(1e-4)) ** 2)
    kernel = kernel / kernel.sum()
    return kernel.view(1, 1, kernel_size)


def hilbert_imag(x: torch.Tensor) -> torch.Tensor:
    n = x.shape[-1]
    spectrum = torch.fft.fft(x, dim=-1)
    h = torch.zeros(n, dtype=spectrum.dtype, device=x.device)

    if n % 2 == 0:
        h[0] = 1
        h[n // 2] = 1
        h[1 : n // 2] = 2
    else:
        h[0] = 1
        h[1 : (n + 1) // 2] = 2

    analytic = torch.fft.ifft(spectrum * h, dim=-1)
    return analytic.imag


class TCNNHilbert(nn.Module):
    def __init__(self, input_dim: int = 11, target_len: int = 201, seed_len: int = 25) -> None:
        super().__init__()
        self.target_len = target_len
        self.seed_len = seed_len
        self.seed_channels = 32
        self.log_sigma = nn.Parameter(torch.tensor(0.0))

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 96),
            nn.Tanh(),
            nn.Linear(96, 160),
            nn.Tanh(),
            nn.Linear(160, self.seed_channels * seed_len),
            nn.Tanh(),
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose1d(self.seed_channels, 32, kernel_size=5, stride=2, padding=2, output_padding=1),
            nn.Tanh(),
            nn.ConvTranspose1d(32, 16, kernel_size=5, stride=2, padding=2, output_padding=1),
            nn.Tanh(),
            nn.ConvTranspose1d(16, 1, kernel_size=4, stride=2, padding=1),
        )

    def smooth(self, x: torch.Tensor, kernel_size: int = 41) -> torch.Tensor:
        if kernel_size % 2 == 0:
            kernel_size += 1
        sigma = torch.exp(self.log_sigma)
        kernel = build_gaussian_kernel(kernel_size, sigma, x.device)
        x = F.pad(x, (kernel_size // 2, kernel_size // 2), mode="reflect")
        return F.conv1d(x, kernel)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        z = z.view(x.shape[0], self.seed_channels, self.seed_len)
        y = self.decoder(z)
        if y.shape[-1] != self.target_len:
            y = F.interpolate(y, size=self.target_len, mode="linear", align_corners=False)
        y = self.smooth(y)

        real = y[:, 0, :]
        imag = hilbert_imag(real)
        return torch.stack([real, imag], dim=1)


class TCNNDual(nn.Module):
    def __init__(self, input_dim: int = 11, target_len: int = 201, seed_len: int = 25) -> None:
        super().__init__()
        self.target_len = target_len
        self.seed_len = seed_len
        self.seed_channels = 32
        self.log_sigma = nn.Parameter(torch.tensor(0.0))

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 96),
            nn.Tanh(),
            nn.Linear(96, 160),
            nn.Tanh(),
            nn.Linear(160, self.seed_channels * seed_len),
            nn.Tanh(),
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose1d(self.seed_channels, 32, kernel_size=5, stride=2, padding=2, output_padding=1),
            nn.Tanh(),
            nn.ConvTranspose1d(32, 16, kernel_size=5, stride=2, padding=2, output_padding=1),
            nn.Tanh(),
            nn.ConvTranspose1d(16, 2, kernel_size=4, stride=2, padding=1),
        )

    def smooth(self, x: torch.Tensor, kernel_size: int = 41) -> torch.Tensor:
        if kernel_size % 2 == 0:
            kernel_size += 1
        sigma = torch.exp(self.log_sigma)
        kernel = build_gaussian_kernel(kernel_size, sigma, x.device)
        kernel = kernel.repeat(x.shape[1], 1, 1)
        x = F.pad(x, (kernel_size // 2, kernel_size // 2), mode="reflect")
        return F.conv1d(x, kernel, groups=x.shape[1])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        z = z.view(x.shape[0], self.seed_channels, self.seed_len)
        y = self.decoder(z)
        if y.shape[-1] != self.target_len:
            y = F.interpolate(y, size=self.target_len, mode="linear", align_corners=False)
        y = self.smooth(y)
        return y


def create_model(model_type: str, input_dim: int, target_len: int) -> nn.Module:
    if model_type == "hilbert":
        return TCNNHilbert(input_dim=input_dim, target_len=target_len)
    if model_type == "dual":
        return TCNNDual(input_dim=input_dim, target_len=target_len)
    raise ValueError(f"Unsupported model_type: {model_type}")


def load_lhs_data(root: Path) -> tuple[np.ndarray, np.ndarray]:
    lhs_dir = root / "data" / "LHS"
    input_files = sorted(lhs_dir.glob("input_trials_done_LHS_n20_rounded_seed*.csv"))
    if not input_files:
        raise FileNotFoundError("No LHS input files found in data/LHS")

    x_all = []
    y_all = []
    for input_path in input_files:
        seed = input_path.stem.split("seed")[-1]
        real_path = lhs_dir / f"real_initial_LHS_n20_rounded_seed{seed}.csv"
        imag_path = lhs_dir / f"imag_initial_LHS_n20_rounded_seed{seed}.csv"
        if not (real_path.exists() and imag_path.exists()):
            continue

        x_df = pd.read_csv(input_path)
        x_df = x_df[INPUT_COLUMNS]
        real_df = pd.read_csv(real_path)
        imag_df = pd.read_csv(imag_path)

        x = x_df.values.astype(np.float32)
        real = real_df.values.astype(np.float32)
        imag = imag_df.values.astype(np.float32)

        n = min(len(x), len(real), len(imag))
        x_all.append(x[:n])
        y_all.append(np.stack([real[:n], imag[:n]], axis=1))

    if not x_all:
        raise RuntimeError("No valid (input, real, imag) triples found.")

    x = np.concatenate(x_all, axis=0)
    y = np.concatenate(y_all, axis=0)
    return x, y


def load_old_excel_data(root: Path) -> tuple[np.ndarray, np.ndarray]:
    data_dir = root / "old" / "data"
    input_path = data_dir / "input_parameters.xlsx"
    real_path = data_dir / "reel.xlsx"
    imag_path = data_dir / "imaginary.xlsx"

    if not input_path.exists() or not real_path.exists() or not imag_path.exists():
        raise FileNotFoundError("Missing old/data Excel files (input_parameters.xlsx, reel.xlsx, imaginary.xlsx)")

    x_df = pd.read_excel(input_path)
    x_df = x_df[INPUT_COLUMNS]
    real_df = pd.read_excel(real_path)
    imag_df = pd.read_excel(imag_path)

    x = x_df.values.astype(np.float32)
    real = real_df.values.astype(np.float32)
    imag = imag_df.values.astype(np.float32)
    n = min(len(x), len(real), len(imag))
    y = np.stack([real[:n], imag[:n]], axis=1)
    return x[:n], y


def split_indices(n: int, val_ratio: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    rng.shuffle(idx)
    n_val = max(1, int(n * val_ratio))
    val_idx = idx[:n_val]
    train_idx = idx[n_val:]
    return train_idx, val_idx


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> float:
    model.eval()
    mse = nn.MSELoss()
    losses = []
    with torch.no_grad():
        for xb, yb in loader:
            xb = xb.to(device)
            yb = yb.to(device)
            pred = model(xb)
            losses.append(mse(pred, yb).item())
    return float(np.mean(losses)) if losses else float("nan")


def compute_loss(
    pred: torch.Tensor,
    target: torch.Tensor,
    mode: str,
    db_weight: float,
    slope_weight: float,
    passivity_weight: float,
) -> torch.Tensor:
    mse = nn.MSELoss()

    real_pred = pred[:, 0, :]
    imag_pred = pred[:, 1, :]
    real_true = target[:, 0, :]
    imag_true = target[:, 1, :]

    mag_pred = torch.sqrt(real_pred**2 + imag_pred**2 + 1e-12)
    mag_true = torch.sqrt(real_true**2 + imag_true**2 + 1e-12)

    base_loss: torch.Tensor
    if mode == "ri":
        base_loss = mse(pred, target)
    elif mode == "mag":
        base_loss = mse(mag_pred, mag_true)
    elif mode == "mag_db":
        mag_pred_db = 20.0 * torch.log10(torch.clamp(mag_pred, min=1e-8))
        mag_true_db = 20.0 * torch.log10(torch.clamp(mag_true, min=1e-8))
        base_loss = mse(mag_pred_db, mag_true_db)
    elif mode == "mag_db_hybrid":
        mag_pred_db = 20.0 * torch.log10(torch.clamp(mag_pred, min=1e-8))
        mag_true_db = 20.0 * torch.log10(torch.clamp(mag_true, min=1e-8))
        base_loss = mse(mag_pred, mag_true) + db_weight * mse(mag_pred_db, mag_true_db)
    else:
        raise ValueError(f"Unknown loss mode: {mode}")

    if slope_weight > 0:
        mag_pred_db = 20.0 * torch.log10(torch.clamp(mag_pred, min=1e-8))
        mag_true_db = 20.0 * torch.log10(torch.clamp(mag_true, min=1e-8))
        slope_pred = mag_pred_db[:, 1:] - mag_pred_db[:, :-1]
        slope_true = mag_true_db[:, 1:] - mag_true_db[:, :-1]
        base_loss = base_loss + slope_weight * mse(slope_pred, slope_true)

    if passivity_weight > 0:
        passivity_penalty = torch.mean(torch.relu(mag_pred - 1.0) ** 2)
        base_loss = base_loss + passivity_weight * passivity_penalty

    return base_loss


def evaluate_with_loss(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    mode: str,
    db_weight: float,
    slope_weight: float,
    passivity_weight: float,
) -> float:
    model.eval()
    losses = []
    with torch.no_grad():
        for xb, yb in loader:
            xb = xb.to(device)
            yb = yb.to(device)
            pred = model(xb)
            losses.append(
                compute_loss(
                    pred,
                    yb,
                    mode=mode,
                    db_weight=db_weight,
                    slope_weight=slope_weight,
                    passivity_weight=passivity_weight,
                ).item()
            )
    return float(np.mean(losses)) if losses else float("nan")


def train(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    out_dir = (root / args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.dataset == "lhs":
        x_raw, y = load_lhs_data(root)
    elif args.dataset == "old_excel":
        x_raw, y = load_old_excel_data(root)
    else:
        raise ValueError(f"Unsupported dataset: {args.dataset}")
    scaler = MinMaxScaler(feature_range=(-1, 1))
    x_scaled = scaler.fit_transform(x_raw).astype(np.float32)

    train_idx, val_idx = split_indices(len(x_scaled), args.val_ratio, args.seed)
    x_train = torch.tensor(x_scaled[train_idx], dtype=torch.float32)
    y_train = torch.tensor(y[train_idx], dtype=torch.float32)
    x_val = torch.tensor(x_scaled[val_idx], dtype=torch.float32)
    y_val = torch.tensor(y[val_idx], dtype=torch.float32)

    train_loader = DataLoader(TensorDataset(x_train, y_train), batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(x_val, y_val), batch_size=args.batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    model = create_model(args.model_type, input_dim=x_train.shape[1], target_len=y_train.shape[-1]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    best_val = float("inf")
    best_state = None
    history = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        batch_losses = []
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)

            optimizer.zero_grad(set_to_none=True)
            pred = model(xb)
            loss = compute_loss(
                pred,
                yb,
                mode=args.loss_mode,
                db_weight=args.db_weight,
                slope_weight=args.slope_weight,
                passivity_weight=args.passivity_weight,
            )
            loss.backward()
            optimizer.step()
            batch_losses.append(loss.item())

        scheduler.step()
        train_loss = float(np.mean(batch_losses))
        val_loss = evaluate_with_loss(
            model,
            val_loader,
            device,
            mode=args.loss_mode,
            db_weight=args.db_weight,
            slope_weight=args.slope_weight,
            passivity_weight=args.passivity_weight,
        )
        history.append({"epoch": epoch, "train_mse": train_loss, "val_mse": val_loss})

        if val_loss < best_val:
            best_val = val_loss
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}

        if epoch % args.log_every == 0 or epoch == 1 or epoch == args.epochs:
            print(f"epoch={epoch:4d} train_mse={train_loss:.6f} val_mse={val_loss:.6f}")

    if best_state is not None:
        model.load_state_dict(best_state)

    model_path = out_dir / args.model_name
    scaler_path = out_dir / args.scaler_name
    history_path = out_dir / args.history_name
    meta_path = out_dir / args.meta_name

    torch.save(model.state_dict(), model_path)
    joblib.dump(scaler, scaler_path)
    pd.DataFrame(history).to_csv(history_path, index=False)

    meta = {
        "model": "TCNN",
        "model_type": args.model_type,
        "dataset": args.dataset,
        "loss_mode": args.loss_mode,
        "db_weight": args.db_weight,
        "slope_weight": args.slope_weight,
        "passivity_weight": args.passivity_weight,
        "input_columns": INPUT_COLUMNS,
        "target_length": int(y.shape[-1]),
        "n_samples": int(len(x_scaled)),
        "n_train": int(len(train_idx)),
        "n_val": int(len(val_idx)),
        "best_val_mse": float(best_val),
        "device": str(device),
        "model_path": str(model_path),
        "scaler_path": str(scaler_path),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Saved model: {model_path}")
    print(f"Saved scaler: {scaler_path}")
    print(f"Best validation MSE: {best_val:.6f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train TCNN+Hilbert model for antenna S-parameter prediction")
    parser.add_argument("--project-root", type=str, default=".")
    parser.add_argument("--output-dir", type=str, default="NNModel")
    parser.add_argument("--model-name", type=str, default="trained_model_tcnn_hilbert.pt")
    parser.add_argument("--scaler-name", type=str, default="scaler_tcnn_hilbert.gz")
    parser.add_argument("--history-name", type=str, default="history_tcnn_hilbert.csv")
    parser.add_argument("--meta-name", type=str, default="meta_tcnn_hilbert.json")
    parser.add_argument("--dataset", type=str, default="lhs", choices=["lhs", "old_excel"])
    parser.add_argument("--model-type", type=str, default="hilbert", choices=["hilbert", "dual"])
    parser.add_argument("--epochs", type=int, default=400)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--loss-mode", type=str, default="ri", choices=["ri", "mag", "mag_db", "mag_db_hybrid"])
    parser.add_argument("--db-weight", type=float, default=0.1)
    parser.add_argument("--slope-weight", type=float, default=0.0)
    parser.add_argument("--passivity-weight", type=float, default=0.0)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--log-every", type=int, default=20)
    parser.add_argument("--cpu", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    torch.manual_seed(42)
    np.random.seed(42)
    args = parse_args()
    train(args)
