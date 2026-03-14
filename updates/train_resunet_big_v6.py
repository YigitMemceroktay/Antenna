"""
train_resunet_big_v6.py  —  BigResUNet v6 (= Big v4 + Optuna HPO hyperparameters)

Big v4 = SmoothResUNet1D + CosineAnnealingLR + early stopping.
Big v6 keeps the same v4 architecture/scheduler but applies HPO-tuned hyperparameters
found by hpo_resunet.py (50 trials, 150 epochs each, best val=0.02671):
  lr=6.16e-4, weight_decay=1.89e-5, batch_size=16
  w_ri=0.248, w_slope=0.0017, w_curv=0.019, w_passivity=0.199

Key insight: w_slope≈0 (was 0.10), lr is the most impactful param (42% importance).

COMPARISON TABLE:
  Model   scheduler              early_stop  best_val
  Big v2  CosineAnnealing(300)   NO          0.0307
  Big v4  CosineAnnealing(500)   YES(p=40)   0.0296  ← base
  Big v6  CosineAnnealing(500)   YES(p=40)   ?       ← v4 + HPO params (this file)
"""

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


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

class ResBlock1D(nn.Module):
    """Conv-BN-GELU → Conv-BN → + skip → GELU."""

    def __init__(self, in_ch: int, out_ch: int) -> None:
        super().__init__()
        self.conv1 = nn.Conv1d(in_ch, out_ch, kernel_size=3, padding=1)
        self.bn1   = nn.BatchNorm1d(out_ch)
        self.conv2 = nn.Conv1d(out_ch, out_ch, kernel_size=3, padding=1)
        self.bn2   = nn.BatchNorm1d(out_ch)
        self.skip  = nn.Conv1d(in_ch, out_ch, kernel_size=1) if in_ch != out_ch else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        s = self.skip(x)
        x = F.gelu(self.bn1(self.conv1(x)))
        x = self.bn2(self.conv2(x))
        return F.gelu(x + s)


class LearnableGaussianSmooth1D(nn.Module):
    """
    Differentiable per-channel Gaussian smoothing with fixed sigma.
    Mirrors Antenna NN's self.smooth() but applied to both output channels jointly.

    sigma=1.527 was determined empirically via an initial learnable-sigma training
    run; it is now fixed (non-trainable buffer).
    """

    def __init__(self, filter_size: int = 41, sigma: float = 1.527) -> None:
        super().__init__()
        self.filter_size = filter_size
        self.register_buffer("logsigma", torch.tensor(float(np.log(sigma))))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, 2, L)
        n      = self.filter_size
        sigma  = torch.exp(self.logsigma)
        hw     = 3.0 * sigma
        t      = torch.linspace(0.0, 1.0, steps=n, device=x.device)
        t      = 2.0 * hw * t - hw                            # centre at 0
        kernel = torch.exp(-0.5 * (t / sigma) ** 2)
        kernel = kernel / kernel.sum()                        # (n,)

        # apply same kernel to both channels
        kernel_2ch = kernel.view(1, 1, n).expand(2, 1, n)    # (2, 1, n)
        pad        = (n - 1) // 2
        x_pad      = F.pad(x, (pad, pad), mode="reflect")
        return F.conv1d(x_pad, kernel_2ch, groups=2)          # (B, 2, L)


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class SmoothResUNet1D(nn.Module):
    """
    BigResUNet1D (base_ch=128) + fixed Gaussian smooth output layer (σ=1.527).

    Architecture identical to BigResUNet1D except the final step:
        out_head: Conv1d(128 → 2, k=1)  → (B, 2, L)
        smooth:   LearnableGaussianSmooth1D(filter_size=41, sigma=1.527)  ← NEW
    """

    def __init__(
        self,
        input_dim: int = 11,
        target_len: int = 201,
        base_ch: int = 128,
        smooth_filter: int = 41,
    ) -> None:
        super().__init__()
        self.target_len   = target_len
        self.pos_channels = 16

        self.cond_mlp = nn.Sequential(
            nn.Linear(input_dim, base_ch * 2),
            nn.GELU(),
            nn.Linear(base_ch * 2, base_ch),
            nn.GELU(),
        )

        enc_in = base_ch + self.pos_channels  # 128 + 16 = 144

        self.enc1       = ResBlock1D(enc_in,      base_ch)
        self.enc2       = ResBlock1D(base_ch,     base_ch * 2)
        self.bottleneck = ResBlock1D(base_ch * 2, base_ch * 4)

        self.up2  = nn.ConvTranspose1d(base_ch * 4, base_ch * 2, kernel_size=2, stride=2)
        self.dec2 = ResBlock1D(base_ch * 4, base_ch * 2)

        self.up1  = nn.ConvTranspose1d(base_ch * 2, base_ch, kernel_size=2, stride=2)
        self.dec1 = ResBlock1D(base_ch * 2, base_ch)

        self.out_head = nn.Conv1d(base_ch, 2, kernel_size=1)
        self.smooth   = LearnableGaussianSmooth1D(filter_size=smooth_filter)

    def _positional_encoding(self, length: int, device: torch.device) -> torch.Tensor:
        pos   = torch.linspace(0, 1, steps=length, device=device)[None, None, :]
        feats = []
        for k in range(1, self.pos_channels // 2 + 1):
            feats.append(torch.sin(2 * np.pi * k * pos))
            feats.append(torch.cos(2 * np.pi * k * pos))
        return torch.cat(feats, dim=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b = x.shape[0]

        cond = self.cond_mlp(x).unsqueeze(-1).expand(-1, -1, self.target_len)
        pe   = self._positional_encoding(self.target_len, x.device).expand(b, -1, -1)
        f0   = torch.cat([cond, pe], dim=1)

        e1 = self.enc1(f0)
        p1 = F.avg_pool1d(e1, kernel_size=2, stride=2)

        e2 = self.enc2(p1)
        p2 = F.avg_pool1d(e2, kernel_size=2, stride=2)

        bn = self.bottleneck(p2)

        u2 = self.up2(bn)
        if u2.shape[-1] != e2.shape[-1]:
            e2 = F.interpolate(e2, size=u2.shape[-1], mode="linear", align_corners=False)
        d2 = self.dec2(torch.cat([u2, e2], dim=1))

        u1 = self.up1(d2)
        if u1.shape[-1] != e1.shape[-1]:
            e1 = F.interpolate(e1, size=u1.shape[-1], mode="linear", align_corners=False)
        d1 = self.dec1(torch.cat([u1, e1], dim=1))

        out = self.out_head(d1)
        if out.shape[-1] != self.target_len:
            out = F.interpolate(out, size=self.target_len, mode="linear", align_corners=False)

        out = self.smooth(out)   # learnable Gaussian smooth
        return out


# ---------------------------------------------------------------------------
# Loss  (5 terms — w_mag now uses magnitude RSE instead of dB RSE)
# ---------------------------------------------------------------------------

def compute_loss(
    pred: torch.Tensor,
    target: torch.Tensor,
    w_ri: float,
    w_mag: float,
    mag_eps: float,
    w_slope: float,
    w_curv: float,
    w_passivity: float,
) -> torch.Tensor:
    mse = nn.MSELoss()

    real_p, imag_p = pred[:, 0, :],   pred[:, 1, :]
    real_t, imag_t = target[:, 0, :], target[:, 1, :]

    mag_p = torch.sqrt(real_p**2 + imag_p**2 + 1e-12)
    mag_t = torch.sqrt(real_t**2 + imag_t**2 + 1e-12)

    # Magnitude RSE (physically correct — aligns with evaluation metric)
    mag_loss = torch.mean(((mag_p - mag_t) ** 2) / (mag_t**2 + mag_eps))

    db_p = 20.0 * torch.log10(torch.clamp(mag_p, min=1e-8))
    db_t = 20.0 * torch.log10(torch.clamp(mag_t, min=1e-8))

    slope_p = db_p[:, 1:] - db_p[:, :-1]
    slope_t = db_t[:, 1:] - db_t[:, :-1]

    curv_p = slope_p[:, 1:] - slope_p[:, :-1]
    curv_t = slope_t[:, 1:] - slope_t[:, :-1]

    passivity = torch.mean(torch.relu(mag_p - 1.0) ** 2)

    return (
        w_ri          * mse(pred, target)
        + w_mag       * mag_loss
        + w_slope     * mse(slope_p, slope_t)
        + w_curv      * mse(curv_p, curv_t)
        + w_passivity * passivity
    )


# ---------------------------------------------------------------------------
# Data loading  (identical to BigResUNet)
# ---------------------------------------------------------------------------

def load_lhs_data(root: Path) -> tuple[np.ndarray, np.ndarray]:
    lhs_dir     = root / "data" / "LHS"
    input_files = sorted(lhs_dir.glob("input_trials_done_LHS_n20_rounded_seed*.csv"))
    if not input_files:
        raise FileNotFoundError("No LHS input files found in data/LHS")
    x_all, y_all = [], []
    for input_path in input_files:
        seed      = input_path.stem.split("seed")[-1]
        real_path = lhs_dir / f"real_initial_LHS_n20_rounded_seed{seed}.csv"
        imag_path = lhs_dir / f"imag_initial_LHS_n20_rounded_seed{seed}.csv"
        if not (real_path.exists() and imag_path.exists()):
            continue
        x_df    = pd.read_csv(input_path)[INPUT_COLUMNS]
        real_df = pd.read_csv(real_path)
        imag_df = pd.read_csv(imag_path)
        n       = min(len(x_df), len(real_df), len(imag_df))
        x_all.append(x_df.values[:n].astype(np.float32))
        y_all.append(np.stack([real_df.values[:n], imag_df.values[:n]], axis=1).astype(np.float32))
    if not x_all:
        raise RuntimeError("No valid LHS tuples found")
    return np.concatenate(x_all, axis=0), np.concatenate(y_all, axis=0)


def load_old_excel_data(root: Path) -> tuple[np.ndarray, np.ndarray]:
    old = root / "old" / "data"
    x   = pd.read_excel(old / "input_parameters.xlsx")[INPUT_COLUMNS].values.astype(np.float32)
    r   = pd.read_excel(old / "reel.xlsx").values.astype(np.float32)
    i   = pd.read_excel(old / "imaginary.xlsx").values.astype(np.float32)
    n   = min(len(x), len(r), len(i))
    return x[:n], np.stack([r[:n], i[:n]], axis=1)


def split_indices(n: int, val_ratio: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng   = np.random.default_rng(seed)
    idx   = np.arange(n)
    rng.shuffle(idx)
    n_val = max(1, int(n * val_ratio))
    return idx[n_val:], idx[:n_val]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(model: nn.Module, loader: DataLoader, device: torch.device, args: argparse.Namespace) -> float:
    model.eval()
    losses = []
    with torch.no_grad():
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            pred   = model(xb)
            loss   = compute_loss(
                pred, yb,
                w_ri=args.w_ri, w_mag=args.w_mag,
                mag_eps=args.mag_eps,
                w_slope=args.w_slope, w_curv=args.w_curv,
                w_passivity=args.w_passivity,
            )
            losses.append(loss.item())
    return float(np.mean(losses)) if losses else float("nan")


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train(args: argparse.Namespace) -> None:
    root    = Path(args.project_root).resolve()
    out_dir = (root / args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.dataset == "old_excel":
        x_raw, y = load_old_excel_data(root)
    else:
        x_raw, y = load_lhs_data(root)

    scaler   = MinMaxScaler(feature_range=(-1, 1))
    x_scaled = scaler.fit_transform(x_raw).astype(np.float32)

    tr_idx, va_idx = split_indices(len(x_scaled), args.val_ratio, args.seed)
    x_train = torch.tensor(x_scaled[tr_idx], dtype=torch.float32)
    y_train = torch.tensor(y[tr_idx],         dtype=torch.float32)
    x_val   = torch.tensor(x_scaled[va_idx],  dtype=torch.float32)
    y_val   = torch.tensor(y[va_idx],          dtype=torch.float32)

    if args.cpu:
        device = torch.device("cpu")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    train_loader = DataLoader(TensorDataset(x_train, y_train), batch_size=args.batch_size, shuffle=True)
    val_loader   = DataLoader(TensorDataset(x_val,   y_val),   batch_size=args.batch_size, shuffle=False)

    model = SmoothResUNet1D(
        input_dim=x_train.shape[1],
        target_len=y_train.shape[-1],
        base_ch=args.base_channels,
        smooth_filter=args.smooth_filter,
    ).to(device)

    n_params   = sum(p.numel() for p in model.parameters() if p.requires_grad)
    sigma_fixed = float(np.exp(model.smooth.logsigma.item()))
    print(f"SmoothResUNet1D  |  base_ch={args.base_channels}  |  trainable params: {n_params:,}")
    print(f"Device: {device}  |  fixed sigma: {sigma_fixed:.3f}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_val      = float("inf")
    best_state    = None
    history       = []
    patience_ctr  = 0
    stopped_epoch = args.epochs

    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            pred = model(xb)
            loss = compute_loss(
                pred, yb,
                w_ri=args.w_ri, w_mag=args.w_mag,
                mag_eps=args.mag_eps,
                w_slope=args.w_slope, w_curv=args.w_curv,
                w_passivity=args.w_passivity,
            )
            loss.backward()
            optimizer.step()
            losses.append(loss.item())

        scheduler.step()
        train_loss = float(np.mean(losses))
        val_loss   = evaluate(model, val_loader, device, args)
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})

        if val_loss < best_val:
            best_val     = val_loss
            best_state   = {k: v.detach().cpu() for k, v in model.state_dict().items()}
            patience_ctr = 0
        else:
            patience_ctr += 1

        if epoch % args.log_every == 0 or epoch == 1:
            print(f"epoch={epoch:4d}  train={train_loss:.6f}  val={val_loss:.6f}  patience={patience_ctr}/{args.patience}")

        if patience_ctr >= args.patience:
            print(f"\nEarly stopping at epoch {epoch} (patience={args.patience}). Best val: {best_val:.6f}")
            stopped_epoch = epoch
            break

    if stopped_epoch == args.epochs:
        print(f"epoch={stopped_epoch:4d}  train={train_loss:.6f}  val={val_loss:.6f}")

    if best_state is not None:
        model.load_state_dict(best_state)

    model_path   = out_dir / args.model_name
    scaler_path  = out_dir / args.scaler_name
    history_path = out_dir / args.history_name
    meta_path    = out_dir / args.meta_name

    torch.save(model.state_dict(), model_path)
    joblib.dump(scaler, scaler_path)
    pd.DataFrame(history).to_csv(history_path, index=False)

    meta = {
        "model": "SmoothResUNet1D",
        "dataset": args.dataset,
        "base_channels": args.base_channels,
        "trainable_params": n_params,
        "motivation": "Big v6: v4 (CosineAnnealingLR + early stopping) + Optuna HPO hyperparameters.",
        "stopped_epoch": stopped_epoch,
        "loss_weights": {
            "w_ri":        args.w_ri,
            "w_mag":       args.w_mag,
            "mag_loss":    "magnitude RSE",
            "w_slope":     args.w_slope,
            "w_curv":      args.w_curv,
            "w_passivity": args.w_passivity,
        },
        "smooth_filter_size": args.smooth_filter,
        "fixed_sigma":        sigma_fixed,
        "n_samples":          int(len(x_scaled)),
        "n_train":            int(len(tr_idx)),
        "n_val":              int(len(va_idx)),
        "best_val_loss":      float(best_val),
        "model_path":         str(model_path),
        "scaler_path":        str(scaler_path),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"\nSaved model:  {model_path}")
    print(f"Saved scaler: {scaler_path}")
    print(f"Best val loss: {best_val:.6f}")
    print(f"Fixed sigma:   {sigma_fixed:.4f}")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train BigResUNet v6 — Big v4 + HPO hyperparameters")
    parser.add_argument("--project-root",  type=str,   default=".")
    parser.add_argument("--dataset",       type=str,   default="old_excel", choices=["old_excel", "lhs"])
    parser.add_argument("--output-dir",    type=str,   default="NNModel")
    parser.add_argument("--model-name",    type=str,   default="trained_model_resunet_v6.pt")
    parser.add_argument("--scaler-name",   type=str,   default="scaler_resunet_v6.gz")
    parser.add_argument("--history-name",  type=str,   default="history_resunet_v6.csv")
    parser.add_argument("--meta-name",     type=str,   default="meta_resunet_v6.json")

    parser.add_argument("--epochs",        type=int,   default=500)
    parser.add_argument("--patience",      type=int,   default=40)
    # HPO-tuned training params (batch=16 vs v4's 32, lr=6.16e-4 vs 8e-4, wd smaller)
    parser.add_argument("--batch-size",    type=int,   default=16)
    parser.add_argument("--lr",            type=float, default=6.16e-4)
    parser.add_argument("--weight-decay",  type=float, default=1.887e-5)
    parser.add_argument("--val-ratio",     type=float, default=0.2)
    parser.add_argument("--seed",          type=int,   default=42)
    parser.add_argument("--base-channels", type=int,   default=128)
    parser.add_argument("--smooth-filter", type=int,   default=41)

    # HPO-tuned loss weights (w_mag=1.0 reference; w_slope≈0 is key finding)
    parser.add_argument("--w-ri",          type=float, default=0.2482)
    parser.add_argument("--w-mag",         type=float, default=1.00)
    parser.add_argument("--mag-eps",       type=float, default=1e-4)
    parser.add_argument("--w-slope",       type=float, default=0.0017)
    parser.add_argument("--w-curv",        type=float, default=0.01856)
    parser.add_argument("--w-passivity",   type=float, default=0.19933)

    parser.add_argument("--log-every",     type=int,   default=10)
    parser.add_argument("--cpu",           action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    torch.manual_seed(42)
    np.random.seed(42)
    args = parse_args()
    train(args)
