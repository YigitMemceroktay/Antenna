"""
train_antenna_nn_nsamples.py  —  AntennaNN (old NN) training with sample-size control

Architecture: MLP(11→60→60→60, Tanh) + deconv layers → 2×201 output
Loss: same 3-term AntennaNN Huber loss as ResUNet v9 (ri + F-FFT + mag)
Data: old_excel only
"""

from __future__ import annotations

import argparse
import json
import math
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
    "length of patch", "width of patch", "height of patch",
    "height of substrate", "height of solder resist layer",
    "radius of the probe", "c_pad", "c_antipad", "c_probe",
    "dielectric constant of substrate", "dielectric constant of solder resist layer",
]

_K_IDX = torch.cat([torch.arange(0, 40), torch.arange(161, 201)])


class AddCoords1D(nn.Module):
    def forward(self, out: torch.Tensor) -> torch.Tensor:
        in_batch, _, in_w = out.shape
        width_coords = torch.linspace(-1, 1, steps=in_w, device=out.device)
        wc = width_coords.repeat(in_batch, 1, 1)
        return torch.cat((out, wc), 1)


class AntennaNeuralNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.logsigma = nn.Parameter(torch.ones(1))
        self.filter_size = 41
        self.add_coords = AddCoords1D()
        self.linear = nn.Sequential(
            nn.Linear(11, 60), nn.Tanh(),
            nn.Linear(60, 60), nn.Tanh(),
            nn.Linear(60, 60), nn.Tanh(),
        )
        self.deconv1 = nn.Sequential(
            nn.ConvTranspose1d(60, 40, kernel_size=21, stride=1), nn.Tanh(),
        )
        self.deconv2 = nn.Sequential(
            nn.ConvTranspose1d(40, 40, kernel_size=7, stride=3), nn.Tanh(),
        )
        self.deconv3 = nn.Sequential(
            nn.ConvTranspose1d(41, 2, kernel_size=3, stride=3), nn.Tanh(),
        )

    def smooth(self, x: torch.Tensor) -> torch.Tensor:
        n = self.filter_size
        x = F.pad(x, ((n - 1) // 2, (n - 1) // 2), mode="reflect")
        sigma = torch.exp(self.logsigma).unsqueeze(-1).unsqueeze(-1)
        sigma = sigma.repeat((1, 1, n))
        hw = 3 * sigma
        xx = torch.linspace(0, 1, steps=n, device=x.device).unsqueeze(0).unsqueeze(0)
        xx = xx.repeat((x.shape[1], 1, 1))
        xx = 2 * hw * xx - hw
        gauss = 1 / (2 * math.pi * sigma ** 2) * torch.exp(-1 / (2 * (sigma ** 2)) * xx ** 2)
        gauss_sum = gauss.sum(dim=2).unsqueeze(-1).repeat((1, 1, gauss.shape[-1]))
        gauss = gauss / gauss_sum
        return F.conv1d(x, gauss, groups=x.shape[1])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.linear(x)
        out = out.view(len(x), 60, 1)
        out = self.deconv1(out)
        out = self.deconv2(out)
        out = self.add_coords(out)
        out = self.deconv3(out)
        return self.smooth(out)


# ---------------------------------------------------------------------------
# Loss  — AntennaNN Huber loss (3 terms, PyTorch differentiable)
# ---------------------------------------------------------------------------

def _huber(diff: torch.Tensor, delta: float) -> torch.Tensor:
    """Element-wise Huber: quadratic for |diff|<delta, linear otherwise."""
    return torch.where(
        diff < delta,
        0.5 * diff ** 2 / delta,
        diff - 0.5 * delta,
    )


def compute_loss(
    pred: torch.Tensor,
    target: torch.Tensor,
    beta: float,
    alfa: float,
    w_filter: float,
    wmag: float,
    k_idx: torch.Tensor,
) -> torch.Tensor:
    """
    Replicates AntennaNN's huber_loss from retrain_neuralnet.ipynb.

    Term 1: Huber(pred_ri, target_ri) with delta=beta
    Term 2: Huber on filtered FFT (high-freq only) with delta=alfa, weight=w_filter
    Term 3: Huber on magnitude with delta=alfa, weight=wmag
    """
    # ---- Term 1: Huber on real/imag ----------------------------------------
    diff_ri  = torch.abs(pred - target)          # (B, 2, L)
    loss_ri  = torch.mean(_huber(diff_ri, beta))

    # ---- Term 2: F-FFT Huber ------------------------------------------------
    real_p = pred[:, 0, :]
    imag_p = pred[:, 1, :]
    real_t = target[:, 0, :]
    imag_t = target[:, 1, :]

    s_pred = torch.complex(real_p, imag_p)
    s_true = torch.complex(real_t, imag_t)
    fft_pred = torch.fft.fft(s_pred, dim=-1)
    fft_true = torch.fft.fft(s_true, dim=-1)

    k = k_idx.to(pred.device)
    diff_fft_re = torch.abs(fft_pred.real[:, k] - fft_true.real[:, k])
    diff_fft_im = torch.abs(fft_pred.imag[:, k] - fft_true.imag[:, k])

    loss_fft = torch.mean(_huber(diff_fft_re, alfa) + _huber(diff_fft_im, alfa))

    # ---- Term 3: Magnitude Huber --------------------------------------------
    mag_pred = torch.sqrt(real_p ** 2 + imag_p ** 2 + 1e-12)
    mag_true = torch.sqrt(real_t ** 2 + imag_t ** 2 + 1e-12)
    diff_mag = torch.abs(mag_pred - mag_true)
    loss_mag = torch.mean(_huber(diff_mag, alfa))

    return loss_ri + loss_fft * w_filter + loss_mag * wmag


# ---------------------------------------------------------------------------
# Data loading  (old_excel only — no leakage)
# ---------------------------------------------------------------------------

def load_old_excel_data(root: Path) -> tuple[np.ndarray, np.ndarray]:
    old = root / "old" / "data"
    x   = pd.read_excel(old / "input_parameters.xlsx")[INPUT_COLUMNS].values.astype(np.float32)
    r   = pd.read_excel(old / "reel.xlsx").values.astype(np.float32)
    i   = pd.read_excel(old / "imaginary.xlsx").values.astype(np.float32)
    n   = min(len(x), len(r), len(i))
    return x[:n], np.stack([r[:n], i[:n]], axis=1)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(model: nn.Module, loader: DataLoader, device: torch.device, args: argparse.Namespace) -> float:
    model.eval()
    k_idx = _K_IDX.to(device)
    losses = []
    with torch.no_grad():
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            pred   = model(xb)
            loss   = compute_loss(
                pred, yb,
                beta=args.beta, alfa=args.alfa,
                w_filter=args.w_filter, wmag=args.wmag,
                k_idx=k_idx,
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

    x_raw, y = load_old_excel_data(root)

    scaler   = MinMaxScaler(feature_range=(-1, 1))
    x_scaled = scaler.fit_transform(x_raw).astype(np.float32)

    rng = np.random.default_rng(args.seed)
    all_idx = np.arange(len(x_scaled))
    rng.shuffle(all_idx)
    if args.n_samples is not None:
        all_idx = all_idx[:args.n_samples]
    n = len(all_idx)
    n_val = max(1, int(n * args.val_ratio))
    va_idx = all_idx[:n_val]
    tr_idx = all_idx[n_val:]

    print(f"Using {len(tr_idx)} train + {len(va_idx)} val samples (from {len(x_scaled)} total available)")

    x_train = torch.tensor(x_scaled[tr_idx], dtype=torch.float32)
    y_train = torch.tensor(y[tr_idx],         dtype=torch.float32)
    x_val   = torch.tensor(x_scaled[va_idx],  dtype=torch.float32)
    y_val   = torch.tensor(y[va_idx],          dtype=torch.float32)

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    k_idx  = _K_IDX.to(device)

    train_loader = DataLoader(TensorDataset(x_train, y_train), batch_size=args.batch_size, shuffle=True)
    val_loader   = DataLoader(TensorDataset(x_val,   y_val),   batch_size=args.batch_size, shuffle=False)

    model = AntennaNeuralNet().to(device)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"AntennaNeuralNet | trainable params: {n_params:,}")
    print(f"Device: {device}")
    print(f"Loss: Huber(ri, beta={args.beta}) + FFT(alfa={args.alfa}, w={args.w_filter}) + Mag(alfa={args.alfa}, w={args.wmag})")

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
                beta=args.beta, alfa=args.alfa,
                w_filter=args.w_filter, wmag=args.wmag,
                k_idx=k_idx,
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
            print(f"\nEarly stopping at epoch {epoch}. Best val: {best_val:.6f}")
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
        "model": "AntennaNeuralNet",
        "dataset": "old_excel",
        "trainable_params": n_params,
        "motivation": (
            "AntennaNN baseline: MLP(11→60→60→60, Tanh) + deconv → 2×201. "
            "Trained with AntennaNN Huber loss."
        ),
        "stopped_epoch": stopped_epoch,
        "loss": {
            "type":     "AntennaNN Huber loss",
            "beta":     args.beta,
            "alfa":     args.alfa,
            "w_filter": args.w_filter,
            "wmag":     args.wmag,
            "k_idx":    "concat(arange(0,40), arange(161,201))",
        },
        "n_samples_requested": args.n_samples,
        "n_samples":     int(len(x_scaled)),
        "n_train":       int(len(tr_idx)),
        "n_val":         int(len(va_idx)),
        "best_val_loss": float(best_val),
        "model_path":    str(model_path),
        "scaler_path":   str(scaler_path),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"\nSaved model:  {model_path}")
    print(f"Saved scaler: {scaler_path}")
    print(f"Best val loss: {best_val:.6f}")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train AntennaNN — MLP + deconv + AntennaNN Huber loss (n-samples)")
    parser.add_argument("--project-root",  type=str,   default=".")
    parser.add_argument("--output-dir",    type=str,   default="NNModel")
    parser.add_argument("--model-name",    type=str,   default="trained_model_antenna_nn.pt")
    parser.add_argument("--scaler-name",   type=str,   default="scaler_antenna_nn.gz")
    parser.add_argument("--history-name",  type=str,   default="history_antenna_nn.csv")
    parser.add_argument("--meta-name",     type=str,   default="meta_antenna_nn.json")

    parser.add_argument("--epochs",        type=int,   default=500)
    parser.add_argument("--patience",      type=int,   default=40)
    parser.add_argument("--batch-size",    type=int,   default=32)
    parser.add_argument("--lr",            type=float, default=8e-4)
    parser.add_argument("--weight-decay",  type=float, default=1e-4)
    parser.add_argument("--val-ratio",     type=float, default=0.2)
    parser.add_argument("--seed",          type=int,   default=42)

    # AntennaNN Huber loss parameters (from retrain_neuralnet.ipynb)
    parser.add_argument("--beta",          type=float, default=0.10)   # Huber delta for ri
    parser.add_argument("--alfa",          type=float, default=0.10)   # Huber delta for FFT + mag
    parser.add_argument("--w-filter",      type=float, default=0.05)   # F-FFT weight
    parser.add_argument("--wmag",          type=float, default=0.40)   # magnitude weight

    parser.add_argument("--n-samples",     type=int,   default=None,
                        help="Limit training to N samples (None = use all)")

    parser.add_argument("--log-every",     type=int,   default=10)
    parser.add_argument("--cpu",           action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    torch.manual_seed(42)
    np.random.seed(42)
    args = parse_args()
    train(args)
