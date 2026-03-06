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
import torch.nn as nn
import torch.nn.functional as F
from sklearn.exceptions import InconsistentVersionWarning

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.append(str(THIS_DIR))

from train_tcnn_hilbert import INPUT_COLUMNS, TCNNHilbert
from train_tcnn_hilbert import create_model


warnings.filterwarnings("ignore", category=InconsistentVersionWarning)


class AddCoords1D(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, out: torch.Tensor) -> torch.Tensor:
        in_batch, _, in_w = out.shape
        width_coords = torch.linspace(-1, 1, steps=in_w, device=out.device)
        wc = width_coords.repeat(in_batch, 1, 1)
        return torch.cat((out, wc), 1)


class AntennaNeuralNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.logsigma = nn.Parameter(torch.ones(1))
        self.filter_size = 41

        self.add_coords = AddCoords1D()
        self.linear = nn.Sequential(
            nn.Linear(11, 60),
            nn.Tanh(),
            nn.Linear(60, 60),
            nn.Tanh(),
            nn.Linear(60, 60),
            nn.Tanh(),
        )
        self.deconv1 = nn.Sequential(
            nn.ConvTranspose1d(in_channels=60, out_channels=40, kernel_size=21, stride=1),
            nn.Tanh(),
        )
        self.deconv2 = nn.Sequential(
            nn.ConvTranspose1d(in_channels=40, out_channels=40, kernel_size=7, stride=3),
            nn.Tanh(),
        )
        self.deconv3 = nn.Sequential(
            nn.ConvTranspose1d(in_channels=41, out_channels=2, kernel_size=3, stride=3),
            nn.Tanh(),
        )

    def smooth(self, x: torch.Tensor) -> torch.Tensor:
        n = self.filter_size
        x = F.pad(x, ((n - 1) // 2, (n - 1) // 2), mode="reflect")

        sigma = torch.exp(self.logsigma).unsqueeze(-1).unsqueeze(-1)
        sigma = sigma.repeat((1, 1, n))
        hw = 3 * sigma
        xx = torch.linspace(0, 1, steps=n, device=x.device).unsqueeze(0).unsqueeze(0)
        xx = xx.repeat((x.shape[1], 1, 1))
        xx = 2 * hw * xx - hw

        gauss = 1 / (2 * np.pi * sigma**2) * torch.exp(-1 / (2 * (sigma**2)) * xx**2)
        gauss_sum = gauss.sum(dim=2).unsqueeze(-1).repeat((1, 1, gauss.shape[-1]))
        gauss = gauss / gauss_sum
        return F.conv1d(x, gauss, groups=x.shape[1])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.linear(x)
        out = out.view(len(x), 60, 1)
        out = self.deconv1(out)
        out = self.deconv2(out)
        out = self.add_coords(out)
        out = self.deconv3(out)
        out = self.smooth(out)
        return out


def to_mag(real: np.ndarray, imag: np.ndarray) -> np.ndarray:
    return np.sqrt(real**2 + imag**2)


def to_db(mag: np.ndarray) -> np.ndarray:
    return 20.0 * np.log10(np.clip(mag, 1e-12, None))


@st.cache_data
def list_lhs_files(project_root: str) -> list[Path]:
    lhs = Path(project_root) / "data" / "LHS"
    return sorted(lhs.glob("input_trials_done_LHS_n20_rounded_seed*.csv"))


@st.cache_data
def load_lhs_seed(input_file: str) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, str]:
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
def load_old_excel(project_root: str) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    old = Path(project_root) / "old" / "data"
    x_df = pd.read_excel(old / "input_parameters.xlsx")[INPUT_COLUMNS]
    real = pd.read_excel(old / "reel.xlsx").values.astype(np.float32)
    imag = pd.read_excel(old / "imaginary.xlsx").values.astype(np.float32)
    n = min(len(x_df), len(real), len(imag))
    return x_df.iloc[:n].copy(), real[:n], imag[:n]


@st.cache_resource
def load_antenna_model_and_scaler(project_root: str, model_path: str, scaler_path: str):
    root = Path(project_root)
    scaler = joblib.load(root / scaler_path)
    model = AntennaNeuralNet()
    model.load_state_dict(torch.load(root / model_path, map_location="cpu"))
    model.eval()
    return model, scaler


@st.cache_resource
def load_tcnn_model_and_scaler(project_root: str, model_path: str, scaler_path: str, target_len: int):
    root = Path(project_root)
    scaler = joblib.load(root / scaler_path)
    model = TCNNHilbert(input_dim=len(INPUT_COLUMNS), target_len=target_len)
    model.load_state_dict(torch.load(root / model_path, map_location="cpu"))
    model.eval()
    return model, scaler


@st.cache_resource
def load_tcnn_model_and_scaler_with_type(
    project_root: str,
    model_path: str,
    scaler_path: str,
    target_len: int,
    model_type: str,
):
    root = Path(project_root)
    scaler = joblib.load(root / scaler_path)
    model = create_model(model_type, input_dim=len(INPUT_COLUMNS), target_len=target_len)
    model.load_state_dict(torch.load(root / model_path, map_location="cpu"))
    model.eval()
    return model, scaler


def main() -> None:
    st.set_page_config(page_title="LHS S11 Comparator", layout="wide")
    st.title("LHS Sample Comparator: Real vs Antenna NN vs Our NN")

    project_root = Path(__file__).resolve().parents[1]

    with st.sidebar:
        st.header("Settings")
        dataset = st.selectbox("Dataset", ["lhs", "old_excel"], index=0)
        trace_label = st.selectbox("Trace label", ["S11", "Sdd11"], index=0)
        magnitude_db = st.checkbox("Show magnitude in dB", value=True)

        antenna_model_path = st.text_input("Antenna model", value="NNModel/trained_model.pt")
        antenna_scaler_path = st.text_input("Antenna scaler", value="NNModel/scaler.gz")

        tcnn_model_path = st.text_input("Our model", value="NNModel/trained_model_tcnn_hilbert_oldexcel_db.pt")
        tcnn_scaler_path = st.text_input("Our scaler", value="NNModel/scaler_tcnn_hilbert_oldexcel_db.gz")
        tcnn_model_type = st.selectbox("Our model type", ["hilbert", "dual"], index=0)

    if dataset == "lhs":
        files = list_lhs_files(str(project_root))
        if not files:
            st.error("No LHS input files found in data/LHS")
            return
        file_labels = [f.name for f in files]
        selected_label = st.selectbox("Select LHS file", file_labels)
        selected_file = next(f for f in files if f.name == selected_label)
        x_df, real_all, imag_all, seed = load_lhs_seed(str(selected_file))
        seed_label = f"seed{seed}"
    else:
        x_df, real_all, imag_all = load_old_excel(str(project_root))
        seed_label = "old_excel"

    sample_idx = st.slider("Sample index", min_value=0, max_value=len(x_df) - 1, value=0, step=1)

    real_true = real_all[sample_idx]
    imag_true = imag_all[sample_idx]
    mag_true = to_mag(real_true, imag_true)

    antenna_model, antenna_scaler = load_antenna_model_and_scaler(
        str(project_root), antenna_model_path, antenna_scaler_path
    )
    tcnn_model, tcnn_scaler = load_tcnn_model_and_scaler_with_type(
        str(project_root),
        tcnn_model_path,
        tcnn_scaler_path,
        target_len=real_true.shape[0],
        model_type=tcnn_model_type,
    )

    x_one = x_df.iloc[[sample_idx]].values.astype(np.float32)
    x_ant = antenna_scaler.transform(x_one).astype(np.float32)
    x_tcnn = tcnn_scaler.transform(x_one).astype(np.float32)

    with torch.no_grad():
        ant_pred = antenna_model(torch.tensor(x_ant))
        tcnn_pred = tcnn_model(torch.tensor(x_tcnn))

    real_ant = ant_pred[0, 0, :].numpy()
    imag_ant = ant_pred[0, 1, :].numpy()
    mag_ant = to_mag(real_ant, imag_ant)

    real_tcnn = tcnn_pred[0, 0, :].numpy()
    imag_tcnn = tcnn_pred[0, 1, :].numpy()
    mag_tcnn = to_mag(real_tcnn, imag_tcnn)

    if magnitude_db:
        y_true = to_db(mag_true)
        y_ant = to_db(mag_ant)
        y_tcnn = to_db(mag_tcnn)
        y_label = f"|{trace_label}| (dB)"
    else:
        y_true = mag_true
        y_ant = mag_ant
        y_tcnn = mag_tcnn
        y_label = f"|{trace_label}|"

    mse_ant = float(np.mean((y_ant - y_true) ** 2))
    mse_tcnn = float(np.mean((y_tcnn - y_true) ** 2))

    col1, col2, col3 = st.columns(3)
    col1.metric("Dataset", seed_label)
    col2.metric("Antenna NN MSE", f"{mse_ant:.6f}")
    col3.metric("Our NN MSE", f"{mse_tcnn:.6f}")

    x_axis = np.arange(len(y_true))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_axis, y=y_true, mode="lines", name=f"Real {trace_label}", line=dict(width=3)))
    fig.add_trace(go.Scatter(x=x_axis, y=y_ant, mode="lines", name="Antenna NN", line=dict(width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=x_axis, y=y_tcnn, mode="lines", name="Our NN", line=dict(width=2, dash="dot")))
    fig.update_layout(
        title=f"{trace_label} comparison ({seed_label}, sample={sample_idx})",
        xaxis_title="Point index",
        yaxis_title=y_label,
        template="plotly_white",
        height=520,
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Selected geometry input"):
        st.dataframe(x_df.iloc[[sample_idx]], use_container_width=True)


if __name__ == "__main__":
    main()
