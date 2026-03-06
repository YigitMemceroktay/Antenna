from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch

from compare_antenna_vs_tcnn_sdd11 import AntennaNeuralNet, to_db
from train_tcnn_hilbert import INPUT_COLUMNS, create_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank models by dataset-wide dB MSE")
    parser.add_argument("--project-root", type=str, default=".")
    parser.add_argument("--dataset", type=str, default="old_excel", choices=["old_excel", "lhs"])
    parser.add_argument("--ablation-csv", type=str, default="NNModel/ablation_results_tcnn_sanity.csv")
    parser.add_argument("--output-csv", type=str, default="NNModel/model_ranking_db.csv")
    return parser.parse_args()


def load_dataset(root: Path, dataset: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if dataset == "old_excel":
        old = root / "old" / "data"
        x = pd.read_excel(old / "input_parameters.xlsx")[INPUT_COLUMNS].values.astype(np.float32)
        real = pd.read_excel(old / "reel.xlsx").values.astype(np.float32)
        imag = pd.read_excel(old / "imaginary.xlsx").values.astype(np.float32)
        n = min(len(x), len(real), len(imag))
        return x[:n], real[:n], imag[:n]

    lhs = root / "data" / "LHS"
    x_all, r_all, i_all = [], [], []
    for inp in sorted(lhs.glob("input_trials_done_LHS_n20_rounded_seed*.csv")):
        seed = inp.stem.split("seed")[-1]
        real_path = lhs / f"real_initial_LHS_n20_rounded_seed{seed}.csv"
        imag_path = lhs / f"imag_initial_LHS_n20_rounded_seed{seed}.csv"
        if not (real_path.exists() and imag_path.exists()):
            continue
        x_df = pd.read_csv(inp)[INPUT_COLUMNS]
        r_df = pd.read_csv(real_path)
        i_df = pd.read_csv(imag_path)
        n = min(len(x_df), len(r_df), len(i_df))
        x_all.append(x_df.values[:n].astype(np.float32))
        r_all.append(r_df.values[:n].astype(np.float32))
        i_all.append(i_df.values[:n].astype(np.float32))
    x = np.concatenate(x_all, axis=0)
    real = np.concatenate(r_all, axis=0)
    imag = np.concatenate(i_all, axis=0)
    return x, real, imag


def eval_antenna(root: Path, x: np.ndarray, real: np.ndarray, imag: np.ndarray) -> dict:
    scaler = joblib.load(root / "NNModel" / "scaler.gz")
    x_scaled = scaler.transform(x).astype(np.float32)

    model = AntennaNeuralNet()
    model.load_state_dict(torch.load(root / "NNModel" / "trained_model.pt", map_location="cpu"))
    model.eval()

    with torch.no_grad():
        pred = model(torch.tensor(x_scaled)).numpy()

    mag_true = np.sqrt(real**2 + imag**2)
    mag_pred = np.sqrt(pred[:, 0, :] ** 2 + pred[:, 1, :] ** 2)
    db_true = to_db(mag_true)
    db_pred = to_db(mag_pred)
    sample_mse = ((db_pred - db_true) ** 2).mean(axis=1)
    return {
        "model": "antenna_nn",
        "model_type": "dual",
        "mean_db_mse": float(sample_mse.mean()),
        "median_db_mse": float(np.median(sample_mse)),
    }


def eval_tcnn(
    x: np.ndarray,
    real: np.ndarray,
    imag: np.ndarray,
    model_path: Path,
    scaler_path: Path,
    model_type: str,
) -> dict:
    scaler = joblib.load(scaler_path)
    x_scaled = scaler.transform(x).astype(np.float32)

    model = create_model(model_type, input_dim=x.shape[1], target_len=real.shape[1])
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    with torch.no_grad():
        pred = model(torch.tensor(x_scaled)).numpy()

    mag_true = np.sqrt(real**2 + imag**2)
    mag_pred = np.sqrt(pred[:, 0, :] ** 2 + pred[:, 1, :] ** 2)
    db_true = to_db(mag_true)
    db_pred = to_db(mag_pred)
    sample_mse = ((db_pred - db_true) ** 2).mean(axis=1)
    return {
        "model": model_path.name,
        "model_type": model_type,
        "mean_db_mse": float(sample_mse.mean()),
        "median_db_mse": float(np.median(sample_mse)),
    }


def main() -> None:
    args = parse_args()
    root = Path(args.project_root).resolve()

    x, real, imag = load_dataset(root, args.dataset)
    rows = [eval_antenna(root, x, real, imag)]

    ablation = pd.read_csv(root / args.ablation_csv)
    for _, row in ablation.iterrows():
        model_path = Path(row["model_path"])
        scaler_path = Path(row["scaler_path"])
        model_type = str(row.get("model_type", "hilbert"))
        rows.append(eval_tcnn(x, real, imag, model_path, scaler_path, model_type=model_type))

    out = pd.DataFrame(rows).sort_values("mean_db_mse", ascending=True).reset_index(drop=True)
    output_csv = (root / args.output_csv).resolve()
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_csv, index=False)
    print(out.to_string(index=False))
    print(f"\nSaved: {output_csv}")


if __name__ == "__main__":
    main()
