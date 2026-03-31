"""
compare_nsamples_app.py

Sample Size Comparison — AntennaNN vs ResUNet v9 (n=100/250/500/1000)

Compares all 8 models trained at different sample sizes side by side.

Run:
    python -m streamlit run updates/compare_nsamples_app.py
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
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter
from sklearn.exceptions import InconsistentVersionWarning

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.append(str(THIS_DIR))

from train_antenna_nn_nsamples import AntennaNeuralNet
from train_resunet_v9_nsamples import SmoothResUNet1D, INPUT_COLUMNS

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODELS = [
    {"name": "AntennaNN n=100",   "cls": "antenna", "model_path": "NNModel/trained_model_antenna_nn_n100.pt",   "scaler_path": "NNModel/scaler_antenna_nn_n100.gz",   "color": "#1565C0"},
    {"name": "AntennaNN n=250",   "cls": "antenna", "model_path": "NNModel/trained_model_antenna_nn_n250.pt",   "scaler_path": "NNModel/scaler_antenna_nn_n250.gz",   "color": "#1976D2"},
    {"name": "AntennaNN n=500",   "cls": "antenna", "model_path": "NNModel/trained_model_antenna_nn_n500.pt",   "scaler_path": "NNModel/scaler_antenna_nn_n500.gz",   "color": "#42A5F5"},
    {"name": "AntennaNN n=1000",  "cls": "antenna", "model_path": "NNModel/trained_model_antenna_nn_n1000.pt",  "scaler_path": "NNModel/scaler_antenna_nn_n1000.gz",  "color": "#90CAF9"},
    {"name": "ResUNet v9 n=100",  "cls": "smooth",  "model_path": "NNModel/trained_model_resunet_v9_n100.pt",  "scaler_path": "NNModel/scaler_resunet_v9_n100.gz",   "color": "#6A1B9A"},
    {"name": "ResUNet v9 n=250",  "cls": "smooth",  "model_path": "NNModel/trained_model_resunet_v9_n250.pt",  "scaler_path": "NNModel/scaler_resunet_v9_n250.gz",   "color": "#8E24AA"},
    {"name": "ResUNet v9 n=500",  "cls": "smooth",  "model_path": "NNModel/trained_model_resunet_v9_n500.pt",  "scaler_path": "NNModel/scaler_resunet_v9_n500.gz",   "color": "#AB47BC"},
    {"name": "ResUNet v9 n=1000", "cls": "smooth",  "model_path": "NNModel/trained_model_resunet_v9_n1000.pt", "scaler_path": "NNModel/scaler_resunet_v9_n1000.gz",  "color": "#CE93D8"},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_mag(real: np.ndarray, imag: np.ndarray) -> np.ndarray:
    return np.sqrt(real**2 + imag**2)


def to_db(mag: np.ndarray) -> np.ndarray:
    return 20.0 * np.log10(np.clip(mag, 1e-12, None))


def rse(pred: np.ndarray, true: np.ndarray, eps: float = 1e-6) -> float:
    return float(np.mean(((pred - true) ** 2) / (true**2 + eps)))


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
        return gaussian_filter1d(y, sigma=max(0.1, float(strength)), mode="reflect")
    return y


def rse_per_sample(pred: np.ndarray, true: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """RSE for each sample individually. pred/true shape: (N, L)"""
    return np.mean(((pred - true) ** 2) / (true**2 + eps), axis=1)


def mse_per_sample(pred: np.ndarray, true: np.ndarray) -> np.ndarray:
    return np.mean((pred - true) ** 2, axis=1)


# ---------------------------------------------------------------------------
# Cached loaders — NewData (primary test set)
# ---------------------------------------------------------------------------

@st.cache_data
def list_new_data_files() -> list[Path]:
    return sorted((PROJECT_ROOT / "NewData" / "inputs").glob("inputs_LHS_n50_seed*.csv"))


@st.cache_data
def load_new_data_seed(input_file: str):
    p    = Path(input_file)
    seed = p.stem.split("seed")[-1]
    x_df = pd.read_csv(p)[INPUT_COLUMNS]
    real = pd.read_csv(PROJECT_ROOT / "NewData" / "reals"     / f"real_LHS_n50_seed{seed}.csv").values.astype(np.float32)
    imag = pd.read_csv(PROJECT_ROOT / "NewData" / "imaginary" / f"imag_LHS_n50_seed{seed}.csv").values.astype(np.float32)
    n    = min(len(x_df), len(real), len(imag))
    return x_df.iloc[:n].copy(), real[:n], imag[:n], seed


@st.cache_data
def load_all_new_data():
    """Concatenate all 18 NewData seeds into a single dataset."""
    files = sorted((PROJECT_ROOT / "NewData" / "inputs").glob("inputs_LHS_n50_seed*.csv"))
    df_parts, x_parts, real_parts, imag_parts = [], [], [], []
    for p in files:
        seed = p.stem.split("seed")[-1]
        real_path = PROJECT_ROOT / "NewData" / "reals"     / f"real_LHS_n50_seed{seed}.csv"
        imag_path = PROJECT_ROOT / "NewData" / "imaginary" / f"imag_LHS_n50_seed{seed}.csv"
        if not (real_path.exists() and imag_path.exists()):
            continue
        x_df_s = pd.read_csv(p)[INPUT_COLUMNS]
        real   = pd.read_csv(real_path).values.astype(np.float32)
        imag   = pd.read_csv(imag_path).values.astype(np.float32)
        n = min(len(x_df_s), len(real), len(imag))
        df_parts.append(x_df_s.iloc[:n])
        x_parts.append(x_df_s.values[:n].astype(np.float32))
        real_parts.append(real[:n])
        imag_parts.append(imag[:n])
    if not x_parts:
        return None, None, None, None
    return (
        pd.concat(df_parts, ignore_index=True),
        np.concatenate(x_parts,    axis=0),
        np.concatenate(real_parts, axis=0),
        np.concatenate(imag_parts, axis=0),
    )


# ---------------------------------------------------------------------------
# Cached loaders — Old LHS (data/LHS/)
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
def load_all_lhs():
    """Concatenate all LHS seeds into a single dataset. Returns (x_df, x_np, real, imag)."""
    files = sorted((PROJECT_ROOT / "data" / "LHS").glob("input_trials_done_LHS_n20_rounded_seed*.csv"))
    df_parts, x_parts, real_parts, imag_parts = [], [], [], []
    for p in files:
        seed = p.stem.split("seed")[-1]
        lhs  = p.parent
        real_path = lhs / f"real_initial_LHS_n20_rounded_seed{seed}.csv"
        imag_path = lhs / f"imag_initial_LHS_n20_rounded_seed{seed}.csv"
        if not (real_path.exists() and imag_path.exists()):
            continue
        x_df_s = pd.read_csv(p)[INPUT_COLUMNS]
        real   = pd.read_csv(real_path).values.astype(np.float32)
        imag   = pd.read_csv(imag_path).values.astype(np.float32)
        n = min(len(x_df_s), len(real), len(imag))
        df_parts.append(x_df_s.iloc[:n])
        x_parts.append(x_df_s.values[:n].astype(np.float32))
        real_parts.append(real[:n])
        imag_parts.append(imag[:n])
    if not x_parts:
        return None, None, None, None
    return (
        pd.concat(df_parts, ignore_index=True),
        np.concatenate(x_parts,    axis=0),
        np.concatenate(real_parts, axis=0),
        np.concatenate(imag_parts, axis=0),
    )


@st.cache_data
def load_old_excel():
    old  = PROJECT_ROOT / "old" / "data"
    x_df = pd.read_excel(old / "input_parameters.xlsx")[INPUT_COLUMNS]
    real = pd.read_excel(old / "reel.xlsx").values.astype(np.float32)
    imag = pd.read_excel(old / "imaginary.xlsx").values.astype(np.float32)
    n = min(len(x_df), len(real), len(imag))
    return x_df.iloc[:n].copy(), real[:n], imag[:n]


# ---------------------------------------------------------------------------
# Cached model loader
# ---------------------------------------------------------------------------

@st.cache_resource
def load_model(model_path: str, scaler_path: str, model_cls: str, target_len: int):
    scaler = joblib.load(PROJECT_ROOT / scaler_path)
    if model_cls == "antenna":
        model = AntennaNeuralNet()
    else:  # smooth
        model = SmoothResUNet1D(input_dim=len(INPUT_COLUMNS), target_len=target_len)
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
# Dataset statistics (cached)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Computing dataset statistics...")
def compute_dataset_stats(
    x_all: np.ndarray,
    real_all: np.ndarray,
    imag_all: np.ndarray,
    model_name: str,
    model_path: str,
    scaler_path: str,
    model_cls: str,
    target_len: int,
    smooth_method: str,
    smooth_strength: float,
    smooth_window: int,
    smooth_poly: int,
) -> dict:
    """Run inference on full dataset, apply smoothing, return per-sample MSE and RSE."""
    try:
        scaler = joblib.load(PROJECT_ROOT / scaler_path)
        if model_cls == "antenna":
            m = AntennaNeuralNet()
        else:
            m = SmoothResUNet1D(input_dim=len(INPUT_COLUMNS), target_len=target_len)
        m.load_state_dict(torch.load(PROJECT_ROOT / model_path, map_location="cpu"))
        m.eval()

        x_scaled = scaler.transform(x_all).astype(np.float32)
        with torch.no_grad():
            out = m(torch.tensor(x_scaled)).numpy()  # (N, 2, L)

        mag_true = to_mag(real_all, imag_all)
        db_true  = to_db(mag_true)

        mag_preds, db_preds = [], []
        for i in range(out.shape[0]):
            r  = out[i, 0, :]
            im = out[i, 1, :]
            mag = to_mag(r, im)
            db  = to_db(mag)
            if smooth_method != "none":
                db  = smooth_1d(db, smooth_method, smooth_strength, smooth_window, smooth_poly)
                mag = 10 ** (db / 20.0)
            mag_preds.append(mag)
            db_preds.append(db)

        mag_preds = np.array(mag_preds)
        db_preds  = np.array(db_preds)

        return {
            "rse":    rse_per_sample(mag_preds, mag_true),
            "rse_db": rse_per_sample(db_preds,  db_true),
            "mse":    mse_per_sample(db_preds,  db_true),
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="Sample Size Comparison", layout="wide")
    st.title("Sample Size Comparison — AntennaNN vs ResUNet v9 (n=100/250/500/1000)")

    # ---- Sidebar ----
    with st.sidebar:
        st.header("Controls")
        dataset      = st.selectbox("Dataset", ["new_data", "lhs", "old_excel"], index=0)
        trace_label  = st.selectbox("Trace label", ["S11", "Sdd11"], index=0)
        magnitude_db = st.checkbox("Show magnitude in dB", value=True)

        st.subheader("Post-smoothing")
        apply_smoothing = st.checkbox("Apply smoothing to model outputs", value=False)
        smooth_method   = st.selectbox("Method", ["none", "gaussian", "savgol", "moving_average"],
                                       index=1, disabled=not apply_smoothing)
        smooth_strength = st.slider("Gaussian sigma", 0.1, 6.0, 1.5, 0.1,
                                    disabled=(not apply_smoothing or smooth_method != "gaussian"))
        smooth_window   = st.slider("Window length", 5, 51, 11, 2,
                                    disabled=(not apply_smoothing or smooth_method == "gaussian"))
        smooth_poly     = st.slider("SavGol polyorder", 2, 5, 3, 1,
                                    disabled=(not apply_smoothing or smooth_method != "savgol"))
        _method = smooth_method if apply_smoothing else "none"
        _str    = smooth_strength
        _win    = smooth_window
        _poly   = smooth_poly

        st.subheader("Model path overrides")
        model_overrides = {}
        for cfg in MODELS:
            with st.expander(cfg["name"], expanded=False):
                mp = st.text_input(f"Model path ({cfg['name']})",  value=cfg["model_path"],  key=f"mp_{cfg['name']}")
                sp = st.text_input(f"Scaler path ({cfg['name']})", value=cfg["scaler_path"], key=f"sp_{cfg['name']}")
                model_overrides[cfg["name"]] = {"model_path": mp, "scaler_path": sp}

    # ---- Load data ----
    if dataset == "new_data":
        files = list_new_data_files()
        if not files:
            st.error("No NewData files found in NewData/inputs/"); return
        aggregate_all = st.checkbox("Aggregate all NewData seeds", value=True)
        if aggregate_all:
            df_agg, x_agg, real_agg, imag_agg = load_all_new_data()
            if x_agg is not None:
                x_df          = df_agg
                real_all      = real_agg
                imag_all      = imag_agg
                dataset_label = "new_data_all_seeds"
            else:
                st.error("Could not load NewData."); return
        else:
            selected_file = st.selectbox("NewData seed file", [f.name for f in files])
            fpath = next(f for f in files if f.name == selected_file)
            x_df, real_all, imag_all, seed = load_new_data_seed(str(fpath))
            dataset_label = f"new_data_seed{seed}"
    elif dataset == "lhs":
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

    real_true  = real_all[idx]
    imag_true  = imag_all[idx]
    x_row      = x_df.iloc[idx].values.astype(np.float32)
    target_len = real_true.shape[0]

    # ---- Load all 8 models ----
    loaded_models = {}
    for cfg in MODELS:
        name = cfg["name"]
        mp   = model_overrides[name]["model_path"]
        sp   = model_overrides[name]["scaler_path"]
        cls  = cfg["cls"]
        try:
            m, sc = load_model(mp, sp, cls, target_len)
            loaded_models[name] = (m, sc)
        except Exception as e:
            st.warning(f"{name}: could not load model from {mp} — {e}")
            loaded_models[name] = (None, None)

    # ---- Predictions for selected sample ----
    def get_curve(name):
        m, sc = loaded_models[name]
        if m is None:
            return None, None
        return predict(m, sc, x_row)

    curves = {cfg["name"]: get_curve(cfg["name"]) for cfg in MODELS}

    # ---- Convert to display space ----
    def display(real, imag):
        if real is None:
            return None
        mag = to_mag(real, imag)
        return to_db(mag) if magnitude_db else mag

    def smooth_curve(y):
        if y is None:
            return None
        return smooth_1d(y, _method, _str, _win, _poly)

    y_true  = display(real_true, imag_true)
    y_label = f"|{trace_label}| (dB)" if magnitude_db else f"|{trace_label}|"

    y_preds = {}
    for cfg in MODELS:
        r, i = curves[cfg["name"]]
        y_preds[cfg["name"]] = smooth_curve(display(r, i))

    # ---- Metrics ----
    mag_true_sample = to_mag(real_true, imag_true)
    db_true_sample  = to_db(mag_true_sample)

    def metrics_for(name):
        r, i = curves[name]
        if r is None:
            return {}
        mag_p = to_mag(r, i)
        db_p  = to_db(mag_p)
        if _method != "none":
            db_p  = smooth_1d(db_p, _method, _str, _win, _poly)
            mag_p = 10 ** (db_p / 20.0)
        mse_val    = float(np.mean((db_p - db_true_sample) ** 2))
        rse_mag    = float(np.mean(((mag_p - mag_true_sample) ** 2) / (mag_true_sample ** 2 + 1e-6)))
        rse_db_val = float(np.mean(((db_p  - db_true_sample)  ** 2) / (db_true_sample  ** 2 + 1e-6)))
        return {"mse": mse_val, "rse_mag": rse_mag, "rse_db": rse_db_val}

    all_metrics = {cfg["name"]: metrics_for(cfg["name"]) for cfg in MODELS}

    # ---- Metrics grid: 3 rows × 9 cols ----
    n_cols = 1 + len(MODELS)
    row1 = st.columns(n_cols)
    row2 = st.columns(n_cols)
    row3 = st.columns(n_cols)
    row1[0].metric("Dataset", dataset_label)
    row2[0].metric("Sample",  idx)
    row3[0].metric("Metric", "RSE (dB)", label_visibility="hidden")
    for col_i, cfg in enumerate(MODELS):
        name = cfg["name"]
        m    = all_metrics[name]
        row1[col_i + 1].metric(f"{name} MSE",      f"{m['mse']:.6f}"     if m else "—")
        row2[col_i + 1].metric(f"{name} RSE(mag)",  f"{m['rse_mag']:.6f}" if m else "—")
        row3[col_i + 1].metric(f"{name} RSE(dB)",   f"{m['rse_db']:.6f}"  if m else "—")

    # ---- Plot ----
    x_axis = np.arange(len(y_true))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_axis, y=y_true, mode="lines",
        name=f"Real {trace_label}",
        line=dict(width=3, color="gold"),
    ))
    for cfg in MODELS:
        name = cfg["name"]
        y_p  = y_preds[name]
        if y_p is not None:
            fig.add_trace(go.Scatter(
                x=x_axis, y=y_p, mode="lines",
                name=name,
                line=dict(width=2, dash="dash", color=cfg["color"]),
            ))

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

    # ---- Dataset-wide statistics ----
    st.subheader("Dataset statistics (all samples)")
    st.caption("Runs inference on the full dataset. First load may take a moment.")

    if dataset == "new_data":
        df_agg2, x_agg2, real_agg2, imag_agg2 = load_all_new_data()
        if x_agg2 is not None:
            x_df_stat   = df_agg2
            x_all_np    = x_agg2
            real_all_np = real_agg2
            imag_all_np = imag_agg2
        else:
            x_df_stat   = x_df
            x_all_np    = x_df.values.astype(np.float32)
            real_all_np = real_all
            imag_all_np = imag_all
    elif dataset == "lhs":
        aggregate_all_lhs = st.checkbox("Aggregate all LHS seeds for stats", value=True)
        if aggregate_all_lhs:
            df_agg2, x_agg2, real_agg2, imag_agg2 = load_all_lhs()
            if x_agg2 is not None:
                x_df_stat   = df_agg2
                x_all_np    = x_agg2
                real_all_np = real_agg2
                imag_all_np = imag_agg2
            else:
                st.warning("Could not load all LHS seeds.")
                x_df_stat   = x_df
                x_all_np    = x_df.values.astype(np.float32)
                real_all_np = real_all
                imag_all_np = imag_all
        else:
            x_df_stat   = x_df
            x_all_np    = x_df.values.astype(np.float32)
            real_all_np = real_all
            imag_all_np = imag_all
    else:
        x_df_stat   = x_df
        x_all_np    = x_df.values.astype(np.float32)
        real_all_np = real_all
        imag_all_np = imag_all

    all_stats = {}
    for cfg in MODELS:
        name = cfg["name"]
        mp   = model_overrides[name]["model_path"]
        sp   = model_overrides[name]["scaler_path"]
        cls  = cfg["cls"]
        if not (PROJECT_ROOT / mp).exists():
            continue
        stats = compute_dataset_stats(
            x_all_np, real_all_np, imag_all_np,
            model_name=name,
            model_path=mp,
            scaler_path=sp,
            model_cls=cls,
            target_len=int(real_all_np.shape[1]),
            smooth_method=_method,
            smooth_strength=_str,
            smooth_window=_win,
            smooth_poly=_poly,
        )
        if stats and "error" not in stats:
            all_stats[name] = stats
        elif stats and "error" in stats:
            st.warning(f"{name} stats error: {stats['error']}")

    if all_stats:
        percentiles = [0, 25, 50, 75, 100]

        # --- RSE table ---
        rse_metric = st.radio(
            "RSE metric", ["magnitude (mag)", "dB"],
            horizontal=True, key="rse_metric_radio",
        )
        rse_key   = "rse"    if rse_metric == "magnitude (mag)" else "rse_db"
        rse_label = "RSE (magnitude)" if rse_metric == "magnitude (mag)" else "RSE (dB)"
        st.markdown(f"**{rse_label} across dataset** (lower is better)")
        rse_rows = []
        for name, stats in all_stats.items():
            arr = stats[rse_key]
            row = {"Model": name, "Mean": float(np.mean(arr))}
            for p in percentiles:
                row[f"p{p}"] = float(np.percentile(arr, p))
            rse_rows.append(row)
        rse_df = pd.DataFrame(rse_rows).set_index("Model")
        st.dataframe(rse_df.style.format("{:.5f}"), use_container_width=True)

        # --- MSE table ---
        st.markdown("**MSE (dB) across dataset**")
        mse_rows = []
        for name, stats in all_stats.items():
            arr = stats["mse"]
            row = {"Model": name, "Mean": float(np.mean(arr))}
            for p in percentiles:
                row[f"p{p}"] = float(np.percentile(arr, p))
            mse_rows.append(row)
        mse_df = pd.DataFrame(mse_rows).set_index("Model")
        st.dataframe(mse_df.style.format("{:.5f}"), use_container_width=True)

        # --- Boxplot (RSE) ---
        st.markdown(f"**{rse_label} distribution — boxplot**")
        fig3 = go.Figure()
        for cfg in MODELS:
            name = cfg["name"]
            if name not in all_stats:
                continue
            fig3.add_trace(go.Box(
                y=all_stats[name][rse_key],
                name=name,
                marker_color=cfg["color"],
                boxmean=True,
            ))
        fig3.update_layout(
            yaxis_title=rse_label,
            template="plotly_white",
            height=400,
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("Box = 25-75th percentile  |  Line = median  |  X = mean  |  Whiskers = min/max")

        # --- Worst samples inspector ---
        st.markdown("---")
        st.markdown("**Worst samples inspector**")
        st.caption("Sort all dataset samples by RSE for a chosen model.")
        col_ws1, col_ws2 = st.columns([2, 1])
        with col_ws1:
            worst_model = st.selectbox("Sort by model (RSE magnitude)", list(all_stats.keys()), key="worst_model")
        with col_ws2:
            top_n = st.slider("Top-N worst", 1, 20, 5, key="top_n")

        worst_rse = all_stats[worst_model]["rse"]
        worst_idx = np.argsort(worst_rse)[::-1][:top_n]

        rows = []
        for rank, si in enumerate(worst_idx):
            row = {"Rank": rank + 1, "Sample idx": int(si)}
            for mname, st_data in all_stats.items():
                row[f"RSE (mag) ({mname})"] = float(st_data["rse"][si])
            geom = x_df_stat.iloc[int(si)].to_dict()
            row.update(geom)
            rows.append(row)
        worst_df = pd.DataFrame(rows).set_index("Rank")
        rse_cols  = [c for c in worst_df.columns if c.startswith("RSE (mag)")]
        geom_cols = [c for c in worst_df.columns if c not in rse_cols and c != "Sample idx"]
        st.dataframe(
            worst_df.style.format(
                {c: "{:.5f}" for c in rse_cols} | {c: "{:.4g}" for c in geom_cols}
            ),
            use_container_width=True,
        )

        # Plot: overlay worst samples for ground truth + chosen model
        with st.expander(f"Plot worst {top_n} samples — ground truth vs {worst_model}"):
            colors_worst = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db",
                            "#9b59b6", "#1abc9c", "#e91e63", "#ff5722", "#607d8b"]
            fig_w = go.Figure()
            worst_model_cfg = next((c for c in MODELS if c["name"] == worst_model), None)
            wm_obj, wm_scaler = loaded_models.get(worst_model, (None, None))
            for rank, si in enumerate(worst_idx):
                color = colors_worst[rank % len(colors_worst)]
                si = int(si)
                y_gt = display(real_all_np[si], imag_all_np[si])
                fig_w.add_trace(go.Scatter(
                    x=x_axis, y=y_gt, mode="lines",
                    name=f"#{si} GT",
                    line=dict(color=color, width=2),
                    legendgroup=str(si),
                ))
                if wm_obj is not None:
                    x_row_si = x_df_stat.iloc[si].values.astype(np.float32)
                    r_p, i_p = predict(wm_obj, wm_scaler, x_row_si)
                    y_p      = smooth_curve(display(r_p, i_p))
                    rse_val  = worst_rse[si]
                    fig_w.add_trace(go.Scatter(
                        x=x_axis, y=y_p, mode="lines",
                        name=f"#{si} pred (RSE={rse_val:.4f})",
                        line=dict(color=color, width=1.5, dash="dash"),
                        legendgroup=str(si),
                    ))
            fig_w.update_layout(
                xaxis_title="Frequency point index",
                yaxis_title=y_label,
                template="plotly_white",
                height=500,
                legend=dict(orientation="v"),
            )
            st.plotly_chart(fig_w, use_container_width=True)

    # ---- Training curves ----
    st.subheader("Training curves (train vs val loss)")

    history_files = {}
    for cfg in MODELS:
        name = cfg["name"]
        # Derive history CSV name from model_path: replace model file pattern
        mp   = model_overrides[name]["model_path"]
        # e.g. NNModel/trained_model_antenna_nn_n100.pt -> NNModel/history_antenna_nn_n100.csv
        mp_stem = Path(mp).stem  # e.g. trained_model_antenna_nn_n100
        if mp_stem.startswith("trained_model_"):
            hist_stem = "history_" + mp_stem[len("trained_model_"):]
        else:
            hist_stem = "history_" + mp_stem
        hist_path = PROJECT_ROOT / Path(mp).parent / (hist_stem + ".csv")
        history_files[name] = hist_path

    available = {name: path for name, path in history_files.items() if path.exists()}
    if not available:
        st.info("No history CSV files found. Train the models first.")
    else:
        selected_histories = st.multiselect(
            "Show training curves for:",
            options=list(available.keys()),
            default=list(available.keys()),
        )

        color_map = {cfg["name"]: cfg["color"] for cfg in MODELS}
        fig2 = go.Figure()

        for name in selected_histories:
            df_h  = pd.read_csv(available[name])
            color = color_map.get(name, "gray")
            fig2.add_trace(go.Scatter(
                x=df_h["epoch"], y=df_h["train_loss"],
                mode="lines", name=f"{name} train",
                line=dict(color=color, width=2),
            ))
            fig2.add_trace(go.Scatter(
                x=df_h["epoch"], y=df_h["val_loss"],
                mode="lines", name=f"{name} val",
                line=dict(color=color, width=2, dash="dash"),
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
