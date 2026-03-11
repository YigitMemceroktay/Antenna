"""
compare_all_models_app.py

Compares five models side by side on the same sample:
  1. Real data (ground truth)
  2. Antenna NN         (benchmark)
  3. DualResUNet        (base_ch=64, 6-term loss, 300 epochs)
  4. SmallResUNet v1    (base_ch=32, 4-term loss, 150 epochs — underfit)
  5. SmallResUNet v2    (base_ch=48, 5-term loss, 250 epochs — capacity fixed)

Run:
    python3 -m streamlit run updates/compare_all_models_app.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import torch
from sklearn.exceptions import InconsistentVersionWarning

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.append(str(THIS_DIR))

from compare_antenna_vs_tcnn_sdd11 import AntennaNeuralNet
from train_resunet_dual import DualResUNet1D, INPUT_COLUMNS
from train_resunet_small import SmallResUNet1D
from train_resunet_small_v2 import SmallResUNet1DV2

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_mag(real: np.ndarray, imag: np.ndarray) -> np.ndarray:
    return np.sqrt(real**2 + imag**2)


def to_db(mag: np.ndarray) -> np.ndarray:
    return 20.0 * np.log10(np.clip(mag, 1e-12, None))


def rse(pred: np.ndarray, true: np.ndarray, eps: float = 1e-6) -> float:
    return float(np.mean(((pred - true) ** 2) / (true**2 + eps)))


# ---------------------------------------------------------------------------
# Cached loaders
# ---------------------------------------------------------------------------

@st.cache_data
def list_lhs_files() -> list[Path]:
    return sorted((PROJECT_ROOT / "data" / "LHS").glob("input_trials_done_LHS_n20_rounded_seed*.csv"))


@st.cache_data
def load_lhs_seed(input_file: str):
    p = Path(input_file)
    seed = p.stem.split("seed")[-1]
    lhs  = p.parent
    x_df = pd.read_csv(p)[INPUT_COLUMNS]
    real = pd.read_csv(lhs / f"real_initial_LHS_n20_rounded_seed{seed}.csv").values.astype(np.float32)
    imag = pd.read_csv(lhs / f"imag_initial_LHS_n20_rounded_seed{seed}.csv").values.astype(np.float32)
    return x_df, real, imag, seed


@st.cache_data
def load_old_excel():
    old  = PROJECT_ROOT / "old" / "data"
    x_df = pd.read_excel(old / "input_parameters.xlsx")[INPUT_COLUMNS]
    real = pd.read_excel(old / "reel.xlsx").values.astype(np.float32)
    imag = pd.read_excel(old / "imaginary.xlsx").values.astype(np.float32)
    n = min(len(x_df), len(real), len(imag))
    return x_df.iloc[:n].copy(), real[:n], imag[:n]


@st.cache_resource
def load_antenna_nn(model_path: str, scaler_path: str):
    scaler = joblib.load(PROJECT_ROOT / scaler_path)
    model  = AntennaNeuralNet()
    model.load_state_dict(torch.load(PROJECT_ROOT / model_path, map_location="cpu"))
    model.eval()
    return model, scaler


@st.cache_resource
def load_dual_resunet(model_path: str, scaler_path: str, target_len: int):
    scaler = joblib.load(PROJECT_ROOT / scaler_path)
    model  = DualResUNet1D(input_dim=len(INPUT_COLUMNS), target_len=target_len)
    model.load_state_dict(torch.load(PROJECT_ROOT / model_path, map_location="cpu"))
    model.eval()
    return model, scaler


@st.cache_resource
def load_small_resunet(model_path: str, scaler_path: str, target_len: int):
    scaler = joblib.load(PROJECT_ROOT / scaler_path)
    model  = SmallResUNet1D(input_dim=len(INPUT_COLUMNS), target_len=target_len)
    model.load_state_dict(torch.load(PROJECT_ROOT / model_path, map_location="cpu"))
    model.eval()
    return model, scaler


@st.cache_resource
def load_small_resunet_v2(model_path: str, scaler_path: str, target_len: int):
    scaler = joblib.load(PROJECT_ROOT / scaler_path)
    model  = SmallResUNet1DV2(input_dim=len(INPUT_COLUMNS), target_len=target_len)
    model.load_state_dict(torch.load(PROJECT_ROOT / model_path, map_location="cpu"))
    model.eval()
    return model, scaler


# ---------------------------------------------------------------------------
# Prediction helper
# ---------------------------------------------------------------------------

def predict(model: torch.nn.Module, scaler, x_row: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Returns (real_pred, imag_pred) as 1D numpy arrays."""
    x_scaled = scaler.transform(x_row.reshape(1, -1)).astype(np.float32)
    with torch.no_grad():
        out = model(torch.tensor(x_scaled))  # (1, 2, L)
    return out[0, 0, :].numpy(), out[0, 1, :].numpy()


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="All Models Comparator", layout="wide")
    st.title("S11 Comparison: Real vs Antenna NN vs DualResUNet vs SmallResUNet")

    # ---- Sidebar ----
    with st.sidebar:
        st.header("Controls")
        dataset      = st.selectbox("Dataset", ["lhs", "old_excel"], index=0)
        trace_label  = st.selectbox("Trace label", ["S11", "Sdd11"], index=0)
        magnitude_db = st.checkbox("Show magnitude in dB", value=True)

        st.subheader("Model paths")
        ant_model_path   = st.text_input("Antenna NN model",      value="NNModel/trained_model.pt")
        ant_scaler_path  = st.text_input("Antenna NN scaler",     value="NNModel/scaler.gz")
        dual_model_path  = st.text_input("DualResUNet model",     value="NNModel/trained_model_resunet_dual.pt")
        dual_scaler_path = st.text_input("DualResUNet scaler",    value="NNModel/scaler_resunet_dual.gz")
        sml_model_path   = st.text_input("SmallResUNet v1 model",  value="NNModel/trained_model_resunet_small.pt")
        sml_scaler_path  = st.text_input("SmallResUNet v1 scaler", value="NNModel/scaler_resunet_small.gz")
        sml2_model_path  = st.text_input("SmallResUNet v2 model",  value="NNModel/trained_model_resunet_small_v2.pt")
        sml2_scaler_path = st.text_input("SmallResUNet v2 scaler", value="NNModel/scaler_resunet_small_v2.gz")

    # ---- Load data ----
    if dataset == "lhs":
        files = list_lhs_files()
        if not files:
            st.error("No LHS files found in data/LHS"); return
        selected_file = st.selectbox("LHS file", [f.name for f in files])
        fpath = next(f for f in files if f.name == selected_file)
        x_df, real_all, imag_all, seed = load_lhs_seed(str(fpath))
        dataset_label = f"seed{seed}"
    else:
        x_df, real_all, imag_all = load_old_excel()
        dataset_label = "old_excel"

    idx = st.slider("Sample index", 0, len(x_df) - 1, 0)

    real_true = real_all[idx]
    imag_true = imag_all[idx]
    x_row     = x_df.iloc[idx].values.astype(np.float32)
    target_len = real_true.shape[0]

    # ---- Load models ----
    try:
        ant_model, ant_scaler = load_antenna_nn(ant_model_path, ant_scaler_path)
    except Exception as e:
        st.warning(f"Antenna NN could not be loaded: {e}")
        ant_model = None

    try:
        dual_model, dual_scaler = load_dual_resunet(dual_model_path, dual_scaler_path, target_len)
    except Exception as e:
        st.warning(f"DualResUNet could not be loaded: {e}")
        dual_model = None

    try:
        sml_model, sml_scaler = load_small_resunet(sml_model_path, sml_scaler_path, target_len)
    except Exception as e:
        st.warning(f"SmallResUNet v1 could not be loaded: {e}")
        sml_model = None

    try:
        sml2_model, sml2_scaler = load_small_resunet_v2(sml2_model_path, sml2_scaler_path, target_len)
    except Exception as e:
        st.warning(f"SmallResUNet v2 could not be loaded: {e}")
        sml2_model = None

    # ---- Predictions ----
    def get_curve(model, scaler):
        if model is None:
            return None, None
        r, i = predict(model, scaler, x_row)
        return r, i

    real_ant,  imag_ant  = get_curve(ant_model,  ant_scaler)
    real_dual, imag_dual = get_curve(dual_model, dual_scaler)
    real_sml,  imag_sml  = get_curve(sml_model,  sml_scaler)
    real_sml2, imag_sml2 = get_curve(sml2_model, sml2_scaler)

    # ---- Convert to display space ----
    def display(real, imag):
        if real is None:
            return None
        mag = to_mag(real, imag)
        return to_db(mag) if magnitude_db else mag

    y_true = display(real_true, imag_true)
    y_ant  = display(real_ant,  imag_ant)
    y_dual = display(real_dual, imag_dual)
    y_sml  = display(real_sml,  imag_sml)
    y_sml2 = display(real_sml2, imag_sml2)
    y_label = f"|{trace_label}| (dB)" if magnitude_db else f"|{trace_label}|"

    # ---- Metrics ----
    def metrics_row(y_pred, label):
        if y_pred is None:
            return {}
        return {
            f"{label} MSE": f"{np.mean((y_pred - y_true)**2):.6f}",
            f"{label} RSE": f"{rse(y_pred, y_true):.6f}",
        }

    ant_m  = metrics_row(y_ant,  "Antenna NN")
    dual_m = metrics_row(y_dual, "DualResUNet")
    sml_m  = metrics_row(y_sml,  "Small v1")
    sml2_m = metrics_row(y_sml2, "Small v2")

    all_metrics = {**ant_m, **dual_m, **sml_m, **sml2_m}
    cols = st.columns(2 + len(all_metrics))
    cols[0].metric("Dataset", dataset_label)
    cols[1].metric("Sample", idx)
    for i, (label, val) in enumerate(all_metrics.items()):
        cols[2 + i].metric(label, val)

    # ---- Plot ----
    x_axis = np.arange(len(y_true))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_axis, y=y_true, mode="lines", name=f"Real {trace_label}",
                             line=dict(width=3, color="black")))
    if y_ant is not None:
        fig.add_trace(go.Scatter(x=x_axis, y=y_ant, mode="lines", name="Antenna NN",
                                 line=dict(width=2, dash="dash", color="royalblue")))
    if y_dual is not None:
        fig.add_trace(go.Scatter(x=x_axis, y=y_dual, mode="lines", name="DualResUNet (base_ch=64)",
                                 line=dict(width=2, dash="dot", color="firebrick")))
    if y_sml is not None:
        fig.add_trace(go.Scatter(x=x_axis, y=y_sml, mode="lines", name="Small v1 (base_ch=32)",
                                 line=dict(width=2, dash="dashdot", color="seagreen")))
    if y_sml2 is not None:
        fig.add_trace(go.Scatter(x=x_axis, y=y_sml2, mode="lines", name="Small v2 (base_ch=48)",
                                 line=dict(width=2, dash="longdash", color="darkorange")))

    fig.update_layout(
        title=f"{trace_label} — {dataset_label}, sample {idx}",
        xaxis_title="Frequency point index",
        yaxis_title=y_label,
        template="plotly_white",
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Selected geometry input"):
        st.dataframe(x_df.iloc[[idx]], use_container_width=True)

    # ---- Model info ----
    with st.expander("Model info"):
        st.markdown("""
| Model | base_ch | Params | Loss terms | Epochs |
|-------|---------|--------|------------|--------|
| Antenna NN | — | ~small | MSE | — |
| DualResUNet | 64 | ~1.5M | 6 (ri, mag_db, slope, curv, passivity, hilbert) | 300 |
| Small v1 | 32 | 193k | 4 (ri, mag_db, slope, passivity) | 150 — underfits |
| Small v2 | 48 | ~450k | 5 (ri, mag_db, slope, curv, passivity) | 250 |
        """)

    # ---- Training curves ----
    st.subheader("Training curves (train vs val loss)")

    history_files = {
        "DualResUNet":  PROJECT_ROOT / "NNModel" / "history_resunet_dual.csv",
        "Small v1":     PROJECT_ROOT / "NNModel" / "history_resunet_small.csv",
        "Small v2":     PROJECT_ROOT / "NNModel" / "history_resunet_small_v2.csv",
    }

    available = {name: path for name, path in history_files.items() if path.exists()}
    if not available:
        st.info("No history CSV files found.")
    else:
        selected_histories = st.multiselect(
            "Show training curves for:",
            options=list(available.keys()),
            default=list(available.keys()),
        )

        colors = {"DualResUNet": "firebrick", "Small v1": "seagreen", "Small v2": "darkorange"}
        fig2 = go.Figure()

        for name in selected_histories:
            df = pd.read_csv(available[name])
            fig2.add_trace(go.Scatter(
                x=df["epoch"], y=df["train_loss"],
                mode="lines", name=f"{name} train",
                line=dict(color=colors[name], width=2),
            ))
            fig2.add_trace(go.Scatter(
                x=df["epoch"], y=df["val_loss"],
                mode="lines", name=f"{name} val",
                line=dict(color=colors[name], width=2, dash="dash"),
            ))

        fig2.update_layout(
            xaxis_title="Epoch",
            yaxis_title="Loss",
            template="plotly_white",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Solid = train loss  |  Dashed = val loss  |  Train ≈ Val → no overfitting")


if __name__ == "__main__":
    main()
