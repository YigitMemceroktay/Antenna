from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch

from train_resunet_dual import INPUT_COLUMNS, DualResUNet1D, load_lhs_data, load_old_excel_data


def to_db_from_ri(real: np.ndarray, imag: np.ndarray) -> np.ndarray:
    mag = np.sqrt(real**2 + imag**2 + 1e-12)
    return 20.0 * np.log10(np.clip(mag, 1e-8, None))


def rse_db(y_pred_db: np.ndarray, y_true_db: np.ndarray, eps: float = 1e-4) -> float:
    return float(np.mean(((y_pred_db - y_true_db) ** 2) / (y_true_db**2 + eps)))


def load_dataset(root: Path, dataset: str) -> tuple[np.ndarray, np.ndarray]:
    if dataset == "old_excel":
        return load_old_excel_data(root)
    return load_lhs_data(root)


def build_model(model_path: Path, input_dim: int, target_len: int, base_channels: int, device: torch.device) -> DualResUNet1D:
    model = DualResUNet1D(input_dim=input_dim, target_len=target_len, base_ch=base_channels).to(device)
    state = torch.load(model_path, map_location=device)
    model.load_state_dict(state)
    model.eval()
    return model


def predict_db(model: DualResUNet1D, x_scaled: np.ndarray, batch_size: int, device: torch.device) -> np.ndarray:
    preds = []
    with torch.no_grad():
        for start in range(0, len(x_scaled), batch_size):
            xb = torch.tensor(x_scaled[start : start + batch_size], dtype=torch.float32, device=device)
            yb = model(xb).detach().cpu().numpy()
            preds.append(yb)
    pred = np.concatenate(preds, axis=0)
    return to_db_from_ri(pred[:, 0, :], pred[:, 1, :])


def permutation_importance(
    model: DualResUNet1D,
    x_scaled: np.ndarray,
    y_true_db: np.ndarray,
    batch_size: int,
    device: torch.device,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    baseline_pred_db = predict_db(model, x_scaled, batch_size=batch_size, device=device)
    baseline_rse = rse_db(baseline_pred_db, y_true_db)

    rows = []
    for feat_idx, feat_name in enumerate(INPUT_COLUMNS):
        x_perm = x_scaled.copy()
        shuffled = x_perm[:, feat_idx].copy()
        rng.shuffle(shuffled)
        x_perm[:, feat_idx] = shuffled

        pred_perm_db = predict_db(model, x_perm, batch_size=batch_size, device=device)
        perm_rse = rse_db(pred_perm_db, y_true_db)

        rows.append(
            {
                "feature": feat_name,
                "baseline_rse": baseline_rse,
                "permuted_rse": perm_rse,
                "delta_rse": perm_rse - baseline_rse,
            }
        )

    return pd.DataFrame(rows).sort_values("delta_rse", ascending=False).reset_index(drop=True)


def gradient_sensitivity(
    model: DualResUNet1D,
    x_scaled: np.ndarray,
    sample_limit: int,
    batch_size: int,
    device: torch.device,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    x_use = x_scaled[:sample_limit]
    n_freq = model.target_len

    grad_sum_by_feature = np.zeros(len(INPUT_COLUMNS), dtype=np.float64)
    grad_count = 0

    grad_sum_freq_feature = np.zeros((n_freq, len(INPUT_COLUMNS)), dtype=np.float64)
    freq_count = 0

    for start in range(0, len(x_use), batch_size):
        xb_np = x_use[start : start + batch_size]
        xb = torch.tensor(xb_np, dtype=torch.float32, device=device, requires_grad=True)

        pred = model(xb)
        real_p = pred[:, 0, :]
        imag_p = pred[:, 1, :]
        mag_p = torch.sqrt(real_p**2 + imag_p**2 + 1e-12)
        db_p = 20.0 * torch.log10(torch.clamp(mag_p, min=1e-8))

        scalar = db_p.sum()
        grads_global = torch.autograd.grad(scalar, xb, retain_graph=True)[0]
        grad_sum_by_feature += grads_global.detach().abs().sum(dim=0).cpu().numpy()
        grad_count += xb.shape[0] * n_freq

        for freq_idx in range(n_freq):
            gk = torch.autograd.grad(db_p[:, freq_idx].sum(), xb, retain_graph=True)[0]
            grad_sum_freq_feature[freq_idx] += gk.detach().abs().sum(dim=0).cpu().numpy()
            freq_count += xb.shape[0]

    mean_abs_grad_by_feature = grad_sum_by_feature / max(1, grad_count)
    grad_feature_df = pd.DataFrame(
        {
            "feature": INPUT_COLUMNS,
            "mean_abs_grad_db": mean_abs_grad_by_feature,
        }
    ).sort_values("mean_abs_grad_db", ascending=False).reset_index(drop=True)

    grad_freq_feature = grad_sum_freq_feature / max(1, freq_count)
    grad_freq_df = pd.DataFrame(grad_freq_feature, columns=INPUT_COLUMNS)
    grad_freq_df.insert(0, "freq_index", np.arange(n_freq))

    return grad_feature_df, grad_freq_df


def frequency_error_profile(
    y_pred_db: np.ndarray,
    y_true_db: np.ndarray,
    eps: float = 1e-4,
) -> pd.DataFrame:
    mse = np.mean((y_pred_db - y_true_db) ** 2, axis=0)
    rse = np.mean(((y_pred_db - y_true_db) ** 2) / (y_true_db**2 + eps), axis=0)
    return pd.DataFrame(
        {
            "freq_index": np.arange(y_true_db.shape[1]),
            "mse_db": mse,
            "rse_db": rse,
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ResUNet error analysis: feature importance + sensitivity + frequency profile")
    parser.add_argument("--project-root", type=str, default=".")
    parser.add_argument("--dataset", type=str, default="old_excel", choices=["old_excel", "lhs"])
    parser.add_argument("--model-path", type=str, default="NNModel/trained_model_resunet_dual.pt")
    parser.add_argument("--scaler-path", type=str, default="NNModel/scaler_resunet_dual.gz")
    parser.add_argument("--meta-path", type=str, default="NNModel/meta_resunet_dual.json")
    parser.add_argument("--output-dir", type=str, default="NNModel/analysis")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--sample-limit", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cpu", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.project_root).resolve()
    out_dir = (root / args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    model_path = (root / args.model_path).resolve()
    scaler_path = (root / args.scaler_path).resolve()
    meta_path = (root / args.meta_path).resolve()

    x_raw, y = load_dataset(root, args.dataset)
    scaler = joblib.load(scaler_path)
    x_scaled = scaler.transform(x_raw).astype(np.float32)

    y_true_db = to_db_from_ri(y[:, 0, :], y[:, 1, :])

    base_channels = 64
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            base_channels = int(meta.get("base_channels", 64))
        except json.JSONDecodeError:
            pass

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    model = build_model(
        model_path=model_path,
        input_dim=x_scaled.shape[1],
        target_len=y.shape[-1],
        base_channels=base_channels,
        device=device,
    )

    pred_db = predict_db(model, x_scaled, batch_size=args.batch_size, device=device)

    perm_df = permutation_importance(
        model=model,
        x_scaled=x_scaled,
        y_true_db=y_true_db,
        batch_size=args.batch_size,
        device=device,
        seed=args.seed,
    )
    grad_feat_df, grad_freq_df = gradient_sensitivity(
        model=model,
        x_scaled=x_scaled,
        sample_limit=min(args.sample_limit, len(x_scaled)),
        batch_size=args.batch_size,
        device=device,
    )
    freq_err_df = frequency_error_profile(pred_db, y_true_db)

    perm_path = out_dir / "feature_permutation_importance.csv"
    grad_feat_path = out_dir / "feature_gradient_sensitivity.csv"
    grad_freq_path = out_dir / "feature_frequency_sensitivity.csv"
    freq_err_path = out_dir / "frequency_error_profile.csv"

    perm_df.to_csv(perm_path, index=False)
    grad_feat_df.to_csv(grad_feat_path, index=False)
    grad_freq_df.to_csv(grad_freq_path, index=False)
    freq_err_df.to_csv(freq_err_path, index=False)

    summary = {
        "dataset": args.dataset,
        "n_samples": int(len(x_scaled)),
        "sample_limit_gradient": int(min(args.sample_limit, len(x_scaled))),
        "baseline_rse": float(rse_db(pred_db, y_true_db)),
        "top5_permutation": perm_df.head(5).to_dict(orient="records"),
        "top5_gradient": grad_feat_df.head(5).to_dict(orient="records"),
        "outputs": {
            "feature_permutation_importance": str(perm_path),
            "feature_gradient_sensitivity": str(grad_feat_path),
            "feature_frequency_sensitivity": str(grad_freq_path),
            "frequency_error_profile": str(freq_err_path),
        },
    }
    summary_path = out_dir / "analysis_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Saved: {perm_path}")
    print(f"Saved: {grad_feat_path}")
    print(f"Saved: {grad_freq_path}")
    print(f"Saved: {freq_err_path}")
    print(f"Saved: {summary_path}")
    print("\nTop permutation features by delta RSE:")
    print(perm_df.head(5).to_string(index=False))
    print("\nTop gradient-sensitive features:")
    print(grad_feat_df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
