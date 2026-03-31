"""
train_resunet_v9_nsamples.py  —  BigResUNet v9 (SmoothResUNet1D + AntennaNN Huber loss)
                                 with --n-samples argument support

AntennaNN's loss function (from retrain_neuralnet.ipynb, huber_w_f_fft_mag.pth) has 3 terms:

  1. Huber loss on real/imag prediction  (beta=0.1)
  2. F-FFT Huber regularization          (alfa=0.1, w_filter=0.05)
       — Huber loss on high-frequency FFT components only
       — k = [0:40] ∪ [161:201]  (removes low-frequency component focus)
  3. Magnitude Huber regularization      (alfa=0.1, wmag=0.4)

This file applies that exact loss to our SmoothResUNet1D architecture
(BigResUNet1D + fixed Gaussian smooth output layer, σ=1.527).

PyTorch differentiable implementation: uses torch.fft.fft instead of numpy.

Training data: old_excel only — NewData / LHS are test sets (no leakage).
Hyperparameters: similar to v1 (lr=8e-4, batch=32). Early stopping patience=40.
--n-samples: limit training to N samples (None = use all).
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

# F-FFT filter indices: keep only high-frequency components [0:40] and [161:201]
# (same as AntennaNN: k = np.concatenate((np.arange(0,40), np.arange(161,201))))
_K_IDX = torch.cat([torch.arange(0, 40), torch.arange(161, 201)])  # 80 indices


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

class ResBlock1D(nn.Module):
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


# ---------------------------------------------------------------------------
# Model — SmoothResUNet1D (BigResUNet1D + fixed Gaussian smooth, σ=1.527)
# ---------------------------------------------------------------------------

class LearnableGaussianSmooth1D(nn.Module):
    """Fixed-sigma Gaussian smoothing (sigma=1.527, non-trainable)."""

    def __init__(self, filter_size: int = 41, sigma: float = 1.527) -> None:
        super().__init__()
        self.filter_size = filter_size
        self.register_buffer("logsigma", torch.tensor(float(np.log(sigma))))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        n      = self.filter_size
        sigma  = torch.exp(self.logsigma)
        hw     = 3.0 * sigma
        t      = torch.linspace(0.0, 1.0, steps=n, device=x.device)
        t      = 2.0 * hw * t - hw
        kernel = torch.exp(-0.5 * (t / sigma) ** 2)
        kernel = kernel / kernel.sum()
        kernel_2ch = kernel.view(1, 1, n).expand(2, 1, n)
        pad        = (n - 1) // 2
        x_pad      = F.pad(x, (pad, pad), mode="reflect")
        return F.conv1d(x_pad, kernel_2ch, groups=2)


class SmoothResUNet1D(nn.Module):
    """BigResUNet1D (base_ch=128) + fixed Gaussian smooth output layer (σ=1.527)."""

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

        enc_in = base_ch + self.pos_channels

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
    beta: float,     # Huber delta for ri loss
    alfa: float,     # Huber delta for FFT and magnitude losses
    w_filter: float, # weight for F-FFT term
    wmag: float,     # weight for magnitude term
    k_idx: torch.Tensor,  # F-FFT filter indices (80 values)
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

    s_pred = torch.complex(real_p, imag_p)          # (B, L)
    s_true = torch.complex(real_t, imag_t)
    fft_pred = torch.fft.fft(s_pred, dim=-1)        # (B, L) complex
    fft_true = torch.fft.fft(s_true, dim=-1)

    k = k_idx.to(pred.device)
    diff_fft_re = torch.abs(fft_pred.real[:, k] - fft_true.real[:, k])  # (B, 80)
    diff_fft_im = torch.abs(fft_pred.imag[:, k] - fft_true.imag[:, k])

    loss_fft = torch.mean(_huber(diff_fft_re, alfa) + _huber(diff_fft_im, alfa))

    # ---- Term 3: Magnitude Huber --------------------------------------------
    mag_pred = torch.sqrt(real_p ** 2 + imag_p ** 2 + 1e-12)
    mag_true = torch.sqrt(real_t ** 2 + imag_t ** 2 + 1e-12)
    diff_mag = torch.abs(mag_pred - mag_true)       # (B, L)
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

    model = SmoothResUNet1D(
        input_dim=x_train.shape[1],
        target_len=y_train.shape[-1],
        base_ch=args.base_channels,
        smooth_filter=args.smooth_filter,
    ).to(device)

    n_params    = sum(p.numel() for p in model.parameters() if p.requires_grad)
    sigma_fixed = float(np.exp(model.smooth.logsigma.item()))
    print(f"SmoothResUNet1D (v9)  |  base_ch={args.base_channels}  |  trainable params: {n_params:,}  |  sigma={sigma_fixed:.3f}")
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
        "model": "SmoothResUNet1D",
        "dataset": "old_excel",
        "base_channels": args.base_channels,
        "trainable_params": n_params,
        "motivation": (
            "Big v9: SmoothResUNet1D (BigResUNet1D + Gaussian smooth, σ=1.527) "
            "trained with AntennaNN's Huber loss (3 terms: Huber-ri + F-FFT Huber + Mag Huber). "
            "Tests whether AntennaNN's outlier-robust loss works better inside our larger architecture."
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
        "smooth_filter_size": args.smooth_filter,
        "fixed_sigma":        sigma_fixed,
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
    parser = argparse.ArgumentParser(description="Train BigResUNet v9 — SmoothResUNet + AntennaNN Huber loss (n-samples)")
    parser.add_argument("--project-root",  type=str,   default=".")
    parser.add_argument("--output-dir",    type=str,   default="NNModel")
    parser.add_argument("--model-name",    type=str,   default="trained_model_resunet_v9.pt")
    parser.add_argument("--scaler-name",   type=str,   default="scaler_resunet_v9.gz")
    parser.add_argument("--history-name",  type=str,   default="history_resunet_v9.csv")
    parser.add_argument("--meta-name",     type=str,   default="meta_resunet_v9.json")

    parser.add_argument("--epochs",        type=int,   default=500)
    parser.add_argument("--patience",      type=int,   default=40)
    parser.add_argument("--batch-size",    type=int,   default=32)
    parser.add_argument("--lr",            type=float, default=8e-4)
    parser.add_argument("--weight-decay",  type=float, default=1e-4)
    parser.add_argument("--val-ratio",     type=float, default=0.2)
    parser.add_argument("--seed",          type=int,   default=42)
    parser.add_argument("--base-channels", type=int,   default=128)
    parser.add_argument("--smooth-filter", type=int,   default=41)

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
