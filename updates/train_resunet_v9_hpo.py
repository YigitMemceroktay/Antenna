"""
train_resunet_v9_hpo.py  —  Big v9 + Optuna Hyperparameter Tuning

Uses the same architecture as Big v9 (SmoothResUNet1D) and the same
AntennaNN Huber loss (3 terms: Huber-ri + F-FFT Huber + Mag Huber).

HPO Phase  (Optuna, TPE sampler):
  Tunes: lr, weight_decay, batch_size, beta, alfa, w_filter, wmag
  Each trial: 80 epochs  |  n_trials: 40
  Pruner: MedianPruner (kills bad trials early)

Final Phase:
  Trains best config for 300 epochs with CosineAnnealingLR
  Saves: trained_model_resunet_v9_hpo.pt / scaler_resunet_v9_hpo.gz / ...

Run:
    python updates/train_resunet_v9_hpo.py
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import optuna
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset

warnings.filterwarnings("ignore")

THIS_DIR = Path(__file__).resolve().parent
PROJECT  = THIS_DIR.parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from train_resunet_big_v2 import SmoothResUNet1D, INPUT_COLUMNS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TARGET_LEN   = 201
_K_IDX       = torch.tensor(
    np.concatenate([np.arange(0, 40), np.arange(161, 201)]), dtype=torch.long
)

HPO_EPOCHS    = 80
HPO_TRIALS    = 40
FINAL_EPOCHS  = 300
VAL_RATIO     = 0.2
SEED          = 42

MODEL_NAME   = "trained_model_resunet_v9_hpo.pt"
SCALER_NAME  = "scaler_resunet_v9_hpo.gz"
HISTORY_NAME = "history_resunet_v9_hpo.csv"
META_NAME    = "meta_resunet_v9_hpo.json"

# ---------------------------------------------------------------------------
# Loss  (identical to v9 — AntennaNN Huber, 3 terms)
# ---------------------------------------------------------------------------

def _huber(diff: torch.Tensor, delta: float) -> torch.Tensor:
    return torch.where(diff < delta, 0.5 * diff**2 / delta, diff - 0.5 * delta)


def compute_loss(pred, target, beta, alfa, w_filter, wmag):
    k = _K_IDX.to(pred.device)

    diff_ri = torch.abs(pred - target)
    loss_ri = torch.mean(_huber(diff_ri, beta))

    real_p, imag_p = pred[:, 0, :],   pred[:, 1, :]
    real_t, imag_t = target[:, 0, :], target[:, 1, :]
    fft_pred = torch.fft.fft(torch.complex(real_p, imag_p), dim=-1)
    fft_true = torch.fft.fft(torch.complex(real_t, imag_t), dim=-1)
    diff_re  = torch.abs(fft_pred.real[:, k] - fft_true.real[:, k])
    diff_im  = torch.abs(fft_pred.imag[:, k] - fft_true.imag[:, k])
    loss_fft = torch.mean(_huber(diff_re, alfa) + _huber(diff_im, alfa))

    mag_p    = torch.sqrt(real_p**2 + imag_p**2 + 1e-12)
    mag_t    = torch.sqrt(real_t**2 + imag_t**2 + 1e-12)
    loss_mag = torch.mean(_huber(torch.abs(mag_p - mag_t), alfa))

    return loss_ri + loss_fft * w_filter + loss_mag * wmag


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def load_data(root: Path):
    old = root / "old" / "data"
    x   = pd.read_excel(old / "input_parameters.xlsx")[INPUT_COLUMNS].values.astype(np.float32)
    r   = pd.read_excel(old / "reel.xlsx").values.astype(np.float32)
    i   = pd.read_excel(old / "imaginary.xlsx").values.astype(np.float32)
    n   = min(len(x), len(r), len(i))
    return x[:n], np.stack([r[:n], i[:n]], axis=1).astype(np.float32)


def get_device():
    if torch.cuda.is_available():  return torch.device("cuda")
    if torch.backends.mps.is_available(): return torch.device("mps")
    return torch.device("cpu")


# ---------------------------------------------------------------------------
# One full train loop (used by both HPO trials and final training)
# ---------------------------------------------------------------------------

def run_training(
    x_train, y_train, x_val, y_val,
    lr, weight_decay, batch_size,
    beta, alfa, w_filter, wmag,
    base_ch, epochs,
    device,
    trial=None,           # optuna trial for pruning
    log_every=10,
):
    train_loader = DataLoader(
        TensorDataset(x_train, y_train),
        batch_size=batch_size, shuffle=True, drop_last=False,
    )
    val_loader = DataLoader(
        TensorDataset(x_val, y_val),
        batch_size=batch_size, shuffle=False,
    )

    model = SmoothResUNet1D(
        input_dim=x_train.shape[1], target_len=TARGET_LEN, base_ch=base_ch
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val   = float("inf")
    best_state = None
    history    = []

    for epoch in range(1, epochs + 1):
        model.train()
        t_losses = []
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = compute_loss(model(xb), yb, beta, alfa, w_filter, wmag)
            loss.backward()
            optimizer.step()
            t_losses.append(loss.item())
        scheduler.step()

        model.eval()
        v_losses = []
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                v_losses.append(compute_loss(model(xb), yb, beta, alfa, w_filter, wmag).item())

        t_loss = float(np.mean(t_losses))
        v_loss = float(np.mean(v_losses))
        history.append({"epoch": epoch, "train_loss": t_loss, "val_loss": v_loss})

        if v_loss < best_val:
            best_val   = v_loss
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}

        if log_every and (epoch % log_every == 0 or epoch == 1 or epoch == epochs):
            print(f"  epoch {epoch:4d}  train={t_loss:.6f}  val={v_loss:.6f}")

        # Optuna pruning
        if trial is not None:
            trial.report(v_loss, epoch)
            if trial.should_prune():
                raise optuna.exceptions.TrialPruned()

    if best_state:
        model.load_state_dict(best_state)
    return model, best_val, pd.DataFrame(history)


# ---------------------------------------------------------------------------
# Optuna objective
# ---------------------------------------------------------------------------

def make_objective(x_train, y_train, x_val, y_val, device):
    def objective(trial: optuna.Trial) -> float:
        lr           = trial.suggest_float("lr",           1e-4,  1e-3,  log=True)
        weight_decay = trial.suggest_float("weight_decay", 1e-6,  5e-4,  log=True)
        batch_size   = trial.suggest_categorical("batch_size", [16, 32, 64])
        beta         = trial.suggest_float("beta",         0.03,  0.30)
        alfa         = trial.suggest_float("alfa",         0.03,  0.30)
        w_filter     = trial.suggest_float("w_filter",     0.01,  0.20)
        wmag         = trial.suggest_float("wmag",         0.10,  1.00)

        _, best_val, _ = run_training(
            x_train, y_train, x_val, y_val,
            lr=lr, weight_decay=weight_decay, batch_size=batch_size,
            beta=beta, alfa=alfa, w_filter=w_filter, wmag=wmag,
            base_ch=128, epochs=HPO_EPOCHS,
            device=device, trial=trial, log_every=0,
        )
        return best_val

    return objective


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    root    = PROJECT
    out_dir = root / "NNModel"
    out_dir.mkdir(parents=True, exist_ok=True)

    device = get_device()
    print(f"Device: {device}")

    # ── Load & split data ───────────────────────────────────────────────────
    print("Loading data...")
    x_raw, y = load_data(root)
    print(f"  Samples: {len(x_raw)}")

    scaler   = MinMaxScaler(feature_range=(-1, 1))
    x_scaled = scaler.fit_transform(x_raw).astype(np.float32)

    rng    = np.random.default_rng(SEED)
    idx    = np.arange(len(x_scaled))
    rng.shuffle(idx)
    n_val  = max(1, int(len(idx) * VAL_RATIO))
    tr_idx, va_idx = idx[n_val:], idx[:n_val]

    x_train = torch.tensor(x_scaled[tr_idx], dtype=torch.float32)
    y_train = torch.tensor(y[tr_idx],         dtype=torch.float32)
    x_val   = torch.tensor(x_scaled[va_idx],  dtype=torch.float32)
    y_val   = torch.tensor(y[va_idx],          dtype=torch.float32)

    print(f"  Train: {len(x_train)}  Val: {len(x_val)}")

    # ── HPO ─────────────────────────────────────────────────────────────────
    print(f"\n=== HPO Phase: {HPO_TRIALS} trials x {HPO_EPOCHS} epochs ===")
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    study = optuna.create_study(
        direction="minimize",
        sampler=TPESampler(seed=SEED),
        pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=20),
    )
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    study.optimize(
        make_objective(x_train, y_train, x_val, y_val, device),
        n_trials=HPO_TRIALS,
        show_progress_bar=True,
    )

    best = study.best_trial
    print(f"\nBest trial #{best.number}  val_loss={best.value:.6f}")
    print("Best params:")
    for k, v in best.params.items():
        print(f"  {k}: {v}")

    # Save HPO study results
    study_df = study.trials_dataframe()
    study_df.to_csv(out_dir / "hpo_results_v9_hpo.csv", index=False)

    bp = best.params
    best_params_dict = {
        "best_val_loss": best.value,
        "n_trials": HPO_TRIALS,
        "epochs_per_trial": HPO_EPOCHS,
        **bp,
    }
    (out_dir / "hpo_best_params_v9_hpo.json").write_text(
        json.dumps(best_params_dict, indent=2), encoding="utf-8"
    )

    # ── Final training ───────────────────────────────────────────────────────
    print(f"\n=== Final Training: {FINAL_EPOCHS} epochs with best params ===")
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    final_model, best_val, history_df = run_training(
        x_train, y_train, x_val, y_val,
        lr=bp["lr"],
        weight_decay=bp["weight_decay"],
        batch_size=bp["batch_size"],
        beta=bp["beta"],
        alfa=bp["alfa"],
        w_filter=bp["w_filter"],
        wmag=bp["wmag"],
        base_ch=128,
        epochs=FINAL_EPOCHS,
        device=device,
        trial=None,
        log_every=10,
    )

    n_params = sum(p.numel() for p in final_model.parameters() if p.requires_grad)
    sigma    = float(np.exp(final_model.smooth.logsigma.item()))

    # ── Save ─────────────────────────────────────────────────────────────────
    torch.save(final_model.state_dict(), out_dir / MODEL_NAME)
    joblib.dump(scaler, out_dir / SCALER_NAME)
    history_df.to_csv(out_dir / HISTORY_NAME, index=False)

    meta = {
        "model":            "SmoothResUNet1D",
        "variant":          "v9_hpo",
        "dataset":          "old_excel",
        "base_channels":    128,
        "trainable_params": n_params,
        "fixed_sigma":      sigma,
        "motivation": (
            "Big v9 architecture (SmoothResUNet1D) with hyperparameters tuned via "
            "Optuna TPE (40 trials x 80 epochs). Same AntennaNN Huber loss. "
            "HPO searched: lr, weight_decay, batch_size, beta, alfa, w_filter, wmag."
        ),
        "hpo": {
            "n_trials":          HPO_TRIALS,
            "epochs_per_trial":  HPO_EPOCHS,
            "best_trial":        best.number,
            "hpo_best_val_loss": best.value,
        },
        "loss": {
            "type":     "AntennaNN Huber loss",
            "beta":     bp["beta"],
            "alfa":     bp["alfa"],
            "w_filter": bp["w_filter"],
            "wmag":     bp["wmag"],
            "k_idx":    "concat(arange(0,40), arange(161,201))",
        },
        "optimizer": {
            "lr":           bp["lr"],
            "weight_decay": bp["weight_decay"],
            "batch_size":   bp["batch_size"],
            "scheduler":    f"CosineAnnealingLR(T_max={FINAL_EPOCHS})",
        },
        "n_samples":   int(len(x_scaled)),
        "n_train":     int(len(tr_idx)),
        "n_val":       int(len(va_idx)),
        "best_val_loss": float(best_val),
    }
    (out_dir / META_NAME).write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"\nSaved: {out_dir / MODEL_NAME}")
    print(f"Saved: {out_dir / SCALER_NAME}")
    print(f"Best val loss: {best_val:.6f}")
    print(f"Fixed sigma:   {sigma:.4f}")
    print("Done.")


if __name__ == "__main__":
    main()
