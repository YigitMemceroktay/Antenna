from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from train_tcnn_hilbert import INPUT_COLUMNS, TCNNHilbert


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare NN and real Sdd11 for one sample")
    parser.add_argument("--project-root", type=str, default=".")
    parser.add_argument("--seed", type=str, default="001", help="Seed id, e.g., 001")
    parser.add_argument("--sample-idx", type=int, default=0, help="Row index in selected seed file")
    parser.add_argument("--model", type=str, default="NNModel/trained_model_tcnn_hilbert.pt")
    parser.add_argument("--scaler", type=str, default="NNModel/scaler_tcnn_hilbert.gz")
    parser.add_argument("--out", type=str, default="updates/sdd11_compare_seed001_idx0.png")
    parser.add_argument("--magnitude-db", action="store_true", help="Plot |Sdd11| in dB instead of linear")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.project_root).resolve()
    lhs = root / "data" / "LHS"

    input_path = lhs / f"input_trials_done_LHS_n20_rounded_seed{args.seed}.csv"
    real_path = lhs / f"real_initial_LHS_n20_rounded_seed{args.seed}.csv"
    imag_path = lhs / f"imag_initial_LHS_n20_rounded_seed{args.seed}.csv"

    if not input_path.exists() or not real_path.exists() or not imag_path.exists():
        raise FileNotFoundError(f"Seed {args.seed} files are missing in data/LHS")

    x_df = pd.read_csv(input_path)[INPUT_COLUMNS]
    real_df = pd.read_csv(real_path)
    imag_df = pd.read_csv(imag_path)

    idx = args.sample_idx
    if idx < 0 or idx >= len(x_df):
        raise IndexError(f"sample-idx {idx} out of range [0, {len(x_df)-1}]")

    x_one = x_df.iloc[[idx]].values.astype(np.float32)
    real_true = real_df.iloc[idx].values.astype(np.float32)
    imag_true = imag_df.iloc[idx].values.astype(np.float32)
    mag_true = np.sqrt(real_true**2 + imag_true**2)

    scaler = joblib.load(root / args.scaler)
    x_scaled = scaler.transform(x_one).astype(np.float32)

    model = TCNNHilbert(input_dim=len(INPUT_COLUMNS), target_len=real_true.shape[0])
    state_dict = torch.load(root / args.model, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()

    with torch.no_grad():
        pred = model(torch.tensor(x_scaled))
    real_pred = pred[0, 0, :].numpy()
    imag_pred = pred[0, 1, :].numpy()
    mag_pred = np.sqrt(real_pred**2 + imag_pred**2)

    if args.magnitude_db:
        eps = 1e-12
        mag_true_plot = 20.0 * np.log10(np.clip(mag_true, eps, None))
        mag_pred_plot = 20.0 * np.log10(np.clip(mag_pred, eps, None))
        y_label = "|Sdd11| (dB)"
        title_suffix = "magnitude in dB"
    else:
        mag_true_plot = mag_true
        mag_pred_plot = mag_pred
        y_label = "Sdd11"
        title_suffix = "linear"

    x_axis = np.arange(real_true.shape[0])
    plt.figure(figsize=(11, 7))
    plt.plot(x_axis, mag_true_plot, label="Real Sdd11 |S|", linewidth=2)
    plt.plot(x_axis, mag_pred_plot, label="NN Sdd11 |S|", linewidth=2, linestyle="--")
    if not args.magnitude_db:
        plt.plot(x_axis, real_true, label="Real(Sdd11) True", alpha=0.7)
        plt.plot(x_axis, real_pred, label="Real(Sdd11) NN", alpha=0.7, linestyle="--")
    plt.title(f"Sdd11 comparison ({title_suffix}, seed={args.seed}, sample={idx})")
    plt.xlabel("Point index")
    plt.ylabel(y_label)
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()

    out_path = (root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()

    mse_mag = float(np.mean((mag_pred - mag_true) ** 2))
    if args.magnitude_db:
        mse_mag_db = float(np.mean((mag_pred_plot - mag_true_plot) ** 2))
    print(f"Saved plot: {out_path}")
    print(f"seed={args.seed}, sample_idx={idx}, magnitude_mse={mse_mag:.6f}")
    if args.magnitude_db:
        print(f"seed={args.seed}, sample_idx={idx}, magnitude_db_mse={mse_mag_db:.6f}")
    print("Selected geometry input:")
    print(x_df.iloc[idx].to_string())


if __name__ == "__main__":
    main()
