"""
train_resunet_big_v10.py  —  BigResUNet v10 (= v1.2 + quartic dB RSE)

v1.2 baseline (2nd best on NewData, RSE-dB mean=0.01213):
  BigResUNet1D, no smooth layer, 5-term loss, w_mag_db=3.0, CosineAnnealingLR.

v10 single change: dB RSE term raised from ^2 → ^4.

  v1.2: db_loss = mean( (db_p - db_t)^2 / (db_t^2 + eps) )
  v10:  db_loss = mean( (db_p - db_t)^4 / (db_t^4 + eps) )

Effect: large errors are penalised disproportionately more; small errors are
almost ignored. Acts as a "soft maximum" over frequency — similar philosophy
to the max-deviation penalty in v8 but differentiable and smoother.

Gradient clipping (max_norm=5.0) is added to guard against the larger
gradients produced by the ^4 term during early training.

Loss terms (5 — same structure as v1.2, only dB RSE changes):
  w_ri        * MSE(real/imag)
  w_mag_db    * dB_RSE_quartic  (weight=3.0)
  w_slope     * MSE(dB slope)
  w_curv      * MSE(dB curvature)
  w_passivity * passivity penalty

Architecture: BigResUNet1D (no smooth layer) — same as v1 / v1.2 / v8.
Hyperparameters: same as v1.2 (lr=8e-4, batch=32, wd=1e-4).
Training data: old_excel only — NewData / LHS are test sets (no leakage).
Early stopping: patience=40.
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
# Building blocks (identical to v1 / v1.2 / v8)
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
# Model — BigResUNet1D, no smooth layer (identical to v1 / v1.2 / v8)
# ---------------------------------------------------------------------------

class BigResUNet1D(nn.Module):
    def __init__(self, input_dim: int = 11, target_len: int = 201, base_ch: int = 128) -> None:
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
        return out


# ---------------------------------------------------------------------------
# Loss  (5 terms — v1.2 structure, dB RSE raised to ^4)
# ---------------------------------------------------------------------------

def compute_loss(
    pred: torch.Tensor,
    target: torch.Tensor,
    w_ri: float,
    w_mag_db: float,
    db_weight_eps: float,
    w_slope: float,
    w_curv: float,
    w_passivity: float,
) -> torch.Tensor:
    mse = nn.MSELoss()

    real_p, imag_p = pred[:, 0, :],   pred[:, 1, :]
    real_t, imag_t = target[:, 0, :], target[:, 1, :]

    mag_p = torch.sqrt(real_p**2 + imag_p**2 + 1e-12)
    mag_t = torch.sqrt(real_t**2 + imag_t**2 + 1e-12)

    db_p = 20.0 * torch.log10(torch.clamp(mag_p, min=1e-8))
    db_t = 20.0 * torch.log10(torch.clamp(mag_t, min=1e-8))

    # dB RSE — quartic: (err^4 / denom^4)  instead of v1.2's (err^2 / denom^2)
    # Large errors penalised disproportionately; gradient clipping handles the
    # larger gradient magnitudes during early training.
    err4   = (db_p - db_t) ** 4
    denom4 = db_t ** 4 + db_weight_eps
    db_loss = torch.mean(err4 / denom4)

    slope_p = db_p[:, 1:] - db_p[:, :-1]
    slope_t = db_t[:, 1:] - db_t[:, :-1]
    curv_p  = slope_p[:, 1:] - slope_p[:, :-1]
    curv_t  = slope_t[:, 1:] - slope_t[:, :-1]

    passivity = torch.mean(torch.relu(mag_p - 1.0) ** 2)

    return (
        w_ri          * mse(pred, target)
        + w_mag_db    * db_loss
        + w_slope     * mse(slope_p, slope_t)
        + w_curv      * mse(curv_p, curv_t)
        + w_passivity * passivity
    )


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
                w_ri=args.w_ri, w_mag_db=args.w_mag_db,
                db_weight_eps=args.db_weight_eps,
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

    x_raw, y = load_old_excel_data(root)

    scaler   = MinMaxScaler(feature_range=(-1, 1))
    x_scaled = scaler.fit_transform(x_raw).astype(np.float32)

    tr_idx, va_idx = split_indices(len(x_scaled), args.val_ratio, args.seed)
    x_train = torch.tensor(x_scaled[tr_idx], dtype=torch.float32)
    y_train = torch.tensor(y[tr_idx],         dtype=torch.float32)
    x_val   = torch.tensor(x_scaled[va_idx],  dtype=torch.float32)
    y_val   = torch.tensor(y[va_idx],          dtype=torch.float32)

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")

    train_loader = DataLoader(TensorDataset(x_train, y_train), batch_size=args.batch_size, shuffle=True)
    val_loader   = DataLoader(TensorDataset(x_val,   y_val),   batch_size=args.batch_size, shuffle=False)

    model = BigResUNet1D(
        input_dim=x_train.shape[1],
        target_len=y_train.shape[-1],
        base_ch=args.base_channels,
    ).to(device)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"BigResUNet1D (v10)  |  base_ch={args.base_channels}  |  trainable params: {n_params:,}")
    print(f"Device: {device}")
    print(f"dB RSE: quartic (^4)  |  w_mag_db={args.w_mag_db}  |  grad_clip={args.grad_clip}")

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
                w_ri=args.w_ri, w_mag_db=args.w_mag_db,
                db_weight_eps=args.db_weight_eps,
                w_slope=args.w_slope, w_curv=args.w_curv,
                w_passivity=args.w_passivity,
            )
            loss.backward()
            if args.grad_clip > 0:
                nn.utils.clip_grad_norm_(model.parameters(), max_norm=args.grad_clip)
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
        "model": "BigResUNet1D",
        "dataset": "old_excel",
        "base_channels": args.base_channels,
        "trainable_params": n_params,
        "motivation": (
            "Big v10: v1.2 (BigResUNet1D, no smooth layer, 5-term loss) "
            "with dB RSE raised from ^2 to ^4. "
            "Large frequency-point errors are penalised disproportionately more "
            "than in v1.2; acts as a soft maximum over frequency errors. "
            "Gradient clipping (max_norm=5.0) stabilises early training."
        ),
        "stopped_epoch": stopped_epoch,
        "loss_weights": {
            "w_ri":         args.w_ri,
            "w_mag_db":     args.w_mag_db,
            "db_rse_power": 4,
            "w_slope":      args.w_slope,
            "w_curv":       args.w_curv,
            "w_passivity":  args.w_passivity,
        },
        "grad_clip":     args.grad_clip,
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
    parser = argparse.ArgumentParser(description="Train BigResUNet v10 — v1.2 + quartic dB RSE")
    parser.add_argument("--project-root",  type=str,   default=".")
    parser.add_argument("--output-dir",    type=str,   default="NNModel")
    parser.add_argument("--model-name",    type=str,   default="trained_model_resunet_v10.pt")
    parser.add_argument("--scaler-name",   type=str,   default="scaler_resunet_v10.gz")
    parser.add_argument("--history-name",  type=str,   default="history_resunet_v10.csv")
    parser.add_argument("--meta-name",     type=str,   default="meta_resunet_v10.json")

    parser.add_argument("--epochs",        type=int,   default=500)
    parser.add_argument("--patience",      type=int,   default=40)
    parser.add_argument("--batch-size",    type=int,   default=32)
    parser.add_argument("--lr",            type=float, default=8e-4)
    parser.add_argument("--weight-decay",  type=float, default=1e-4)
    parser.add_argument("--val-ratio",     type=float, default=0.2)
    parser.add_argument("--seed",          type=int,   default=42)
    parser.add_argument("--base-channels", type=int,   default=128)

    # Loss weights — same defaults as v1.2
    parser.add_argument("--w-ri",          type=float, default=0.20)
    parser.add_argument("--w-mag-db",      type=float, default=3.00)
    parser.add_argument("--db-weight-eps", type=float, default=1e-4)
    parser.add_argument("--w-slope",       type=float, default=0.10)
    parser.add_argument("--w-curv",        type=float, default=0.03)
    parser.add_argument("--w-passivity",   type=float, default=0.05)

    # Gradient clipping — important for ^4 term stability
    parser.add_argument("--grad-clip",     type=float, default=5.0,
                        help="Max gradient norm. Set 0 to disable. Recommended: 1.0-5.0.")

    parser.add_argument("--log-every",     type=int,   default=10)
    parser.add_argument("--cpu",           action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    torch.manual_seed(42)
    args = parse_args()
    # namespace attr uses underscore
    args.project_root = args.project_root
    train(args)
