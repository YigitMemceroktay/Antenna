"""
compare_v9_vs_oldnn.py  —  Streamlit app

Compares Big v9 (SmoothResUNet1D) vs the original Antenna NN
across sample sizes: 100, 250, 500, 1000.

Run:
    python -m streamlit run updates/compare_v9_vs_oldnn.py
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
from plotly.subplots import make_subplots
from sklearn.exceptions import InconsistentVersionWarning

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

THIS_DIR = Path(__file__).resolve().parent
PROJECT  = THIS_DIR.parent
NN_DIR   = PROJECT / "NNModel"
NEWDATA  = PROJECT / "NewData"

if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from compare_antenna_vs_tcnn_sdd11 import AntennaNeuralNet
from train_resunet_big import BigResUNet1D, INPUT_COLUMNS
from train_resunet_big_v2 import SmoothResUNet1D

TARGET_LEN   = 201
SAMPLE_SIZES = [100, 250, 500, 1000]
SEED         = 42

COLORS = {"Old NN": "#4C72B0", "Big v9": "#DD8452"}
METRICS = [
    ("rse_mag", "RSE — Magnitude", "Lower is better"),
    ("rse_db",  "RSE — dB",        "Lower is better"),
    ("mse_db",  "MSE — dB",        "Lower is better"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_mag(r, i):  return np.sqrt(r**2 + i**2)
def to_db(m):      return 20.0 * np.log10(np.clip(m, 1e-12, None))

def rse_per(pred, true, eps=1e-6):
    return np.mean(((pred - true)**2) / (true**2 + eps), axis=1)

def mse_per(pred, true):
    return np.mean((pred - true)**2, axis=1)

# ---------------------------------------------------------------------------
# Cached loaders
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading NewData…")
def load_all_new_data():
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
    return np.concatenate(x_list), np.concatenate(r_list), np.concatenate(i_list)


@st.cache_resource(show_spinner="Loading Old NN…")
def load_old_nn():
    scaler = joblib.load(NN_DIR / "scaler.gz")
    m = AntennaNeuralNet()
    m.load_state_dict(torch.load(NN_DIR / "trained_model.pt", map_location="cpu"))
    m.eval()
    return m, scaler


@st.cache_resource(show_spinner="Loading Big v9…")
def load_v9():
    scaler = joblib.load(NN_DIR / "scaler_resunet_v9.gz")
    m = SmoothResUNet1D(input_dim=len(INPUT_COLUMNS), target_len=TARGET_LEN)
    m.load_state_dict(torch.load(NN_DIR / "trained_model_resunet_v9.pt", map_location="cpu"))
    m.eval()
    return m, scaler


def run_inference(model, scaler, x):
    x_sc = scaler.transform(x).astype(np.float32)
    with torch.no_grad():
        out = model(torch.tensor(x_sc)).numpy()
    return out[:, 0, :], out[:, 1, :]


@st.cache_data(show_spinner="Running inference…")
def compute_all_results(_old_model, _old_scaler, _v9_model, _v9_scaler,
                        x_all, real_all, imag_all):
    rng = np.random.default_rng(SEED)
    results = {}
    for n in SAMPLE_SIZES:
        available = len(x_all)
        replace   = n > available
        idx       = rng.choice(available, size=n, replace=replace)
        x_s  = x_all[idx];   r_s = real_all[idx];  i_s = imag_all[idx]

        mag_t = to_mag(r_s, i_s);  db_t = to_db(mag_t)

        for model_name, model, scaler in [
            ("Old NN", _old_model, _old_scaler),
            ("Big v9", _v9_model,  _v9_scaler),
        ]:
            rp, ip   = run_inference(model, scaler, x_s)
            mag_p    = to_mag(rp, ip);  db_p = to_db(mag_p)
            results[(model_name, n)] = {
                "rse_mag": rse_per(mag_p, mag_t),
                "rse_db":  rse_per(db_p,  db_t),
                "mse_db":  mse_per(db_p,  db_t),
            }
    return results

# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

st.set_page_config(page_title="v9 vs Old NN", layout="wide")
st.title("Big v9 vs Old Antenna NN — Sample Size Comparison")
st.caption("NewData test set (900 samples, 18 seeds x 50). "
           "n=1000 uses sampling with replacement.")

# Load everything
x_all, real_all, imag_all = load_all_new_data()
old_model, old_scaler     = load_old_nn()
v9_model,  v9_scaler      = load_v9()

st.info(f"Dataset loaded: **{len(x_all)} samples** available in NewData.")

results = compute_all_results(
    old_model, old_scaler, v9_model, v9_scaler,
    x_all, real_all, imag_all,
)

# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

st.subheader("Mean Metrics Summary")

rows = []
for n in SAMPLE_SIZES:
    for model_name in ("Old NN", "Big v9"):
        d = results[(model_name, n)]
        rows.append({
            "Model":     model_name,
            "n":         n,
            "RSE Mag":   round(float(d["rse_mag"].mean()), 5),
            "RSE dB":    round(float(d["rse_db"].mean()),  5),
            "MSE dB":    round(float(d["mse_db"].mean()),  5),
        })

summary_df = pd.DataFrame(rows)

def color_winner(df):
    styled = df.copy().astype(str)
    for n in SAMPLE_SIZES:
        for col in ["RSE Mag", "RSE dB", "MSE dB"]:
            vals = df[df["n"] == n][col].values
            min_idx = df[(df["n"] == n)].index[np.argmin(vals)]
            styled.loc[min_idx, col] = f"**{df.loc[min_idx, col]}**"
    return styled

st.dataframe(
    summary_df.style
        .highlight_min(subset=["RSE Mag", "RSE dB", "MSE dB"],
                       axis=0, color="#c6efce")
        .format({"RSE Mag": "{:.5f}", "RSE dB": "{:.5f}", "MSE dB": "{:.5f}"}),
    use_container_width=True,
    height=200,
)

# ---------------------------------------------------------------------------
# Box plots — one section per metric, 4 rows (one per sample size)
# ---------------------------------------------------------------------------

st.subheader("Per-sample Error Distributions")
st.markdown("One row per sample size. **Big v9** on top, **Old NN** below. "
            "Whiskers = min/max (0th–100th pct). Box = 25th–75th. Line = median.")

def pct_box(data, model_name, show_legend, row):
    """Return a go.Box trace using explicit 0/25/50/75/100 percentile fences."""
    p0, p25, p50, p75, p100 = (
        float(np.percentile(data, q)) for q in [0, 25, 50, 75, 100]
    )
    return go.Box(
        lowerfence=[p0],
        q1=[p25],
        median=[p50],
        q3=[p75],
        upperfence=[p100],
        mean=[float(np.mean(data))],
        name=model_name,
        orientation="h",
        marker_color=COLORS[model_name],
        boxmean=True,
        legendgroup=model_name,
        showlegend=show_legend,
        line=dict(width=2),
        fillcolor=COLORS[model_name],
        opacity=0.80,
    ), (p0, p25, p50, p75, p100)


for metric_key, metric_label, metric_hint in METRICS:
    st.markdown(f"#### {metric_label}  <small style='color:gray'>({metric_hint})</small>",
                unsafe_allow_html=True)

    fig = make_subplots(
        rows=len(SAMPLE_SIZES), cols=1,
        subplot_titles=[f"n = {n}" for n in SAMPLE_SIZES],
        shared_xaxes=False,
        vertical_spacing=0.08,
    )

    for row_idx, n in enumerate(SAMPLE_SIZES, start=1):
        for model_name in ["Big v9", "Old NN"]:
            data  = results[(model_name, n)][metric_key]
            trace, (p0, p25, p50, p75, p100) = pct_box(
                data, model_name,
                show_legend=(row_idx == 1),
                row=row_idx,
            )
            fig.add_trace(trace, row=row_idx, col=1)

            # Percentile value annotations above each box
            y_offset = 0.38 if model_name == "Big v9" else -0.38
            for pct_val, pct_lbl in [(p0, "0th"), (p25, "25th"),
                                      (p50, "50th"), (p75, "75th"), (p100, "100th")]:
                fig.add_annotation(
                    x=pct_val, y=model_name,
                    text=f"<b>{pct_lbl}</b><br>{pct_val:.4f}",
                    showarrow=False,
                    font=dict(size=10, color=COLORS[model_name]),
                    yshift=42 if model_name == "Big v9" else -42,
                    xanchor="center",
                    row=row_idx, col=1,
                )

        x_max = max(
            results[("Old NN", n)][metric_key].max(),
            results[("Big v9",  n)][metric_key].max(),
        )
        fig.update_xaxes(
            title_text=metric_label,
            title_font=dict(size=13),
            tickfont=dict(size=12),
            tickformat=".4f",
            showgrid=True,
            gridcolor="#eeeeee",
            range=[0, x_max / 4],
            row=row_idx, col=1,
        )
        fig.update_yaxes(
            tickfont=dict(size=13),
            row=row_idx, col=1,
        )

    fig.update_layout(
        height=len(SAMPLE_SIZES) * 230,
        margin=dict(t=40, b=40, l=90, r=30),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01, x=0.5,
            xanchor="center", font=dict(size=15),
        ),
        boxmode="overlay",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    # Make subplot titles bigger
    for ann in fig.layout.annotations:
        ann.font = dict(size=14, color="#333")

    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Bar chart — mean comparison across sample sizes
# ---------------------------------------------------------------------------

st.subheader("Mean Metric Comparison — Trend by Sample Size")

fig_bar = make_subplots(
    rows=1, cols=3,
    subplot_titles=[m[1] for m in METRICS],
    horizontal_spacing=0.08,
)

for col_idx, (metric_key, metric_label, _) in enumerate(METRICS, start=1):
    for model_name in ("Old NN", "Big v9"):
        means = [results[(model_name, n)][metric_key].mean() for n in SAMPLE_SIZES]
        stds  = [results[(model_name, n)][metric_key].std()  for n in SAMPLE_SIZES]
        fig_bar.add_trace(
            go.Bar(
                name=model_name,
                x=[f"n={n}" for n in SAMPLE_SIZES],
                y=means,
                error_y=dict(type="data", array=stds, visible=True),
                marker_color=COLORS[model_name],
                opacity=0.85,
                legendgroup=model_name,
                showlegend=(col_idx == 1),
                text=[f"{v:.4f}" for v in means],
                textposition="outside",
                textfont=dict(size=10),
            ),
            row=1, col=col_idx,
        )
    fig_bar.update_yaxes(title_text=metric_label, row=1, col=col_idx)

fig_bar.update_layout(
    height=600,
    barmode="group",
    margin=dict(t=60, b=40, l=60, r=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0.5,
                xanchor="center", font=dict(size=13)),
    plot_bgcolor="white",
    paper_bgcolor="white",
)
fig_bar.update_xaxes(tickfont=dict(size=11))

st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------------------------
# Trend lines
# ---------------------------------------------------------------------------

st.subheader("Trend Lines (mean +/- std)")

fig_line = make_subplots(
    rows=1, cols=3,
    subplot_titles=[m[1] for m in METRICS],
    horizontal_spacing=0.08,
)

for col_idx, (metric_key, metric_label, _) in enumerate(METRICS, start=1):
    for model_name in ("Old NN", "Big v9"):
        means = np.array([results[(model_name, n)][metric_key].mean() for n in SAMPLE_SIZES])
        stds  = np.array([results[(model_name, n)][metric_key].std()  for n in SAMPLE_SIZES])
        color = COLORS[model_name]
        fig_line.add_trace(
            go.Scatter(
                x=SAMPLE_SIZES, y=means,
                name=model_name,
                mode="lines+markers",
                line=dict(color=color, width=2.5),
                marker=dict(size=9),
                legendgroup=model_name,
                showlegend=(col_idx == 1),
            ),
            row=1, col=col_idx,
        )
        # std ribbon
        fig_line.add_trace(
            go.Scatter(
                x=SAMPLE_SIZES + SAMPLE_SIZES[::-1],
                y=list(means + stds) + list((means - stds)[::-1]),
                fill="toself",
                fillcolor=color,
                opacity=0.15,
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False,
                hoverinfo="skip",
                legendgroup=model_name,
            ),
            row=1, col=col_idx,
        )
    fig_line.update_xaxes(tickvals=SAMPLE_SIZES, ticktext=[str(n) for n in SAMPLE_SIZES],
                           title_text="Sample size", row=1, col=col_idx)
    fig_line.update_yaxes(title_text=metric_label, row=1, col=col_idx)

fig_line.update_layout(
    height=550,
    margin=dict(t=60, b=40, l=60, r=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0.5,
                xanchor="center", font=dict(size=13)),
    plot_bgcolor="white",
    paper_bgcolor="white",
)

st.plotly_chart(fig_line, use_container_width=True)

# ---------------------------------------------------------------------------
# Percentile tables — one per metric, rows = (sample size, model)
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Percentile Tables")
st.caption("Rows = (sample size, model)  |  Columns = Mean, p0, p25, p50, p75, p100")

PCTS = [0, 25, 50, 75, 100]

for metric_key, metric_label, _ in METRICS:
    st.markdown(f"**{metric_label}**")
    rows = []
    for n in SAMPLE_SIZES:
        for model_name in ("Old NN", "Big v9"):
            arr = results[(model_name, n)][metric_key]
            row = {
                "n":     n,
                "Model": model_name,
                "Mean":  float(np.mean(arr)),
            }
            for p in PCTS:
                row[f"p{p}"] = float(np.percentile(arr, p))
            rows.append(row)

    df = pd.DataFrame(rows).set_index(["n", "Model"])

    # Highlight the better (lower) value between Old NN and Big v9 for each n
    def highlight_winner(df):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for n in SAMPLE_SIZES:
            for col in df.columns:
                try:
                    old_val = df.loc[(n, "Old NN"), col]
                    v9_val  = df.loc[(n, "Big v9"),  col]
                    winner  = (n, "Old NN") if old_val <= v9_val else (n, "Big v9")
                    styles.loc[winner, col] = "background-color: #c6efce; font-weight: bold"
                except Exception:
                    pass
        return styles

    st.dataframe(
        df.style
            .apply(highlight_winner, axis=None)
            .format("{:.5f}"),
        use_container_width=True,
        height=35 * len(rows) + 40,
    )
