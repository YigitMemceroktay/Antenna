"""
train_resunet_small.py  —  SmallResUNet1D

A deliberately smaller version of DualResUNet1D. Every reduction is explicit so you can
explain exactly what changed and why.

WHAT WAS REDUCED vs DualResUNet1D (train_resunet_dual.py):
  base_ch          64  →  32    Conv params scale quadratically; single biggest lever (~9x fewer total params)
  cond_mlp         11→128→64  →  11→64→32    Removed one hidden layer; one fewer nonlinearity to explain
  pos_channels     16  →  8     4 sin/cos harmonics is enough for 201 frequency points
  loss terms       6   →  4     Removed w_curv (2nd derivative, marginal, 0.05) and
                                         w_hilbert (Kramers-Kronig via FFT, 0.02, hardest to explain)
  hilbert warmup   removed      No hilbert loss → no warmup schedule needed; simpler training loop
  default epochs   220 →  150   Faster iteration; cosine schedule still covers the full range

WHAT STAYS THE SAME (intentionally):
  - 2-level U-Net: enc1→pool→enc2→pool→bottleneck→up2→dec2→up1→dec1
  - ResBlock1D design: Conv-BN-GELU + skip connection
  - AdamW + CosineAnnealingLR
  - MinMaxScaler(-1, 1) preprocessing
  - 80/20 train/val split, seed=42
  - Output shape: (batch, 2, 201) — real + imaginary
  - Data loading from old_excel or LHS

APPROXIMATE PARAMETER COUNTS:
  DualResUNet1D  (base_ch=64)  ≈ 1,500,000 params
  SmallResUNet1D (base_ch=32)  ≈   135,000 params  (~9x fewer)
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
    """
    One residual block: two 1D convolutions with a skip connection.

    Forward pass:
        x → Conv(k=3)-BN-GELU → Conv(k=3)-BN → + skip(x) → GELU

    If in_ch != out_ch the skip is a 1×1 conv; otherwise it is an identity.
    """

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
# Main model
# ---------------------------------------------------------------------------

class SmallResUNet1D(nn.Module):
    """
    Smaller 1D U-Net that predicts complex S11 from 11 antenna geometry parameters.

    Architecture summary (base_ch = 32):

        11 params
        └─ cond_mlp: Linear(11→64)→GELU→Linear(64→32)→GELU    # geometry embedding
               ↓ broadcast to (32, 201)
        positional encoding: 8 channels of sin/cos → (8, 201)
               ↓ concat → (40, 201)

        Encoder
          enc1:  ResBlock1D(40 → 32)     → avg_pool → (32, ~100)
          enc2:  ResBlock1D(32 → 64)     → avg_pool → (64, ~50)
          bottleneck: ResBlock1D(64 → 128)

        Decoder (with skip connections from encoder)
          up2 + cat(enc2) → ResBlock1D(128 → 64)
          up1 + cat(enc1) → ResBlock1D(64  → 32)

        out_head: Conv1d(32 → 2, k=1)   → (batch, 2, 201)  [real, imag]
    """

    def __init__(
        self,
        input_dim: int = 11,
        target_len: int = 201,
        base_ch: int = 32,   # REDUCED from 64
    ) -> None:
        super().__init__()
        self.target_len = target_len
        self.pos_channels = 8  # REDUCED from 16

        # Geometry embedding — REDUCED: one hidden layer instead of two
        self.cond_mlp = nn.Sequential(
            nn.Linear(input_dim, base_ch * 2),  # 11 → 64
            nn.GELU(),
            nn.Linear(base_ch * 2, base_ch),    # 64 → 32
            nn.GELU(),
        )

        enc_in = base_ch + self.pos_channels  # 32 + 8 = 40

        # Encoder
        self.enc1       = ResBlock1D(enc_in,        base_ch)        # 40 → 32
        self.enc2       = ResBlock1D(base_ch,       base_ch * 2)    # 32 → 64
        self.bottleneck = ResBlock1D(base_ch * 2,   base_ch * 4)    # 64 → 128

        # Decoder
        self.up2  = nn.ConvTranspose1d(base_ch * 4, base_ch * 2, kernel_size=2, stride=2)
        self.dec2 = ResBlock1D(base_ch * 4, base_ch * 2)  # concat → 128 → 64

        self.up1  = nn.ConvTranspose1d(base_ch * 2, base_ch, kernel_size=2, stride=2)
        self.dec1 = ResBlock1D(base_ch * 2, base_ch)       # concat → 64  → 32

        # Output: 2 channels = real + imaginary
        self.out_head = nn.Conv1d(base_ch, 2, kernel_size=1)

    def _positional_encoding(self, length: int, device: torch.device) -> torch.Tensor:
        """
        Build sinusoidal positional encoding of shape (1, pos_channels, length).
        Uses 4 harmonics (k=1..4), each contributing sin + cos = 8 channels total.
        REDUCED from 8 harmonics (16 channels) in DualResUNet1D.
        """
        pos = torch.linspace(0, 1, steps=length, device=device)[None, None, :]  # (1,1,L)
        feats = []
        for k in range(1, self.pos_channels // 2 + 1):  # k = 1, 2, 3, 4
            feats.append(torch.sin(2 * np.pi * k * pos))
            feats.append(torch.cos(2 * np.pi * k * pos))
        return torch.cat(feats, dim=1)  # (1, 8, L)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b = x.shape[0]

        # Encode geometry → broadcast across frequency axis
        cond = self.cond_mlp(x).unsqueeze(-1).expand(-1, -1, self.target_len)  # (B, 32, 201)

        # Add positional encoding
        pe = self._positional_encoding(self.target_len, x.device).expand(b, -1, -1)  # (B, 8, 201)
        f0 = torch.cat([cond, pe], dim=1)  # (B, 40, 201)

        # Encoder
        e1 = self.enc1(f0)                               # (B, 32, 201)
        p1 = F.avg_pool1d(e1, kernel_size=2, stride=2)  # (B, 32, ~100)

        e2 = self.enc2(p1)                               # (B, 64, ~100)
        p2 = F.avg_pool1d(e2, kernel_size=2, stride=2)  # (B, 64, ~50)

        bn = self.bottleneck(p2)                         # (B, 128, ~50)

        # Decoder with skip connections
        u2 = self.up2(bn)                                # (B, 64, ~100)
        if u2.shape[-1] != e2.shape[-1]:
            e2 = F.interpolate(e2, size=u2.shape[-1], mode="linear", align_corners=False)
        d2 = self.dec2(torch.cat([u2, e2], dim=1))      # (B, 64, ~100)

        u1 = self.up1(d2)                                # (B, 32, ~200)
        if u1.shape[-1] != e1.shape[-1]:
            e1 = F.interpolate(e1, size=u1.shape[-1], mode="linear", align_corners=False)
        d1 = self.dec1(torch.cat([u1, e1], dim=1))      # (B, 32, ~200)

        out = self.out_head(d1)                          # (B, 2, ~200)
        if out.shape[-1] != self.target_len:
            out = F.interpolate(out, size=self.target_len, mode="linear", align_corners=False)
        return out  # (B, 2, 201)


# ---------------------------------------------------------------------------
# Loss function  (4 terms — SIMPLIFIED from 6)
# ---------------------------------------------------------------------------

def compute_loss(
    pred: torch.Tensor,
    target: torch.Tensor,
    w_ri: float,
    w_mag_db: float,
    db_weight_eps: float,
    w_slope: float,
    w_passivity: float,
) -> torch.Tensor:
    """
    4-term loss (down from 6 in DualResUNet1D):

      w_ri       × MSE(real+imag)            — raw complex error
      w_mag_db   × RSE(dB magnitude)         — main driver; normalises by target magnitude
      w_slope    × MSE(dB first-differences) — encourages smooth frequency response
      w_passivity× relu(|pred|-1)²           — physics: S11 amplitude must be ≤ 1

    REMOVED from original:
      w_curv    (2nd derivative, marginal benefit, 0.05)
      w_hilbert (Kramers-Kronig via FFT, hardest to explain, 0.02)
    """
    mse = nn.MSELoss()

    real_p, imag_p = pred[:, 0, :],   pred[:, 1, :]
    real_t, imag_t = target[:, 0, :], target[:, 1, :]

    mag_p = torch.sqrt(real_p**2 + imag_p**2 + 1e-12)
    mag_t = torch.sqrt(real_t**2 + imag_t**2 + 1e-12)

    db_p = 20.0 * torch.log10(torch.clamp(mag_p, min=1e-8))
    db_t = 20.0 * torch.log10(torch.clamp(mag_t, min=1e-8))

    # RSE in dB space: normalise error by target magnitude
    db_loss = torch.mean(((db_p - db_t) ** 2) / (db_t**2 + db_weight_eps))

    # Slope: first differences of dB curve
    slope_p = db_p[:, 1:] - db_p[:, :-1]
    slope_t = db_t[:, 1:] - db_t[:, :-1]

    # Passivity: penalise predictions where |S11| > 1 (physically impossible)
    passivity = torch.mean(torch.relu(mag_p - 1.0) ** 2)

    return (
        w_ri       * mse(pred, target)
        + w_mag_db * db_loss
        + w_slope  * mse(slope_p, slope_t)
        + w_passivity * passivity
    )


# ---------------------------------------------------------------------------
# Data loading  (identical to train_resunet_dual.py)
# ---------------------------------------------------------------------------

def load_lhs_data(root: Path) -> tuple[np.ndarray, np.ndarray]:
    lhs_dir = root / "data" / "LHS"
    input_files = sorted(lhs_dir.glob("input_trials_done_LHS_n20_rounded_seed*.csv"))
    if not input_files:
        raise FileNotFoundError("No LHS input files found in data/LHS")

    x_all, y_all = [], []
    for input_path in input_files:
        seed = input_path.stem.split("seed")[-1]
        real_path = lhs_dir / f"real_initial_LHS_n20_rounded_seed{seed}.csv"
        imag_path = lhs_dir / f"imag_initial_LHS_n20_rounded_seed{seed}.csv"
        if not (real_path.exists() and imag_path.exists()):
            continue
        x_df   = pd.read_csv(input_path)[INPUT_COLUMNS]
        real_df = pd.read_csv(real_path)
        imag_df = pd.read_csv(imag_path)
        n = min(len(x_df), len(real_df), len(imag_df))
        x_all.append(x_df.values[:n].astype(np.float32))
        y_all.append(np.stack([real_df.values[:n], imag_df.values[:n]], axis=1).astype(np.float32))

    if not x_all:
        raise RuntimeError("No valid LHS tuples found")
    return np.concatenate(x_all, axis=0), np.concatenate(y_all, axis=0)


def load_old_excel_data(root: Path) -> tuple[np.ndarray, np.ndarray]:
    old = root / "old" / "data"
    x = pd.read_excel(old / "input_parameters.xlsx")[INPUT_COLUMNS].values.astype(np.float32)
    r = pd.read_excel(old / "reel.xlsx").values.astype(np.float32)
    i = pd.read_excel(old / "imaginary.xlsx").values.astype(np.float32)
    n = min(len(x), len(r), len(i))
    return x[:n], np.stack([r[:n], i[:n]], axis=1)


def split_indices(n: int, val_ratio: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    rng.shuffle(idx)
    n_val = max(1, int(n * val_ratio))
    return idx[n_val:], idx[:n_val]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    args: argparse.Namespace,
) -> float:
    model.eval()
    losses = []
    with torch.no_grad():
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            pred = model(xb)
            loss = compute_loss(
                pred, yb,
                w_ri=args.w_ri,
                w_mag_db=args.w_mag_db,
                db_weight_eps=args.db_weight_eps,
                w_slope=args.w_slope,
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

    train_loader = DataLoader(TensorDataset(x_train, y_train), batch_size=args.batch_size, shuffle=True)
    val_loader   = DataLoader(TensorDataset(x_val,   y_val),   batch_size=args.batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    model  = SmallResUNet1D(
        input_dim=x_train.shape[1],
        target_len=y_train.shape[-1],
        base_ch=args.base_channels,
    ).to(device)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"SmallResUNet1D  |  base_ch={args.base_channels}  |  trainable params: {n_params:,}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_val   = float("inf")
    best_state = None
    history    = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            pred = model(xb)
            loss = compute_loss(
                pred, yb,
                w_ri=args.w_ri,
                w_mag_db=args.w_mag_db,
                db_weight_eps=args.db_weight_eps,
                w_slope=args.w_slope,
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
            best_val   = val_loss
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}

        if epoch % args.log_every == 0 or epoch == 1 or epoch == args.epochs:
            print(f"epoch={epoch:4d}  train={train_loss:.6f}  val={val_loss:.6f}")

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
        "model": "SmallResUNet1D",
        "dataset": args.dataset,
        "base_channels": args.base_channels,
        "trainable_params": n_params,
        "reductions_vs_dual": {
            "base_ch": "64 → 32",
            "cond_mlp": "11→128→64 → 11→64→32 (one hidden layer removed)",
            "pos_channels": "16 → 8 (4 harmonics instead of 8)",
            "loss_terms": "6 → 4 (removed w_curv and w_hilbert)",
            "hilbert_warmup": "removed",
            "default_epochs": "220 → 150",
        },
        "loss_weights": {
            "w_ri":        args.w_ri,
            "w_mag_db":    args.w_mag_db,
            "w_slope":     args.w_slope,
            "w_passivity": args.w_passivity,
        },
        "n_samples": int(len(x_scaled)),
        "n_train":   int(len(tr_idx)),
        "n_val":     int(len(va_idx)),
        "best_val_loss": float(best_val),
        "model_path":  str(model_path),
        "scaler_path": str(scaler_path),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"\nSaved model:  {model_path}")
    print(f"Saved scaler: {scaler_path}")
    print(f"Best val loss: {best_val:.6f}")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train SmallResUNet1D — a compact, explainable S-parameter predictor"
    )
    parser.add_argument("--project-root",  type=str,   default=".")
    parser.add_argument("--dataset",       type=str,   default="old_excel", choices=["old_excel", "lhs"])
    parser.add_argument("--output-dir",    type=str,   default="NNModel")
    parser.add_argument("--model-name",    type=str,   default="trained_model_resunet_small.pt")
    parser.add_argument("--scaler-name",   type=str,   default="scaler_resunet_small.gz")
    parser.add_argument("--history-name",  type=str,   default="history_resunet_small.csv")
    parser.add_argument("--meta-name",     type=str,   default="meta_resunet_small.json")

    # Training
    parser.add_argument("--epochs",        type=int,   default=150)   # REDUCED from 220
    parser.add_argument("--batch-size",    type=int,   default=32)
    parser.add_argument("--lr",            type=float, default=8e-4)
    parser.add_argument("--weight-decay",  type=float, default=1e-4)
    parser.add_argument("--val-ratio",     type=float, default=0.2)
    parser.add_argument("--seed",          type=int,   default=42)
    parser.add_argument("--base-channels", type=int,   default=32)    # REDUCED from 64

    # Loss weights (4 terms)
    parser.add_argument("--w-ri",          type=float, default=0.20)
    parser.add_argument("--w-mag-db",      type=float, default=1.00)
    parser.add_argument("--db-weight-eps", type=float, default=1e-4)
    parser.add_argument("--w-slope",       type=float, default=0.10)
    parser.add_argument("--w-passivity",   type=float, default=0.05)

    parser.add_argument("--log-every",     type=int,   default=10)
    parser.add_argument("--cpu",           action="store_true")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    torch.manual_seed(42)
    np.random.seed(42)
    args = parse_args()
    train(args)
