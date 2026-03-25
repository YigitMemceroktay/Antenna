"""
train_transformer_crossattn.py  —  Cross-Attention Transformer for S11 prediction

Architecture:
  - 11 geometry parameters → parameter embeddings (keys + values)
  - 201 frequency queries with sinusoidal positional encoding
  - Multi-head cross-attention: each frequency bin attends to all 11 parameters
  - Several stacked cross-attention + self-attention decoder layers
  - Output head: 2 channels (real + imaginary)

Explainability:
  The cross-attention weights form a (201 × 11) map per head — showing
  which geometry parameters dominate at which frequency points.
  Saved automatically after training to NNModel/attn_weights_transformer.npz

Data:
  - Train / Val : old_excel  (80 / 20 split, seed=42, no leakage)
  - Test        : NewData/   (18 seeds × 50 samples = 900 HFSS-simulated points)

Loss: same AntennaNN Huber loss as v9
  1. Huber on real/imag          (beta=0.10)
  2. F-FFT Huber on high-freq    (alfa=0.10, w_filter=0.05)
  3. Magnitude Huber             (alfa=0.10, wmag=0.40)

Run:
    python updates/train_transformer_crossattn.py --project-root .
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

# F-FFT filter indices — same as AntennaNN / v9
_K_IDX = torch.cat([torch.arange(0, 40), torch.arange(161, 201)])  # 80 indices


# ---------------------------------------------------------------------------
# Positional encoding
# ---------------------------------------------------------------------------

def sinusoidal_pe(length: int, dim: int, device: torch.device) -> torch.Tensor:
    """Returns (1, length, dim) sinusoidal positional encoding."""
    pos  = torch.arange(length, dtype=torch.float32, device=device).unsqueeze(1)  # (L, 1)
    i    = torch.arange(0, dim, 2, dtype=torch.float32, device=device)            # (dim/2,)
    denom = torch.pow(10000.0, i / dim)
    pe   = torch.zeros(length, dim, device=device)
    pe[:, 0::2] = torch.sin(pos / denom)
    pe[:, 1::2] = torch.cos(pos / denom)
    return pe.unsqueeze(0)  # (1, L, dim)


# ---------------------------------------------------------------------------
# Cross-Attention Transformer Decoder Layer
# ---------------------------------------------------------------------------

class CrossAttnDecoderLayer(nn.Module):
    """
    One decoder layer:
      1. Multi-head cross-attention  (queries=freq bins, keys/values=param embeddings)
      2. Multi-head self-attention   (freq bins attend to each other)
      3. Feed-forward block
    Attention weights from cross-attn are returned for explainability.
    """

    def __init__(self, d_model: int, n_heads: int, ff_dim: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.cross_attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.self_attn  = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)

        self.ff = nn.Sequential(
            nn.Linear(d_model, ff_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, d_model),
        )

        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)
        self.drop  = nn.Dropout(dropout)

    def forward(
        self,
        tgt: torch.Tensor,          # (B, L, d_model)  — frequency queries
        memory: torch.Tensor,       # (B, 11, d_model) — parameter keys/values
    ) -> tuple[torch.Tensor, torch.Tensor]:
        # Cross-attention: freq bins attend to geometry parameters
        attn_out, attn_w = self.cross_attn(tgt, memory, memory, need_weights=True, average_attn_weights=True)
        tgt = self.norm1(tgt + self.drop(attn_out))

        # Self-attention: freq bins attend to each other
        sa_out, _ = self.self_attn(tgt, tgt, tgt)
        tgt = self.norm2(tgt + self.drop(sa_out))

        # Feed-forward
        tgt = self.norm3(tgt + self.drop(self.ff(tgt)))

        return tgt, attn_w   # attn_w: (B, L, 11)


# ---------------------------------------------------------------------------
# Full model
# ---------------------------------------------------------------------------

class CrossAttnTransformer(nn.Module):
    """
    Cross-Attention Transformer for scalar-to-sequence regression.

    Input  : (B, 11)        — scaled geometry parameters
    Output : (B, 2, 201)    — predicted S11 real + imaginary

    Explainability:
      Call forward(..., return_attn=True) to also get a list of attention
      weight tensors, one per decoder layer, each shape (B, 201, 11).
      Average across layers and heads to get the final (201 × 11) importance map.
    """

    def __init__(
        self,
        input_dim:  int   = 11,
        target_len: int   = 201,
        d_model:    int   = 128,
        n_heads:    int   = 8,
        n_layers:   int   = 4,
        ff_dim:     int   = 512,
        dropout:    float = 0.1,
    ) -> None:
        super().__init__()
        self.target_len = target_len
        self.d_model    = d_model

        # Each of the 11 parameters gets its own embedding vector (keys + values)
        self.param_embed = nn.Sequential(
            nn.Linear(1, d_model),
            nn.GELU(),
            nn.Linear(d_model, d_model),
        )

        # Learnable frequency query tokens (one per output point)
        self.freq_queries = nn.Parameter(torch.randn(1, target_len, d_model) * 0.02)

        # Stacked decoder layers
        self.layers = nn.ModuleList([
            CrossAttnDecoderLayer(d_model, n_heads, ff_dim, dropout)
            for _ in range(n_layers)
        ])

        # Output projection: d_model → 2 (real + imaginary)
        self.out_proj = nn.Linear(d_model, 2)

        # Fixed Gaussian smoothing (same sigma as v9 for fair comparison)
        self.register_buffer("_gauss_sigma", torch.tensor(1.527))
        self._smooth_k = 41

    def _smooth(self, x: torch.Tensor) -> torch.Tensor:
        """Apply fixed Gaussian smooth across the frequency dimension."""
        k     = self._smooth_k
        sigma = self._gauss_sigma
        t     = torch.linspace(-(k // 2), k // 2, steps=k, device=x.device, dtype=x.dtype)
        kernel = torch.exp(-0.5 * (t / sigma) ** 2)
        kernel = kernel / kernel.sum()
        kernel_2ch = kernel.view(1, 1, k).expand(2, 1, k)
        x_pad = F.pad(x, (k // 2, k // 2), mode="reflect")
        return F.conv1d(x_pad, kernel_2ch, groups=2)

    def forward(
        self,
        x: torch.Tensor,                  # (B, 11)
        return_attn: bool = False,
    ) -> torch.Tensor | tuple[torch.Tensor, list[torch.Tensor]]:
        B = x.shape[0]

        # Embed each parameter independently: (B, 11) → (B, 11, d_model)
        params = x.unsqueeze(-1)                          # (B, 11, 1)
        memory = self.param_embed(params)                 # (B, 11, d_model)

        # Add sinusoidal PE to frequency query tokens
        pe  = sinusoidal_pe(self.target_len, self.d_model, x.device)  # (1, L, d_model)
        tgt = self.freq_queries.expand(B, -1, -1) + pe                # (B, L, d_model)

        # Pass through decoder layers
        attn_weights = []
        for layer in self.layers:
            tgt, attn_w = layer(tgt, memory)
            attn_weights.append(attn_w)   # each: (B, L, 11)

        # Project to output: (B, L, 2) → (B, 2, L)
        out = self.out_proj(tgt).permute(0, 2, 1)        # (B, 2, 201)

        # Smooth output
        out = self._smooth(out)

        if return_attn:
            return out, attn_weights
        return out


# ---------------------------------------------------------------------------
# Loss — same AntennaNN Huber loss as v9
# ---------------------------------------------------------------------------

def _huber(diff: torch.Tensor, delta: float) -> torch.Tensor:
    return torch.where(diff < delta, 0.5 * diff ** 2 / delta, diff - 0.5 * delta)


def compute_loss(
    pred: torch.Tensor,
    target: torch.Tensor,
    beta: float,
    alfa: float,
    w_filter: float,
    wmag: float,
    k_idx: torch.Tensor,
) -> torch.Tensor:
    # Term 1: Huber on real/imag
    loss_ri = torch.mean(_huber(torch.abs(pred - target), beta))

    # Term 2: F-FFT Huber on high-frequency components
    s_pred   = torch.complex(pred[:, 0, :],   pred[:, 1, :])
    s_true   = torch.complex(target[:, 0, :], target[:, 1, :])
    fft_pred = torch.fft.fft(s_pred, dim=-1)
    fft_true = torch.fft.fft(s_true, dim=-1)
    k        = k_idx.to(pred.device)
    loss_fft = torch.mean(
        _huber(torch.abs(fft_pred.real[:, k] - fft_true.real[:, k]), alfa)
        + _huber(torch.abs(fft_pred.imag[:, k] - fft_true.imag[:, k]), alfa)
    )

    # Term 3: Magnitude Huber
    mag_pred = torch.sqrt(pred[:, 0, :] ** 2   + pred[:, 1, :] ** 2   + 1e-12)
    mag_true = torch.sqrt(target[:, 0, :] ** 2 + target[:, 1, :] ** 2 + 1e-12)
    loss_mag = torch.mean(_huber(torch.abs(mag_pred - mag_true), alfa))

    return loss_ri + loss_fft * w_filter + loss_mag * wmag


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_old_excel_data(root: Path) -> tuple[np.ndarray, np.ndarray]:
    old = root / "old" / "data"
    x   = pd.read_excel(old / "input_parameters.xlsx")[INPUT_COLUMNS].values.astype(np.float32)
    r   = pd.read_excel(old / "reel.xlsx").values.astype(np.float32)
    i   = pd.read_excel(old / "imaginary.xlsx").values.astype(np.float32)
    n   = min(len(x), len(r), len(i))
    return x[:n], np.stack([r[:n], i[:n]], axis=1)


def load_new_data(root: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load all 18 NewData seeds (18 × 50 = 900 samples) as the test set."""
    inp_dir  = root / "NewData" / "inputs"
    real_dir = root / "NewData" / "reals"
    imag_dir = root / "NewData" / "imaginary"

    xs, ys = [], []
    for f in sorted(inp_dir.glob("inputs_LHS_n50_seed*.csv")):
        seed = f.stem.split("seed")[-1]
        x    = pd.read_csv(f)[INPUT_COLUMNS].values.astype(np.float32)
        r    = pd.read_csv(real_dir / f"real_LHS_n50_seed{seed}.csv").values.astype(np.float32)
        i    = pd.read_csv(imag_dir / f"imag_LHS_n50_seed{seed}.csv").values.astype(np.float32)
        n    = min(len(x), len(r), len(i))
        xs.append(x[:n])
        ys.append(np.stack([r[:n], i[:n]], axis=1))

    if not xs:
        raise RuntimeError("No NewData files found — check NewData/inputs/ folder.")

    return np.concatenate(xs, axis=0), np.concatenate(ys, axis=0)


def split_indices(n: int, val_ratio: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng   = np.random.default_rng(seed)
    idx   = np.arange(n)
    rng.shuffle(idx)
    n_val = max(1, int(n * val_ratio))
    return idx[n_val:], idx[:n_val]


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def evaluate(model: nn.Module, loader: DataLoader, device: torch.device, args: argparse.Namespace) -> float:
    model.eval()
    k_idx  = _K_IDX.to(device)
    losses = []
    with torch.no_grad():
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            pred   = model(xb)
            losses.append(compute_loss(pred, yb, args.beta, args.alfa, args.w_filter, args.wmag, k_idx).item())
    return float(np.mean(losses)) if losses else float("nan")


def evaluate_metrics(model: nn.Module, loader: DataLoader, device: torch.device) -> dict:
    """Compute MSE and RSE on magnitude (dB) for final reporting."""
    model.eval()
    mse_list, rse_list = [], []
    with torch.no_grad():
        for xb, yb in loader:
            xb, yb   = xb.to(device), yb.to(device)
            pred     = model(xb)
            mag_p    = torch.sqrt(pred[:, 0, :] ** 2   + pred[:, 1, :] ** 2   + 1e-12)
            mag_t    = torch.sqrt(yb[:, 0, :] ** 2     + yb[:, 1, :] ** 2     + 1e-12)
            db_p     = 20.0 * torch.log10(mag_p.clamp(min=1e-12))
            db_t     = 20.0 * torch.log10(mag_t.clamp(min=1e-12))
            mse_list.append(torch.mean((db_p - db_t) ** 2).item())
            rse_list.append(torch.mean(((db_p - db_t) ** 2) / (db_t ** 2 + 1e-6)).item())
    return {
        "mse_db": float(np.mean(mse_list)),
        "rse_db": float(np.mean(rse_list)),
    }


def save_attention_weights(model: nn.Module, loader: DataLoader, device: torch.device, out_path: Path) -> None:
    """
    Run one pass over the loader and save the mean cross-attention weights.
    Output: (n_layers, 201, 11) averaged over all samples.
    """
    model.eval()
    layer_accum = None
    n_batches   = 0
    with torch.no_grad():
        for xb, _ in loader:
            xb = xb.to(device)
            _, attn_list = model(xb, return_attn=True)
            # attn_list: list of (B, 201, 11) tensors, one per layer
            batch_stack = torch.stack([a.mean(dim=0) for a in attn_list], dim=0)  # (n_layers, 201, 11)
            if layer_accum is None:
                layer_accum = batch_stack
            else:
                layer_accum = layer_accum + batch_stack
            n_batches += 1
    if layer_accum is not None:
        avg = (layer_accum / n_batches).cpu().numpy()
        np.savez(out_path, attn=avg, param_names=np.array(INPUT_COLUMNS))
        print(f"Saved attention weights: {out_path}  shape={avg.shape}")


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train(args: argparse.Namespace) -> None:
    root    = Path(args.project_root).resolve()
    out_dir = (root / args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Load data ---
    print("Loading old_excel data (train/val)...")
    x_raw, y = load_old_excel_data(root)

    scaler   = MinMaxScaler(feature_range=(-1, 1))
    x_scaled = scaler.fit_transform(x_raw).astype(np.float32)

    tr_idx, va_idx = split_indices(len(x_scaled), args.val_ratio, args.seed)
    x_train = torch.tensor(x_scaled[tr_idx], dtype=torch.float32)
    y_train = torch.tensor(y[tr_idx],         dtype=torch.float32)
    x_val   = torch.tensor(x_scaled[va_idx],  dtype=torch.float32)
    y_val   = torch.tensor(y[va_idx],          dtype=torch.float32)

    print("Loading NewData (test)...")
    x_test_raw, y_test = load_new_data(root)
    x_test  = torch.tensor(scaler.transform(x_test_raw).astype(np.float32), dtype=torch.float32)
    y_test  = torch.tensor(y_test, dtype=torch.float32)

    print(f"  train={len(x_train)}  val={len(x_val)}  test={len(x_test)}")

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    k_idx  = _K_IDX.to(device)

    train_loader = DataLoader(TensorDataset(x_train, y_train), batch_size=args.batch_size, shuffle=True,  drop_last=True)
    val_loader   = DataLoader(TensorDataset(x_val,   y_val),   batch_size=args.batch_size, shuffle=False)
    test_loader  = DataLoader(TensorDataset(x_test,  y_test),  batch_size=args.batch_size, shuffle=False)

    # --- Model ---
    model = CrossAttnTransformer(
        input_dim=len(INPUT_COLUMNS),
        target_len=y_train.shape[-1],
        d_model=args.d_model,
        n_heads=args.n_heads,
        n_layers=args.n_layers,
        ff_dim=args.ff_dim,
        dropout=args.dropout,
    ).to(device)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\nCrossAttnTransformer  |  d_model={args.d_model}  n_heads={args.n_heads}  "
          f"n_layers={args.n_layers}  ff_dim={args.ff_dim}  params={n_params:,}")
    print(f"Device: {device}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_val      = float("inf")
    best_state    = None
    history       = []
    patience_ctr  = 0
    stopped_epoch = args.epochs

    print("\nTraining...")
    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            pred = model(xb)
            loss = compute_loss(pred, yb, args.beta, args.alfa, args.w_filter, args.wmag, k_idx)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
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

    # --- Restore best and evaluate test ---
    if best_state is not None:
        model.load_state_dict(best_state)

    test_metrics = evaluate_metrics(model, test_loader, device)
    val_metrics  = evaluate_metrics(model, val_loader,  device)
    print(f"\nVal  MSE(dB)={val_metrics['mse_db']:.6f}  RSE(dB)={val_metrics['rse_db']:.6f}")
    print(f"Test MSE(dB)={test_metrics['mse_db']:.6f}  RSE(dB)={test_metrics['rse_db']:.6f}")

    # --- Save ---
    model_path   = out_dir / args.model_name
    scaler_path  = out_dir / args.scaler_name
    history_path = out_dir / args.history_name
    meta_path    = out_dir / args.meta_name
    attn_path    = out_dir / args.attn_name

    torch.save(model.state_dict(), model_path)
    joblib.dump(scaler, scaler_path)
    pd.DataFrame(history).to_csv(history_path, index=False)

    meta = {
        "model":          "CrossAttnTransformer",
        "train_dataset":  "old_excel",
        "test_dataset":   "NewData (18 seeds × 50 = 900 samples)",
        "n_train":        int(len(tr_idx)),
        "n_val":          int(len(va_idx)),
        "n_test":         int(len(x_test)),
        "d_model":        args.d_model,
        "n_heads":        args.n_heads,
        "n_layers":       args.n_layers,
        "ff_dim":         args.ff_dim,
        "dropout":        args.dropout,
        "trainable_params": n_params,
        "stopped_epoch":  stopped_epoch,
        "best_val_loss":  float(best_val),
        "val_mse_db":     val_metrics["mse_db"],
        "val_rse_db":     val_metrics["rse_db"],
        "test_mse_db":    test_metrics["mse_db"],
        "test_rse_db":    test_metrics["rse_db"],
        "loss": {
            "type":     "AntennaNN Huber (3 terms)",
            "beta":     args.beta,
            "alfa":     args.alfa,
            "w_filter": args.w_filter,
            "wmag":     args.wmag,
        },
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # Save attention weights for explainability
    save_attention_weights(model, test_loader, device, attn_path)

    print(f"\nSaved model  : {model_path}")
    print(f"Saved scaler : {scaler_path}")
    print(f"Saved attn   : {attn_path}")
    print(f"Best val loss: {best_val:.6f}")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cross-Attention Transformer for S11 prediction")
    parser.add_argument("--project-root",  type=str,   default=".")
    parser.add_argument("--output-dir",    type=str,   default="NNModel")
    parser.add_argument("--model-name",    type=str,   default="trained_model_transformer_crossattn.pt")
    parser.add_argument("--scaler-name",   type=str,   default="scaler_transformer_crossattn.gz")
    parser.add_argument("--history-name",  type=str,   default="history_transformer_crossattn.csv")
    parser.add_argument("--meta-name",     type=str,   default="meta_transformer_crossattn.json")
    parser.add_argument("--attn-name",     type=str,   default="attn_weights_transformer.npz")

    # Architecture
    parser.add_argument("--d-model",       type=int,   default=128)
    parser.add_argument("--n-heads",       type=int,   default=8)
    parser.add_argument("--n-layers",      type=int,   default=4)
    parser.add_argument("--ff-dim",        type=int,   default=512)
    parser.add_argument("--dropout",       type=float, default=0.1)

    # Training
    parser.add_argument("--epochs",        type=int,   default=500)
    parser.add_argument("--patience",      type=int,   default=40)
    parser.add_argument("--batch-size",    type=int,   default=32)
    parser.add_argument("--lr",            type=float, default=3e-4)
    parser.add_argument("--weight-decay",  type=float, default=1e-4)
    parser.add_argument("--val-ratio",     type=float, default=0.2)
    parser.add_argument("--seed",          type=int,   default=42)

    # Loss (same as v9)
    parser.add_argument("--beta",          type=float, default=0.10)
    parser.add_argument("--alfa",          type=float, default=0.10)
    parser.add_argument("--w-filter",      type=float, default=0.05)
    parser.add_argument("--wmag",          type=float, default=0.40)

    parser.add_argument("--log-every",     type=int,   default=10)
    parser.add_argument("--cpu",           action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    torch.manual_seed(42)
    np.random.seed(42)
    args = parse_args()
    train(args)
