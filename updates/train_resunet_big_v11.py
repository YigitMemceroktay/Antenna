"""
train_resunet_big_v11.py  —  BigResUNet v11 (v9 loss + dB-derivative Huber)

What v11 keeps from v9:
  1) Huber(real/imag)
  2) Filtered FFT Huber (high-frequency bins)
  3) Magnitude Huber

What v11 adds:
  4) dB first-derivative (slope) Huber
  5) dB second-derivative (curvature) Huber
    6) dB top-k hardest-frequency absolute-error term

Total loss:
    L = L_ri + w_filter*L_fft + wmag*L_mag + w_db_d1*L_db_d1 + w_db_d2*L_db_d2 + w_topk*L_topk

Backbone/data flow is reused from v9:
  - SmoothResUNet1D (fixed Gaussian smoothing output layer)
  - old_excel-only training split
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
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset

from train_resunet_big_v9 import (
    _K_IDX,
    SmoothResUNet1D,
    load_old_excel_data,
    split_indices,
)


def _huber(diff_abs: torch.Tensor, delta: float) -> torch.Tensor:
    return torch.where(
        diff_abs < delta,
        0.5 * diff_abs**2 / delta,
        diff_abs - 0.5 * delta,
    )


def compute_loss(
    pred: torch.Tensor,
    target: torch.Tensor,
    beta: float,
    alfa: float,
    w_filter: float,
    wmag: float,
    w_db_d1: float,
    w_db_d2: float,
    w_topk: float,
    topk_freq: int,
    db_eps: float,
    k_idx: torch.Tensor,
) -> torch.Tensor:
    # ----- v9 terms ----------------------------------------------------------
    diff_ri = torch.abs(pred - target)
    loss_ri = torch.mean(_huber(diff_ri, beta))

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

    mag_pred = torch.sqrt(real_p**2 + imag_p**2 + 1e-12)
    mag_true = torch.sqrt(real_t**2 + imag_t**2 + 1e-12)
    diff_mag = torch.abs(mag_pred - mag_true)
    loss_mag = torch.mean(_huber(diff_mag, alfa))


    # ----- new v11 terms (magnitude derivatives) ---------------------------
    # Slope and curvature in magnitude (not dB)
    d1_pred = mag_pred[:, 1:] - mag_pred[:, :-1]
    d1_true = mag_true[:, 1:] - mag_true[:, :-1]
    loss_db_d1 = torch.mean(_huber(torch.abs(d1_pred - d1_true), alfa))

    d2_pred = d1_pred[:, 1:] - d1_pred[:, :-1]
    d2_true = d1_true[:, 1:] - d1_true[:, :-1]
    loss_db_d2 = torch.mean(_huber(torch.abs(d2_pred - d2_true), alfa))

    # Top-k term now in magnitude
    abs_mag_err = torch.abs(mag_pred - mag_true)
    k_top = max(1, min(topk_freq, abs_mag_err.shape[-1]))
    topk_vals = torch.topk(abs_mag_err, k=k_top, dim=-1, largest=True, sorted=False).values
    loss_topk = torch.mean(topk_vals)

    total = (
        loss_ri
        + w_filter * loss_fft
        + wmag * loss_mag
        + w_db_d1 * loss_db_d1
        + w_db_d2 * loss_db_d2
        + w_topk * loss_topk
    )
    return total


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device, args: argparse.Namespace) -> float:
    model.eval()
    k_idx = _K_IDX.to(device)
    losses = []
    with torch.no_grad():
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            pred = model(xb)
            loss = compute_loss(
                pred,
                yb,
                beta=args.beta,
                alfa=args.alfa,
                w_filter=args.w_filter,
                wmag=args.wmag,
                w_db_d1=args.w_db_d1,
                w_db_d2=args.w_db_d2,
                w_topk=args.w_topk,
                topk_freq=args.topk_freq,
                db_eps=args.db_eps,
                k_idx=k_idx,
            )
            losses.append(loss.item())
    return float(np.mean(losses)) if losses else float("nan")


def train(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    out_dir = (root / args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    x_raw, y = load_old_excel_data(root)

    scaler = MinMaxScaler(feature_range=(-1, 1))
    x_scaled = scaler.fit_transform(x_raw).astype(np.float32)

    tr_idx, va_idx = split_indices(len(x_scaled), args.val_ratio, args.seed)
    x_train = torch.tensor(x_scaled[tr_idx], dtype=torch.float32)
    y_train = torch.tensor(y[tr_idx], dtype=torch.float32)
    x_val = torch.tensor(x_scaled[va_idx], dtype=torch.float32)
    y_val = torch.tensor(y[va_idx], dtype=torch.float32)

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    k_idx = _K_IDX.to(device)

    train_loader = DataLoader(TensorDataset(x_train, y_train), batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(x_val, y_val), batch_size=args.batch_size, shuffle=False)

    model = SmoothResUNet1D(
        input_dim=x_train.shape[1],
        target_len=y_train.shape[-1],
        base_ch=args.base_channels,
        smooth_filter=args.smooth_filter,
    ).to(device)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    sigma_fixed = float(np.exp(model.smooth.logsigma.item()))
    print(
        f"SmoothResUNet1D (v11) | base_ch={args.base_channels} | "
        f"trainable params: {n_params:,} | sigma={sigma_fixed:.3f}"
    )
    print(f"Device: {device}")
    print(
        "Loss: Huber(ri) + w_filter*FFT-Huber + wmag*Mag-Huber + "
        "w_db_d1*dB-slope-Huber + w_db_d2*dB-curvature-Huber + w_topk*topk(dB abs err)"
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_val = float("inf")
    best_state = None
    history = []
    patience_ctr = 0
    stopped_epoch = args.epochs

    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            pred = model(xb)
            loss = compute_loss(
                pred,
                yb,
                beta=args.beta,
                alfa=args.alfa,
                w_filter=args.w_filter,
                wmag=args.wmag,
                w_db_d1=args.w_db_d1,
                w_db_d2=args.w_db_d2,
                w_topk=args.w_topk,
                topk_freq=args.topk_freq,
                db_eps=args.db_eps,
                k_idx=k_idx,
            )
            loss.backward()
            optimizer.step()
            losses.append(loss.item())

        scheduler.step()
        train_loss = float(np.mean(losses))
        val_loss = evaluate(model, val_loader, device, args)
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})

        if val_loss < best_val:
            best_val = val_loss
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}
            patience_ctr = 0
        else:
            patience_ctr += 1

        if epoch % args.log_every == 0 or epoch == 1:
            print(
                f"epoch={epoch:4d}  train={train_loss:.6f}  "
                f"val={val_loss:.6f}  patience={patience_ctr}/{args.patience}"
            )

        if patience_ctr >= args.patience:
            print(f"\nEarly stopping at epoch {epoch}. Best val: {best_val:.6f}")
            stopped_epoch = epoch
            break

    if stopped_epoch == args.epochs:
        print(f"epoch={stopped_epoch:4d}  train={train_loss:.6f}  val={val_loss:.6f}")

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
        "model": "SmoothResUNet1D",
        "dataset": "old_excel",
        "base_channels": args.base_channels,
        "trainable_params": n_params,
        "motivation": (
            "Big v11 extends v9 loss by adding dB slope and curvature Huber terms "
            "and a dB top-k hardest-frequency error term while preserving "
            "RI Huber + filtered FFT Huber + magnitude Huber."
        ),
        "stopped_epoch": stopped_epoch,
        "loss": {
            "type": "v9 Huber + dB derivatives + dB top-k",
            "beta": args.beta,
            "alfa": args.alfa,
            "w_filter": args.w_filter,
            "wmag": args.wmag,
            "w_db_d1": args.w_db_d1,
            "w_db_d2": args.w_db_d2,
            "w_topk": args.w_topk,
            "topk_freq": args.topk_freq,
            "db_eps": args.db_eps,
            "k_idx": "concat(arange(0,40), arange(161,201))",
        },
        "smooth_filter_size": args.smooth_filter,
        "fixed_sigma": sigma_fixed,
        "n_samples": int(len(x_scaled)),
        "n_train": int(len(tr_idx)),
        "n_val": int(len(va_idx)),
        "best_val_loss": float(best_val),
        "model_path": str(model_path),
        "scaler_path": str(scaler_path),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"\nSaved model:  {model_path}")
    print(f"Saved scaler: {scaler_path}")
    print(f"Best val loss: {best_val:.6f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train BigResUNet v11 — v9 Huber loss + dB derivative Huber"
    )
    parser.add_argument("--project-root", type=str, default=".")
    parser.add_argument("--output-dir", type=str, default="NNModel")
    parser.add_argument("--model-name", type=str, default="trained_model_resunet_v11.pt")
    parser.add_argument("--scaler-name", type=str, default="scaler_resunet_v11.gz")
    parser.add_argument("--history-name", type=str, default="history_resunet_v11.csv")
    parser.add_argument("--meta-name", type=str, default="meta_resunet_v11.json")

    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--patience", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=8e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--base-channels", type=int, default=128)
    parser.add_argument("--smooth-filter", type=int, default=41)

    parser.add_argument("--beta", type=float, default=0.10, help="Huber delta for RI term")
    parser.add_argument("--alfa", type=float, default=0.10, help="Huber delta for FFT/Mag/dB-derivative terms")
    parser.add_argument("--w-filter", type=float, default=0.05, help="Weight for FFT Huber term")
    parser.add_argument("--wmag", type=float, default=0.40, help="Weight for magnitude Huber term")
    parser.add_argument("--w-db-d1", type=float, default=0.50, help="Weight for dB slope Huber term")
    parser.add_argument("--w-db-d2", type=float, default=0.25, help="Weight for dB curvature Huber term")
    parser.add_argument("--w-topk", type=float, default=1.00, help="Weight for dB top-k hardest-frequency term")
    parser.add_argument("--topk-freq", type=int, default=15, help="Top-k frequency count for dB absolute-error term")
    parser.add_argument("--db-eps", type=float, default=1e-8, help="Clamp epsilon before log10")

    parser.add_argument("--log-every", type=int, default=10)
    parser.add_argument("--cpu", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    train(args)
