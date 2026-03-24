"""
hpo_resunet.py  —  Optuna hyperparameter optimisation for SmoothResUNet1D (Big family)

What is tuned
─────────────
  Optimiser / scheduler
    lr              1e-4 … 2e-3  (log scale)
    weight_decay    1e-6 … 1e-2  (log scale)
    lr_patience     5  … 25      (ReduceLROnPlateau patience)
    lr_factor       0.3 … 0.7    (ReduceLROnPlateau factor)

  Architecture
    base_ch         64, 96, 128

  Training
    batch_size      16, 32, 64

  Loss weights  (all ≥ 0; w_mag is the dominant term and fixed to 1.0 for identifiability)
    w_ri            0.0 … 0.5
    w_slope         0.0 … 0.3
    w_curv          0.0 … 0.1
    w_passivity     0.0 … 0.2

Objective  →  best val_loss (magnitude-RSE composite) after `--epochs` epochs per trial.

Pruning    →  MedianPruner (warm up 10 trials, prune after 5 intermediate reports).

Run:
    pip install optuna
    python3 -u updates/hpo_resunet.py --n-trials 50 --epochs 150 --project-root .

Results saved to:
    hpo_results/study_results.csv   — all trials
    hpo_results/best_params.json    — best trial hyperparameters
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import optuna
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset

THIS_DIR = Path(__file__).resolve().parent
import sys
if str(THIS_DIR) not in sys.path:
    sys.path.append(str(THIS_DIR))

from train_resunet_big_v5 import (
    SmoothResUNet1D,
    compute_loss,
    load_old_excel_data,
    split_indices,
    INPUT_COLUMNS,
)


# ---------------------------------------------------------------------------
# Device
# ---------------------------------------------------------------------------

def get_device(cpu: bool) -> torch.device:
    if cpu:
        return torch.device("cpu")
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


# ---------------------------------------------------------------------------
# Single-trial training
# ---------------------------------------------------------------------------

def run_trial(
    trial: optuna.Trial,
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_val: torch.Tensor,
    y_val: torch.Tensor,
    device: torch.device,
    args: argparse.Namespace,
) -> float:
    # ---- Suggest hyperparameters ----
    lr           = trial.suggest_float("lr",           1e-4, 2e-3,  log=True)
    weight_decay = trial.suggest_float("weight_decay", 1e-6, 1e-2,  log=True)
    lr_patience  = trial.suggest_int  ("lr_patience",  5,    25)
    lr_factor    = trial.suggest_float("lr_factor",    0.3,  0.7)
    base_ch      = trial.suggest_categorical("base_ch", [64, 96, 128])
    batch_size   = trial.suggest_categorical("batch_size", [16, 32, 64])
    w_ri         = trial.suggest_float("w_ri",         0.0,  0.5)
    w_slope      = trial.suggest_float("w_slope",      0.0,  0.3)
    w_curv       = trial.suggest_float("w_curv",       0.0,  0.1)
    w_passivity  = trial.suggest_float("w_passivity",  0.0,  0.2)

    train_loader = DataLoader(
        TensorDataset(x_train, y_train),
        batch_size=int(batch_size), shuffle=True,
    )
    val_loader = DataLoader(
        TensorDataset(x_val, y_val),
        batch_size=int(batch_size), shuffle=False,
    )

    model = SmoothResUNet1D(
        input_dim=x_train.shape[1],
        target_len=y_train.shape[-1],
        base_ch=int(base_ch),
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=lr_factor, patience=lr_patience, min_lr=1e-7
    )

    best_val     = float("inf")
    patience_ctr = 0

    for epoch in range(1, args.epochs + 1):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = compute_loss(
                model(xb), yb,
                w_ri=w_ri, w_mag=1.0, mag_eps=1e-4,
                w_slope=w_slope, w_curv=w_curv, w_passivity=w_passivity,
            )
            loss.backward()
            optimizer.step()

        # Val loss
        model.eval()
        val_losses = []
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                val_losses.append(compute_loss(
                    model(xb), yb,
                    w_ri=w_ri, w_mag=1.0, mag_eps=1e-4,
                    w_slope=w_slope, w_curv=w_curv, w_passivity=w_passivity,
                ).item())
        val_loss = float(np.mean(val_losses))
        scheduler.step(val_loss)

        # Optuna pruning (report every 5 epochs after warmup)
        if epoch % 5 == 0:
            trial.report(val_loss, epoch)
            if trial.should_prune():
                raise optuna.exceptions.TrialPruned()

        # Track best
        if val_loss < best_val:
            best_val     = val_loss
            patience_ctr = 0
        else:
            patience_ctr += 1

        # Early stopping inside trial (shorter patience to save time)
        if patience_ctr >= args.early_stop:
            break

    return best_val


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(args: argparse.Namespace) -> None:
    root     = Path(args.project_root).resolve()
    out_dir  = root / "hpo_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    device   = get_device(args.cpu)

    print(f"Device: {device}")
    print(f"Epochs per trial: {args.epochs}  |  Trials: {args.n_trials}")

    # ---- Load data once ----
    x_raw, y = load_old_excel_data(root)
    scaler   = MinMaxScaler(feature_range=(-1, 1))
    x_scaled = scaler.fit_transform(x_raw).astype(np.float32)

    tr_idx, va_idx = split_indices(len(x_scaled), val_ratio=0.2, seed=42)
    x_train = torch.tensor(x_scaled[tr_idx], dtype=torch.float32)
    y_train = torch.tensor(y[tr_idx],         dtype=torch.float32)
    x_val   = torch.tensor(x_scaled[va_idx],  dtype=torch.float32)
    y_val   = torch.tensor(y[va_idx],          dtype=torch.float32)
    print(f"Train: {len(x_train)}  Val: {len(x_val)}")

    # ---- Optuna study ----
    pruner = optuna.pruners.MedianPruner(n_warmup_steps=10, n_startup_trials=10)
    study  = optuna.create_study(
        direction="minimize",
        pruner=pruner,
        study_name="big_resunet_hpo",
    )

    def objective(trial: optuna.Trial) -> float:
        return run_trial(trial, x_train, y_train, x_val, y_val, device, args)

    study.optimize(objective, n_trials=args.n_trials, show_progress_bar=True)

    # ---- Save results ----
    results_df = study.trials_dataframe()
    results_path = out_dir / "study_results.csv"
    results_df.to_csv(results_path, index=False)
    print(f"\nAll trial results → {results_path}")

    best = study.best_trial
    best_params = {
        "best_val_loss": best.value,
        "n_trials":      args.n_trials,
        "epochs_per_trial": args.epochs,
        **best.params,
    }
    best_path = out_dir / "best_params.json"
    best_path.write_text(json.dumps(best_params, indent=2))
    print(f"Best params      → {best_path}")

    print(f"\n{'='*50}")
    print(f"Best val loss: {best.value:.6f}")
    print("Best hyperparameters:")
    for k, v in best.params.items():
        print(f"  {k:20s} = {v}")

    # ---- Importance plot (text summary) ----
    try:
        importances = optuna.importance.get_param_importances(study)
        print("\nParameter importances (higher = more impact on val loss):")
        for param, imp in importances.items():
            bar = "█" * int(imp * 40)
            print(f"  {param:20s} {imp:.3f}  {bar}")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Optuna HPO for SmoothResUNet1D (Big v5 architecture)")
    p.add_argument("--project-root",  type=str, default=".")
    p.add_argument("--n-trials",      type=int, default=50,
                   help="Number of Optuna trials (default: 50)")
    p.add_argument("--epochs",        type=int, default=150,
                   help="Epochs per trial — shorter than full training (default: 150)")
    p.add_argument("--early-stop",    type=int, default=30,
                   help="Early stopping patience inside each trial (default: 30)")
    p.add_argument("--cpu",           action="store_true",
                   help="Force CPU (useful for debugging)")
    return p.parse_args()


if __name__ == "__main__":
    torch.manual_seed(0)
    np.random.seed(0)
    args = parse_args()
    main(args)
