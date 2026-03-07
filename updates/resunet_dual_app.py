from __future__ import annotations

from pathlib import Path
import warnings
import sys

import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import torch
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter

from sklearn.exceptions import InconsistentVersionWarning

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.append(str(THIS_DIR))

from compare_antenna_vs_tcnn_sdd11 import AntennaNeuralNet
from train_resunet_dual import INPUT_COLUMNS, DualResUNet1D


warnings.filterwarnings("ignore", category=InconsistentVersionWarning)


def to_mag(real: np.ndarray, imag: np.ndarray) -> np.ndarray:
    return np.sqrt(real**2 + imag**2)


def to_db(mag: np.ndarray) -> np.ndarray:
    return 20.0 * np.log10(np.clip(mag, 1e-12, None))


def rse(y_pred: np.ndarray, y_true: np.ndarray, eps: float = 1e-6) -> float:
    return float(np.mean(((y_pred - y_true) ** 2) / (y_true**2 + eps)))


def smooth_1d(y: np.ndarray, method: str, strength: float, window: int, poly: int) -> np.ndarray:
    if method == "none":
        return y

    if method == "moving_average":
        w = max(3, int(window))
        if w % 2 == 0:
            w += 1
        kernel = np.ones(w, dtype=np.float64) / w
        y_pad = np.pad(y, (w // 2, w // 2), mode="reflect")
        return np.convolve(y_pad, kernel, mode="valid")

    if method == "savgol":
        w = max(5, int(window))
        if w % 2 == 0:
            w += 1
        w = min(w, len(y) - (1 - len(y) % 2))
        if w <= poly:
            w = poly + 3 if (poly + 3) % 2 == 1 else poly + 4
        w = min(w, len(y) - (1 - len(y) % 2))
        if w < 5:
            return y
        return savgol_filter(y, window_length=w, polyorder=min(poly, w - 2), mode="interp")

    if method == "gaussian":
        sigma = max(0.1, float(strength))
        return gaussian_filter1d(y, sigma=sigma, mode="reflect")

    return y


@st.cache_data
def list_lhs_files(project_root: str) -> list[Path]:
    lhs = Path(project_root) / "data" / "LHS"
    return sorted(lhs.glob("input_trials_done_LHS_n20_rounded_seed*.csv"))


@st.cache_data
def load_lhs_seed(input_file: str):
    input_path = Path(input_file)
    seed = input_path.stem.split("seed")[-1]
    lhs = input_path.parent
    real_path = lhs / f"real_initial_LHS_n20_rounded_seed{seed}.csv"
    imag_path = lhs / f"imag_initial_LHS_n20_rounded_seed{seed}.csv"
    x_df = pd.read_csv(input_path)[INPUT_COLUMNS]
    real = pd.read_csv(real_path).values.astype(np.float32)
    imag = pd.read_csv(imag_path).values.astype(np.float32)
    return x_df, real, imag, seed


@st.cache_data
def load_old_excel(project_root: str):
    old = Path(project_root) / "old" / "data"
    x_df = pd.read_excel(old / "input_parameters.xlsx")[INPUT_COLUMNS]
    real = pd.read_excel(old / "reel.xlsx").values.astype(np.float32)
    imag = pd.read_excel(old / "imaginary.xlsx").values.astype(np.float32)
    n = min(len(x_df), len(real), len(imag))
    return x_df.iloc[:n].copy(), real[:n], imag[:n]


@st.cache_resource
def load_antenna(project_root: str, model_path: str, scaler_path: str):
    root = Path(project_root)
    scaler = joblib.load(root / scaler_path)
    model = AntennaNeuralNet()
    model.load_state_dict(torch.load(root / model_path, map_location="cpu"))
    model.eval()
    return model, scaler


@st.cache_resource
def load_resunet(project_root: str, model_path: str, scaler_path: str, target_len: int):
    root = Path(project_root)
    scaler = joblib.load(root / scaler_path)
    model = DualResUNet1D(input_dim=len(INPUT_COLUMNS), target_len=target_len)
    model.load_state_dict(torch.load(root / model_path, map_location="cpu"))
    model.eval()
    return model, scaler


def main() -> None:
    st.set_page_config(page_title="ResUNet Dual Comparator", layout="wide")
    st.title("ResUNet Dual Web App: Real vs Antenna NN vs Our ResUNet")

    project_root = Path(__file__).resolve().parents[1]

    with st.sidebar:
        st.header("Controls")
        dataset = st.selectbox("Dataset", ["lhs", "old_excel"], index=0)
        trace_label = st.selectbox("Trace label", ["S11", "Sdd11"], index=0)
        magnitude_db = st.checkbox("Show magnitude in dB", value=True)

        st.subheader("Post-smoothing")
        apply_smoothing = st.checkbox("Apply smoothing to model outputs", value=False)
        smooth_method = st.selectbox(
            "Method",
            ["none", "savgol", "gaussian", "moving_average"],
            index=1,
            disabled=not apply_smoothing,
        )
        smooth_strength = st.slider("Gaussian sigma", 0.1, 6.0, 1.5, 0.1, disabled=(not apply_smoothing or smooth_method != "gaussian"))
        smooth_window = st.slider("Window length", 5, 41, 11, 2, disabled=(not apply_smoothing or smooth_method == "gaussian"))
        smooth_poly = st.slider("SavGol polyorder", 2, 5, 3, 1, disabled=(not apply_smoothing or smooth_method != "savgol"))

        antenna_model_path = st.text_input("Antenna model", value="NNModel/trained_model.pt")
        antenna_scaler_path = st.text_input("Antenna scaler", value="NNModel/scaler.gz")

        our_model_path = st.text_input("ResUNet model", value="NNModel/trained_model_resunet_dual.pt")
        our_scaler_path = st.text_input("ResUNet scaler", value="NNModel/scaler_resunet_dual.gz")

    if dataset == "lhs":
        files = list_lhs_files(str(project_root))
        if not files:
            st.error("No LHS files found in data/LHS")
            return
        labels = [f.name for f in files]
        selected = st.selectbox("LHS file", labels)
        selected_file = next(f for f in files if f.name == selected)
        x_df, real_all, imag_all, seed = load_lhs_seed(str(selected_file))
        dataset_label = f"seed{seed}"
    else:
        x_df, real_all, imag_all = load_old_excel(str(project_root))
        dataset_label = "old_excel"

    idx = st.slider("Sample index", min_value=0, max_value=len(x_df) - 1, value=0, step=1)

    real_true = real_all[idx]
    imag_true = imag_all[idx]
    mag_true = to_mag(real_true, imag_true)

    antenna_model, antenna_scaler = load_antenna(str(project_root), antenna_model_path, antenna_scaler_path)
    resunet_model, resunet_scaler = load_resunet(str(project_root), our_model_path, our_scaler_path, target_len=real_true.shape[0])

    x_one = x_df.iloc[[idx]].values.astype(np.float32)
    x_ant = antenna_scaler.transform(x_one).astype(np.float32)
    x_ours = resunet_scaler.transform(x_one).astype(np.float32)

    with torch.no_grad():
        ant_pred = antenna_model(torch.tensor(x_ant))
        our_pred = resunet_model(torch.tensor(x_ours))

    real_ant, imag_ant = ant_pred[0, 0, :].numpy(), ant_pred[0, 1, :].numpy()
    real_ours, imag_ours = our_pred[0, 0, :].numpy(), our_pred[0, 1, :].numpy()

    mag_ant = to_mag(real_ant, imag_ant)
    mag_ours = to_mag(real_ours, imag_ours)

    if magnitude_db:
        y_true = to_db(mag_true)
        y_ant = to_db(mag_ant)
        y_ours = to_db(mag_ours)
        y_label = f"|{trace_label}| (dB)"
    else:
        y_true = mag_true
        y_ant = mag_ant
        y_ours = mag_ours
        y_label = f"|{trace_label}|"

    if apply_smoothing:
        y_ours = smooth_1d(y_ours, method=smooth_method, strength=smooth_strength, window=smooth_window, poly=smooth_poly)

    mse_ant = float(np.mean((y_ant - y_true) ** 2))
    mse_ours = float(np.mean((y_ours - y_true) ** 2))
    rse_ant = rse(y_ant, y_true)
    rse_ours = rse(y_ours, y_true)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Dataset", dataset_label)
    c2.metric("Antenna NN MSE", f"{mse_ant:.6f}")
    c3.metric("ResUNet MSE", f"{mse_ours:.6f}")
    c4.metric("Antenna NN RSE", f"{rse_ant:.6f}")
    c5.metric("ResUNet RSE", f"{rse_ours:.6f}")

    x_axis = np.arange(len(y_true))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_axis, y=y_true, mode="lines", name=f"Real {trace_label}", line=dict(width=3)))
    fig.add_trace(go.Scatter(x=x_axis, y=y_ant, mode="lines", name="Antenna NN", line=dict(width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=x_axis, y=y_ours, mode="lines", name="Our ResUNet", line=dict(width=2, dash="dot")))
    fig.update_layout(
        title=f"{trace_label} comparison ({dataset_label}, sample={idx})",
        xaxis_title="Point index",
        yaxis_title=y_label,
        template="plotly_white",
        height=520,
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Selected geometry input"):
        st.dataframe(x_df.iloc[[idx]], use_container_width=True)


if __name__ == "__main__":
    main()
