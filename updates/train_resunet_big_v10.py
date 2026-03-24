"""
train_resunet_big_v10.py  —  BigResUNet v10 (v9 backbone + dip-aware composite loss)

Base architecture:
  SmoothResUNet1D from v9 (BigResUNet1D + fixed Gaussian smooth output, sigma=1.527).

Professor-suggested composite loss:
  L = lambda_ri * L_RI
    + lambda_db * L_dB
    + lambda_d1 * L_delta
    + lambda_d2 * L_delta2
    + lambda_topk * L_topk
    + lambda_pass * L_pass

Where:
  - L_RI    : Huber(real_pred, real_true) + Huber(imag_pred, imag_true)
  - L_dB    : Huber(y_db_pred, y_db_true)
  - L_delta : Huber(first-derivative in dB)
  - L_delta2: Huber(second-derivative in dB)
  - L_topk  : mean of top-k |y_db_pred - y_db_true| per sample
  - L_pass  : mean(relu(|S11_pred| - 1)^2)

Data policy:
  old_excel only for training/validation (no leakage from NewData / LHS).
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


class ResBlock1D(nn.Module):
    def __init__(self, in_ch: int, out_ch: int) -> None:
        super().__init__()
        self.conv1 = nn.Conv1d(in_ch, out_ch, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(out_ch)
        self.conv2 = nn.Conv1d(out_ch, out_ch, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(out_ch)
        self.skip = nn.Conv1d(in_ch, out_ch, kernel_size=1) if in_ch != out_ch else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        s = self.skip(x)
        x = F.gelu(self.bn1(self.conv1(x)))
        x = self.bn2(self.conv2(x))
        return F.gelu(x + s)


class FixedGaussianSmooth1D(nn.Module):
    def __init__(self, filter_size: int = 41, sigma: float = 1.527) -> None:
        super().__init__()
        self.filter_size = filter_size
        self.register_buffer("logsigma", torch.tensor(float(np.log(sigma))))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        n = self.filter_size
        sigma = torch.exp(self.logsigma)
        hw = 3.0 * sigma
        t = torch.linspace(0.0, 1.0, steps=n, device=x.device)
        t = 2.0 * hw * t - hw
        kernel = torch.exp(-0.5 * (t / sigma) ** 2)
        kernel = kernel / kernel.sum()

        kernel_2ch = kernel.view(1, 1, n).expand(2, 1, n)
        pad = (n - 1) // 2
        x_pad = F.pad(x, (pad, pad), mode="reflect")
        return F.conv1d(x_pad, kernel_2ch, groups=2)


class SmoothResUNet1D(nn.Module):
    def __init__(
        self,
        input_dim: int = 11,
        target_len: int = 201,
        base_ch: int = 128,
        smooth_filter: int = 41,
    ) -> None:
        super().__init__()
        self.target_len = target_len
        self.pos_channels = 16

        self.cond_mlp = nn.Sequential(
            nn.Linear(input_dim, base_ch * 2),
            nn.GELU(),
            nn.Linear(base_ch * 2, base_ch),
            nn.GELU(),
        )

        enc_in = base_ch + self.pos_channels

        self.enc1 = ResBlock1D(enc_in, base_ch)
        self.enc2 = ResBlock1D(base_ch, base_ch * 2)
        self.bottleneck = ResBlock1D(base_ch * 2, base_ch * 4)

        self.up2 = nn.ConvTranspose1d(base_ch * 4, base_ch * 2, kernel_size=2, stride=2)
        self.dec2 = ResBlock1D(base_ch * 4, base_ch * 2)

        self.up1 = nn.ConvTranspose1d(base_ch * 2, base_ch, kernel_size=2, stride=2)
        self.dec1 = ResBlock1D(base_ch * 2, base_ch)

        self.out_head = nn.Conv1d(base_ch, 2, kernel_size=1)
        self.smooth = FixedGaussianSmooth1D(filter_size=smooth_filter)

    def _positional_encoding(self, length: int, device: torch.device) -> torch.Tensor:
        pos = torch.linspace(0, 1, steps=length, device=device)[None, None, :]
        feats = []
        for k in range(1, self.pos_channels // 2 + 1):
            feats.append(torch.sin(2 * np.pi * k * pos))
            feats.append(torch.cos(2 * np.pi * k * pos))
        return torch.cat(feats, dim=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b = x.shape[0]
        cond = self.cond_mlp(x).unsqueeze(-1).expand(-1, -1, self.target_len)
        pe = self._positional_encoding(self.target_len, x.device).expand(b, -1, -1)
        f0 = torch.cat([cond, pe], dim=1)

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


def _huber_abs(diff_abs: torch.Tensor, delta: float) -> torch.Tensor:
    delta_t = torch.tensor(delta, dtype=diff_abs.dtype, device=diff_abs.device)
    return torch.where(
        diff_abs <= delta_t,
        0.5 * (diff_abs**2) / delta_t,
        diff_abs - 0.5 * delta_t,
    )


def _mean_huber(a: torch.Tensor, b: torch.Tensor, delta: float) -> torch.Tensor:
    return torch.mean(_huber_abs(torch.abs(a - b), delta))


def compute_loss(
    pred: torch.Tensor,
    target: torch.Tensor,
    delta_ri: float,
    delta_db: float,
    lambda_ri: float,
    lambda_db: float,
    lambda_d1: float,
    lambda_d2: float,
    lambda_topk: float,
    lambda_pass: float,
    topk_freq: int,
    db_eps: float,
    mag_eps: float,
) -> torch.Tensor:
    real_p, imag_p = pred[:, 0, :], pred[:, 1, :]
    real_t, imag_t = target[:, 0, :], target[:, 1, :]

    mag_p = torch.sqrt(real_p**2 + imag_p**2 + mag_eps)
    mag_t = torch.sqrt(real_t**2 + imag_t**2 + mag_eps)

    y_db_p = 20.0 * torch.log10(torch.clamp(mag_p, min=db_eps))
    y_db_t = 20.0 * torch.log10(torch.clamp(mag_t, min=db_eps))

    l_ri = _mean_huber(real_p, real_t, delta_ri) + _mean_huber(imag_p, imag_t, delta_ri)
    l_db = _mean_huber(y_db_p, y_db_t, delta_db)

    d1_p = y_db_p[:, 1:] - y_db_p[:, :-1]
    d1_t = y_db_t[:, 1:] - y_db_t[:, :-1]
    l_d1 = _mean_huber(d1_p, d1_t, delta_db)

    d2_p = d1_p[:, 1:] - d1_p[:, :-1]
    d2_t = d1_t[:, 1:] - d1_t[:, :-1]
    l_d2 = _mean_huber(d2_p, d2_t, delta_db)

    abs_db_err = torch.abs(y_db_p - y_db_t)
    k = max(1, min(topk_freq, abs_db_err.shape[-1]))
    topk_vals = torch.topk(abs_db_err, k=k, dim=-1, largest=True, sorted=False).values
    l_topk = torch.mean(topk_vals)

    l_pass = torch.mean(torch.relu(mag_p - 1.0) ** 2)

    total = (
        lambda_ri * l_ri
        + lambda_db * l_db
        + lambda_d1 * l_d1
        + lambda_d2 * l_d2
        + lambda_topk * l_topk
        + lambda_pass * l_pass
    )
    return total


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


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device, args: argparse.Namespace) -> float:
    model.eval()
    losses = []
    with torch.no_grad():
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            pred = model(xb)
            loss = compute_loss(
                pred,
                yb,
                delta_ri=args.delta_ri,
                delta_db=args.delta_db,
                lambda_ri=args.lambda_ri,
                lambda_db=args.lambda_db,
                lambda_d1=args.lambda_d1,
                lambda_d2=args.lambda_d2,
                lambda_topk=args.lambda_topk,
                lambda_pass=args.lambda_pass,
                topk_freq=args.topk_freq,
                db_eps=args.db_eps,
                mag_eps=args.mag_eps,
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

    train_loader = DataLoader(TensorDataset(x_train, y_train), batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(x_val, y_val), batch_size=args.batch_size, shuffle=False)

    model = SmoothResUNet1D(
        input_dim=x_train.shape[1],
        target_len=y_train.shape[-1],
        base_ch=args.base_channels,
        smooth_filter=args.smooth_filter,
    ).to(device)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"SmoothResUNet1D (Big v10) | base_ch={args.base_channels} | params: {n_params:,}")
    print(f"Device: {device}")
    print(
        "Loss weights: "
        f"ri={args.lambda_ri}, db={args.lambda_db}, d1={args.lambda_d1}, "
        f"d2={args.lambda_d2}, topk={args.lambda_topk}, pass={args.lambda_pass} | "
        f"topk_freq={args.topk_freq}"
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
        train_losses = []

        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            pred = model(xb)
            loss = compute_loss(
                pred,
                yb,
                delta_ri=args.delta_ri,
                delta_db=args.delta_db,
                lambda_ri=args.lambda_ri,
                lambda_db=args.lambda_db,
                lambda_d1=args.lambda_d1,
                lambda_d2=args.lambda_d2,
                lambda_topk=args.lambda_topk,
                lambda_pass=args.lambda_pass,
                topk_freq=args.topk_freq,
                db_eps=args.db_eps,
                mag_eps=args.mag_eps,
            )
            loss.backward()
            if args.grad_clip > 0:
                nn.utils.clip_grad_norm_(model.parameters(), max_norm=args.grad_clip)
            optimizer.step()
            train_losses.append(loss.item())

        scheduler.step()

        train_loss = float(np.mean(train_losses))
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
        "version": "big_v10",
        "dataset": "old_excel",
        "base_channels": args.base_channels,
        "smooth_filter": args.smooth_filter,
        "trainable_params": n_params,
        "description": "v9 architecture with composite dip-aware Huber loss (RI+dB+derivatives+topk+passivity).",
        "stopped_epoch": stopped_epoch,
        "loss": {
            "formula": "lambda_ri*L_RI + lambda_db*L_dB + lambda_d1*L_delta + lambda_d2*L_delta2 + lambda_topk*L_topk + lambda_pass*L_pass",
            "delta_ri": args.delta_ri,
            "delta_db": args.delta_db,
            "lambda_ri": args.lambda_ri,
            "lambda_db": args.lambda_db,
            "lambda_d1": args.lambda_d1,
            "lambda_d2": args.lambda_d2,
            "lambda_topk": args.lambda_topk,
            "lambda_pass": args.lambda_pass,
            "topk_freq": args.topk_freq,
            "db_eps": args.db_eps,
            "mag_eps": args.mag_eps,
        },
        "grad_clip": args.grad_clip,
        "n_samples": int(len(x_scaled)),
        "n_train": int(len(tr_idx)),
        "n_val": int(len(va_idx)),
        "best_val_loss": float(best_val),
        "model_path": str(model_path),
        "scaler_path": str(scaler_path),
        "history_path": str(history_path),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"\nSaved model:  {model_path}")
    print(f"Saved scaler: {scaler_path}")
    print(f"Best val loss: {best_val:.6f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train BigResUNet v10 (v9 backbone + RI/dB/derivative/top-k/passivity composite loss)"
    )
    parser.add_argument("--project-root", type=str, default=".")
    parser.add_argument("--output-dir", type=str, default="NNModel")
    parser.add_argument("--model-name", type=str, default="trained_model_resunet_v10.pt")
    parser.add_argument("--scaler-name", type=str, default="scaler_resunet_v10.gz")
    parser.add_argument("--history-name", type=str, default="history_resunet_v10.csv")
    parser.add_argument("--meta-name", type=str, default="meta_resunet_v10.json")

    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--patience", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=8e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--base-channels", type=int, default=128)
    parser.add_argument("--smooth-filter", type=int, default=41)

    parser.add_argument("--delta-ri", type=float, default=0.10)
    parser.add_argument("--delta-db", type=float, default=0.20)

    parser.add_argument("--lambda-ri", type=float, default=1.00)
    parser.add_argument("--lambda-db", type=float, default=1.00)
    parser.add_argument("--lambda-d1", type=float, default=0.25)
    parser.add_argument("--lambda-d2", type=float, default=0.10)
    parser.add_argument("--lambda-topk", type=float, default=1.00)
    parser.add_argument("--lambda-pass", type=float, default=0.05)

    parser.add_argument("--topk-freq", type=int, default=20)
    parser.add_argument("--db-eps", type=float, default=1e-8)
    parser.add_argument("--mag-eps", type=float, default=1e-12)

    parser.add_argument("--grad-clip", type=float, default=5.0)
    parser.add_argument("--log-every", type=int, default=10)
    parser.add_argument("--cpu", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    train(args)
