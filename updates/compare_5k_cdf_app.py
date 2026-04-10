"""
compare_5k_cdf_app.py  —  Streamlit comparison dashboard

Compares the two BASE models (each trained on the full 5 000-sample dataset):
  • AntennaNN  (MLP + deconv, ~70 k params)
  • ResUNet v9 (SmoothResUNet1D, ~3 M params)

Evaluation on NewData / LHS held-out test set.
Shows boxplots of per-sample errors for 3 metrics.

Run:
    python -m streamlit run updates/compare_5k_cdf_app.py
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

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

THIS_DIR = Path(__file__).resolve().parent
PROJECT  = THIS_DIR.parent
NN_DIR   = PROJECT / "NNModel"
NEWDATA  = PROJECT / "NewData"

if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from compare_antenna_vs_tcnn_sdd11 import AntennaNeuralNet
from train_resunet_big_v2 import SmoothResUNet1D, INPUT_COLUMNS

TARGET_LEN = 201

COLORS = {
    "AntennaNN":  "#1565C0",
    "ResUNet":    "#7B1FA2",
}

METRICS = [
    ("rse_mag", "RSE — Magnitude"),
    ("rse_db",  "RSE — dB"),
    ("mse_db",  "MSE — dB"),
]

TEMPLATE = "plotly_white"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_mag(r, i):
    return np.sqrt(r ** 2 + i ** 2)

def to_db(m):
    return 20.0 * np.log10(np.clip(m, 1e-12, None))

def rse_per(pred, true, eps=1e-6):
    return np.mean((pred - true) ** 2 / (true ** 2 + eps), axis=1)

def mse_per(pred, true):
    return np.mean((pred - true) ** 2, axis=1)

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading NewData/LHS…")
def load_new_data():
    x_list, r_list, i_list = [], [], []
    for p in sorted((NEWDATA / "inputs").glob("inputs_LHS_n50_seed*.csv")):
        seed = p.stem.split("seed")[-1]
        rp   = NEWDATA / "reals"     / f"real_LHS_n50_seed{seed}.csv"
        ip   = NEWDATA / "imaginary" / f"imag_LHS_n50_seed{seed}.csv"
        if not (rp.exists() and ip.exists()):
            continue
        x    = pd.read_csv(p)[INPUT_COLUMNS].values.astype(np.float32)
        real = pd.read_csv(rp).values.astype(np.float32)
        imag = pd.read_csv(ip).values.astype(np.float32)
        n    = min(len(x), len(real), len(imag))
        x_list.append(x[:n]); r_list.append(real[:n]); i_list.append(imag[:n])
    if not x_list:
        return np.empty((0, len(INPUT_COLUMNS))), np.empty((0, TARGET_LEN)), np.empty((0, TARGET_LEN))
    return np.concatenate(x_list), np.concatenate(r_list), np.concatenate(i_list)


@st.cache_resource(show_spinner="Loading AntennaNN…")
def load_antenna_nn():
    scaler = joblib.load(NN_DIR / "scaler.gz")
    m = AntennaNeuralNet()
    m.load_state_dict(torch.load(NN_DIR / "trained_model.pt", map_location="cpu"))
    m.eval()
    return m, scaler


@st.cache_resource(show_spinner="Loading ResUNet v9…")
def load_resunet_v9():
    scaler = joblib.load(NN_DIR / "scaler_resunet_v9.gz")
    m = SmoothResUNet1D(input_dim=len(INPUT_COLUMNS), target_len=TARGET_LEN)
    m.load_state_dict(torch.load(NN_DIR / "trained_model_resunet_v9.pt", map_location="cpu"))
    m.eval()
    return m, scaler


def run_inference(model, scaler, x: np.ndarray):
    x_sc = scaler.transform(x).astype(np.float32)
    with torch.no_grad():
        out = model(torch.tensor(x_sc)).numpy()
    return out[:, 0, :], out[:, 1, :]


@st.cache_data(show_spinner="Running inference…")
def compute_errors(_ann_model, _ann_scaler, _v9_model, _v9_scaler,
                   x_all, real_all, imag_all):
    mag_true = to_mag(real_all, imag_all)
    db_true  = to_db(mag_true)
    errors = {}
    for label, model, scaler in [
        ("AntennaNN",  _ann_model, _ann_scaler),
        ("ResUNet", _v9_model,  _v9_scaler),
    ]:
        rp, ip   = run_inference(model, scaler, x_all)
        mag_pred = to_mag(rp, ip)
        db_pred  = to_db(mag_pred)
        errors[label] = {
            "rse_mag": rse_per(mag_pred, mag_true),
            "rse_db":  rse_per(db_pred,  db_true),
            "mse_db":  mse_per(db_pred,  db_true),
        }
    return errors

# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

def chart_boxplots(errors: dict) -> go.Figure:
    """Horizontal boxplot — RSE Magnitude only, one box per model.
    The 2 largest AntennaNN values are excluded from the plot to keep scaling sensible.
    """
    fig = go.Figure()

    for model_name, color in COLORS.items():
        vals = np.sort(errors[model_name]["rse_mag"])
        # Drop the 2 biggest outliers only for AntennaNN
        if model_name == "AntennaNN":
            vals = vals[:-2]

        q1, med, q3 = (float(np.percentile(vals, p)) for p in [25, 50, 75])
        iqr  = q3 - q1
        lo   = float(max(vals.min(), q1 - 1.5 * iqr))
        hi   = float(min(vals.max(), q3 + 1.5 * iqr))
        mean = float(np.mean(vals))

        # Box with explicit fences so it always renders
        fig.add_trace(go.Box(
            x=vals,
            name=model_name,
            orientation="h",
            # explicit pre-computed stats
            lowerfence=[lo],
            q1=[q1],
            median=[med],
            mean=[mean],
            q3=[q3],
            upperfence=[hi],
            boxmean="sd",
            boxpoints="all",
            jitter=0.5,
            pointpos=0,
            marker=dict(
                color=color,
                size=6,
                opacity=0.55,
                line=dict(width=0.8, color="white"),
            ),
            line=dict(color=color, width=2.5),
            fillcolor=color,
            opacity=0.45,
        ))

    fig.update_layout(
        xaxis=dict(
            title="RSE — Magnitude  (lower is better)",
            title_font=dict(size=14, color="black"),
            tickfont=dict(size=13, color="black"),
        ),
        yaxis=dict(
            tickfont=dict(size=14, color="black"),
        ),
        boxmode="group",
        height=360,
        template=TEMPLATE,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.04,
            xanchor="left", x=0,
            font=dict(size=14, color="black"),
        ),
        margin=dict(t=60, b=50, l=20, r=20),
        font=dict(size=13, color="black"),
    )
    return fig

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

st.set_page_config(page_title="5k Model Comparison", layout="wide")
st.title("AntennaNN vs ResUNet — Base Models (5 000 samples)")
st.caption(
    "Evaluation on NewData / LHS held-out test set.  "
    "Box = 25th–75th percentile  ·  Line = median  ·  X = mean  ·  Dots = individual samples."
)

x_all, real_all, imag_all = load_new_data()

if len(x_all) == 0:
    st.error("No NewData/LHS samples found. Check the NewData/ directory.")
    st.stop()

ann_model, ann_scaler = load_antenna_nn()
v9_model,  v9_scaler  = load_resunet_v9()

errors = compute_errors(
    ann_model, ann_scaler,
    v9_model,  v9_scaler,
    x_all, real_all, imag_all,
)

st.plotly_chart(chart_boxplots(errors), use_container_width=True)

# Summary numbers below the chart
st.subheader("RSE Magnitude summary")
rows = []
for model_name in ("AntennaNN", "ResUNet"):
    v = errors[model_name]["rse_mag"]
    rows.append({
        "Model":  model_name,
        "Mean":   float(np.mean(v)),
        "Median": float(np.median(v)),
        "Std":    float(np.std(v, ddof=1)),
        "p75":    float(np.percentile(v, 75)),
        "p90":    float(np.percentile(v, 90)),
    })

df = pd.DataFrame(rows).set_index("Model")
fmt = {c: "{:.5f}" for c in df.columns}
st.dataframe(
    df.style.format(fmt).highlight_min(axis=0, color="#c8e6c9"),
    use_container_width=True,
)
st.caption("Green = lower (better) value per column.")
