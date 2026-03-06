from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TCNN ablation study and rank configs")
    parser.add_argument("--project-root", type=str, default=".")
    parser.add_argument("--dataset", type=str, default="old_excel", choices=["lhs", "old_excel"])
    parser.add_argument("--epochs", type=int, default=180)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--output-csv", type=str, default="NNModel/ablation_results_tcnn.csv")
    return parser.parse_args()


def run_config(root: Path, cfg: dict, common: dict) -> dict:
    tag = cfg["tag"]
    model_name = f"ablation_{tag}.pt"
    scaler_name = f"ablation_{tag}.gz"
    history_name = f"ablation_{tag}.csv"
    meta_name = f"ablation_{tag}.json"

    cmd = [
        sys.executable,
        "updates/train_tcnn_hilbert.py",
        "--project-root",
        str(root),
        "--output-dir",
        "NNModel",
        "--dataset",
        common["dataset"],
        "--epochs",
        str(common["epochs"]),
        "--batch-size",
        str(common["batch_size"]),
        "--lr",
        str(common["lr"]),
        "--model-name",
        model_name,
        "--scaler-name",
        scaler_name,
        "--history-name",
        history_name,
        "--meta-name",
        meta_name,
        "--model-type",
        cfg["model_type"],
        "--loss-mode",
        cfg["loss_mode"],
        "--db-weight",
        str(cfg["db_weight"]),
        "--slope-weight",
        str(cfg["slope_weight"]),
        "--passivity-weight",
        str(cfg["passivity_weight"]),
        "--log-every",
        "40",
    ]

    print(f"\n=== Running {tag} ===")
    subprocess.run(cmd, check=True, cwd=root)

    meta_path = root / "NNModel" / meta_name
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return {
        "tag": tag,
        "dataset": common["dataset"],
        "model_type": cfg["model_type"],
        "loss_mode": cfg["loss_mode"],
        "db_weight": cfg["db_weight"],
        "slope_weight": cfg["slope_weight"],
        "passivity_weight": cfg["passivity_weight"],
        "best_val_mse": meta["best_val_mse"],
        "model_path": meta["model_path"],
        "scaler_path": meta["scaler_path"],
    }


def main() -> None:
    args = parse_args()
    root = Path(args.project_root).resolve()

    configs = [
        {
            "tag": "hilbert_ri",
            "model_type": "hilbert",
            "loss_mode": "ri",
            "db_weight": 0.0,
            "slope_weight": 0.0,
            "passivity_weight": 0.0,
        },
        {
            "tag": "dual_ri",
            "model_type": "dual",
            "loss_mode": "ri",
            "db_weight": 0.0,
            "slope_weight": 0.0,
            "passivity_weight": 0.0,
        },
        {
            "tag": "dual_db_hybrid_v1",
            "model_type": "dual",
            "loss_mode": "mag_db_hybrid",
            "db_weight": 0.2,
            "slope_weight": 0.05,
            "passivity_weight": 0.02,
        },
        {
            "tag": "dual_db_hybrid_v2",
            "model_type": "dual",
            "loss_mode": "mag_db_hybrid",
            "db_weight": 0.35,
            "slope_weight": 0.1,
            "passivity_weight": 0.05,
        },
    ]

    common = {
        "dataset": args.dataset,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
    }

    rows = []
    for cfg in configs:
        rows.append(run_config(root, cfg, common))

    df = pd.DataFrame(rows).sort_values("best_val_mse", ascending=True).reset_index(drop=True)
    out_csv = (root / args.output_csv).resolve()
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)

    print("\n=== Ablation ranking ===")
    print(df.to_string(index=False))
    print(f"\nSaved: {out_csv}")


if __name__ == "__main__":
    main()
