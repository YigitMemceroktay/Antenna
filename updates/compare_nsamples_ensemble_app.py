"""
compare_nsamples_ensemble_app.py

Shows performance results from the 5-run repeated training experiment:
  - Bar chart with mean ± std val loss (error bars) per (arch, n_samples)
  - Individual run dots overlaid
  - Ensemble predictions (average of 5 models) on NewData test samples
  - Per-sample RSE/MSE metrics across sample sizes

Run:
    python -m streamlit run updates/compare_nsamples_ensemble_app.py
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import torch
import torch.nn as nn
from sklearn.exceptions import InconsistentVersionWarning

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.append(str(THIS_DIR))

from train_antenna_nn_nsamples import AntennaNeuralNet
from train_resunet_v9_nsamples import SmoothResUNet1D, INPUT_COLUMNS

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR    = PROJECT_ROOT / "NNModel"
SAMPLE_SIZES = [100, 250, 500, 1000]
N_RUNS       = 10
DEVICE       = torch.device("cuda" if torch.cuda.is_available() else "cpu")

ARCH_COLORS = {
    "resunet_v9": ["#4A148C", "#6A1B9A", "#8E24AA", "#AB47BC", "#CE93D8"],
    "antenna_nn": ["#0D47A1", "#1565C0", "#1976D2", "#42A5F5", "#90CAF9"],
}
ARCH_MEAN_COLOR = {"resunet_v9": "#6A1B9A", "antenna_nn": "#1565C0"}
ARCH_LABELS     = {"resunet_v9": "ResUNet v9", "antenna_nn": "AntennaNN"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_mag(real: np.ndarray, imag: np.ndarray) -> np.ndarray:
    return np.sqrt(real ** 2 + imag ** 2)


def to_db(mag: np.ndarray) -> np.ndarray:
    return 20.0 * np.log10(np.clip(mag, 1e-12, None))


def rse(pred: np.ndarray, true: np.ndarray, eps: float = 1e-6) -> float:
    return float(np.mean(((pred - true) ** 2) / (true ** 2 + eps)))


def mse(pred: np.ndarray, true: np.ndarray) -> float:
    return float(np.mean((pred - true) ** 2))


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

@st.cache_resource
def load_antenna_nn(model_path: str, scaler_path: str):
    model = AntennaNeuralNet()
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()
    scaler = joblib.load(scaler_path)
    return model, scaler


@st.cache_resource
def load_resunet_v9(model_path: str, scaler_path: str):
    model = SmoothResUNet1D(input_dim=11, target_len=201, base_ch=128)
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()
    scaler = joblib.load(scaler_path)
    return model, scaler


def predict_single(model: nn.Module, scaler, x_raw: np.ndarray) -> np.ndarray:
    """x_raw: (11,) → returns (2, 201) real/imag prediction."""
    x_scaled = scaler.transform(x_raw.reshape(1, -1)).astype(np.float32)
    x_t      = torch.tensor(x_scaled)
    with torch.no_grad():
        out = model(x_t).cpu().numpy()[0]   # (2, 201)
    return out


def ensemble_predict(arch: str, n: int, x_raw: np.ndarray) -> np.ndarray:
    """Average predictions of all 5 runs for (arch, n). Returns (2, 201)."""
    preds = []
    loader = load_antenna_nn if arch == "antenna_nn" else load_resunet_v9
    prefix = "antenna_nn" if arch == "antenna_nn" else "resunet_v9"
    for run in range(1, N_RUNS + 1):
        tag        = f"n{n}_run{run}"
        model_path = str(MODEL_DIR / f"trained_model_{prefix}_{tag}.pt")
        scaler_path= str(MODEL_DIR / f"scaler_{prefix}_{tag}.gz")
        if not Path(model_path).exists():
            continue
        model, scaler = loader(model_path, scaler_path)
        preds.append(predict_single(model, scaler, x_raw))
    return np.mean(preds, axis=0) if preds else np.zeros((2, 201))


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data
def load_summary() -> dict:
    p = MODEL_DIR / "nsamples_summary.json"
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {}


@st.cache_data
def load_new_data_all():
    files = sorted((PROJECT_ROOT / "NewData" / "inputs").glob("inputs_LHS_n50_seed*.csv"))
    x_parts, real_parts, imag_parts = [], [], []
    for p in files:
        seed       = p.stem.split("seed")[-1]
        real_path  = PROJECT_ROOT / "NewData" / "reals"     / f"real_LHS_n50_seed{seed}.csv"
        imag_path  = PROJECT_ROOT / "NewData" / "imaginary" / f"imag_LHS_n50_seed{seed}.csv"
        if not (real_path.exists() and imag_path.exists()):
            continue
        x_df = pd.read_csv(p)[INPUT_COLUMNS]
        real = pd.read_csv(real_path).values.astype(np.float32)
        imag = pd.read_csv(imag_path).values.astype(np.float32)
        n    = min(len(x_df), len(real), len(imag))
        x_parts.append(x_df.values[:n].astype(np.float32))
        real_parts.append(real[:n])
        imag_parts.append(imag[:n])
    if not x_parts:
        return None, None, None
    return (
        np.concatenate(x_parts,    axis=0),
        np.concatenate(real_parts, axis=0),
        np.concatenate(imag_parts, axis=0),
    )


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------

st.set_page_config(page_title="N-Samples Ensemble Results", layout="wide")
st.title("Sample-Size Study — 5-Run Ensemble Results")
st.caption(f"Device: {DEVICE} | Models: 40 total (2 arch × 4 sample sizes × 5 seeds)")

summary = load_summary()

tab1, tab2, tab3 = st.tabs(["Val Loss Summary", "Ensemble Predictions", "Metric vs N-Samples"])

# ── Tab 1: Val Loss bar chart ────────────────────────────────────────────────
with tab1:
    st.subheader("Validation Loss — Mean ± Std across 5 random seeds")

    if not summary:
        st.error("nsamples_summary.json not found. Run run_nsamples_training.py first.")
    else:
        fig = go.Figure()

        for arch in ("resunet_v9", "antenna_nn"):
            means, stds, ns = [], [], []
            all_vals         = []
            for n in SAMPLE_SIZES:
                key = f"{arch}_n{n}"
                if key in summary:
                    means.append(summary[key]["mean"])
                    stds.append(summary[key]["std"])
                    ns.append(n)
                    all_vals.append(summary[key]["val_losses"])

            label = ARCH_LABELS[arch]
            color = ARCH_MEAN_COLOR[arch]

            # Bar with error bars
            fig.add_trace(go.Bar(
                name=label,
                x=[str(n) for n in ns],
                y=means,
                error_y=dict(type="data", array=stds, visible=True),
                marker_color=color,
                opacity=0.85,
            ))

            # Individual run dots
            for i, (n, vals) in enumerate(zip(ns, all_vals)):
                fig.add_trace(go.Scatter(
                    x=[str(n)] * len(vals),
                    y=vals,
                    mode="markers",
                    marker=dict(size=8, color=ARCH_COLORS[arch][i % 5], opacity=0.9,
                                line=dict(width=1, color="white")),
                    name=f"{label} runs",
                    showlegend=(i == 0),
                    legendgroup=f"{arch}_dots",
                ))

        fig.update_layout(
            barmode="group",
            xaxis_title="Training Sample Size",
            yaxis_title="Best Val Loss",
            legend=dict(groupclick="toggleitem"),
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Numeric table
        rows = []
        for arch in ("resunet_v9", "antenna_nn"):
            for n in SAMPLE_SIZES:
                key = f"{arch}_n{n}"
                if key in summary:
                    d = summary[key]
                    rows.append({
                        "Architecture": ARCH_LABELS[arch],
                        "n_samples":    n,
                        "Mean Val Loss": f"{d['mean']:.6f}",
                        "Std":           f"{d['std']:.6f}",
                        "Runs":          d["n_runs"],
                        "Individual losses": "  |  ".join(f"{v:.4f}" for v in d["val_losses"]),
                    })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)


# ── Tab 2: Ensemble predictions on test samples ──────────────────────────────
with tab2:
    st.subheader("Ensemble Predictions on NewData Test Samples")
    st.caption("Each prediction is the average of 5 independently trained models.")

    x_all, real_all, imag_all = load_new_data_all()
    if x_all is None:
        st.error("NewData not found.")
    else:
        n_test   = len(x_all)
        sample_i = st.slider("Test sample index", 0, n_test - 1, 0)
        view     = st.radio("View", ["Magnitude (dB)", "Real", "Imaginary"], horizontal=True)

        x_raw  = x_all[sample_i]
        r_true = real_all[sample_i]
        i_true = imag_all[sample_i]
        freq   = np.arange(201)

        def get_curve(pred: np.ndarray, v: str):
            if v == "Real":          return pred[0]
            if v == "Imaginary":     return pred[1]
            return to_db(to_mag(pred[0], pred[1]))

        def get_true_curve(v: str):
            if v == "Real":          return r_true
            if v == "Imaginary":     return i_true
            return to_db(to_mag(r_true, i_true))

        fig2 = go.Figure()
        true_curve = get_true_curve(view)
        fig2.add_trace(go.Scatter(x=freq, y=true_curve, name="Ground Truth",
                                  line=dict(color="black", width=2.5)))

        cols = st.columns(2)
        metric_rows = []

        for col_idx, arch in enumerate(("resunet_v9", "antenna_nn")):
            with cols[col_idx]:
                st.markdown(f"**{ARCH_LABELS[arch]}**")

            for n in SAMPLE_SIZES:
                pred  = ensemble_predict(arch, n, x_raw)
                curve = get_curve(pred, view)
                color = ARCH_COLORS[arch][SAMPLE_SIZES.index(n)]
                fig2.add_trace(go.Scatter(
                    x=freq, y=curve,
                    name=f"{ARCH_LABELS[arch]} n={n}",
                    line=dict(color=color, dash="dash" if arch == "antenna_nn" else "solid"),
                ))
                metric_rows.append({
                    "Architecture": ARCH_LABELS[arch],
                    "n_samples":    n,
                    "RSE":          f"{rse(pred, np.stack([r_true, i_true])):.6f}",
                    "MSE":          f"{mse(pred, np.stack([r_true, i_true])):.6f}",
                })

        fig2.update_layout(
            xaxis_title="Frequency index",
            yaxis_title=view,
            height=520,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(pd.DataFrame(metric_rows), use_container_width=True)


# ── Tab 3: RSE / MSE vs N across all test samples ───────────────────────────
with tab3:
    st.subheader("Test-Set RSE vs Sample Size")
    st.caption("Ensemble predictions evaluated on all available NewData samples.")

    x_all2, real_all2, imag_all2 = load_new_data_all()
    if x_all2 is None:
        st.error("NewData not found.")
    else:
        metric_choice = st.radio("Metric", ["RSE", "MSE"], horizontal=True, key="metric3")
        max_test      = st.slider("Max test samples to evaluate", 10, len(x_all2), min(100, len(x_all2)), 10)

        x_sub    = x_all2[:max_test]
        r_sub    = real_all2[:max_test]
        i_sub    = imag_all2[:max_test]
        y_sub    = np.stack([r_sub, i_sub], axis=1)   # (N, 2, 201)

        fig3 = go.Figure()

        for arch in ("resunet_v9", "antenna_nn"):
            means, stds, ns = [], [], []
            for n in SAMPLE_SIZES:
                with st.spinner(f"Evaluating {ARCH_LABELS[arch]} n={n}..."):
                    sample_metrics = []
                    for s_idx in range(len(x_sub)):
                        pred = ensemble_predict(arch, n, x_sub[s_idx])
                        true = y_sub[s_idx]
                        val  = rse(pred, true) if metric_choice == "RSE" else mse(pred, true)
                        sample_metrics.append(val)
                    means.append(float(np.mean(sample_metrics)))
                    stds.append(float(np.std(sample_metrics, ddof=1)))
                    ns.append(n)

            fig3.add_trace(go.Scatter(
                x=ns, y=means,
                error_y=dict(type="data", array=stds, visible=True),
                mode="lines+markers",
                name=ARCH_LABELS[arch],
                line=dict(color=ARCH_MEAN_COLOR[arch], width=2),
                marker=dict(size=10),
            ))

        fig3.update_layout(
            xaxis=dict(title="Training Sample Size", tickvals=SAMPLE_SIZES),
            yaxis_title=metric_choice,
            height=480,
        )
        st.plotly_chart(fig3, use_container_width=True)
