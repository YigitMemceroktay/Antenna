"""
compare_nsamples_charts_app.py

Rich visualisation dashboard for the 5-run sample-size study.
Charts included:
  1. Grouped bar chart  — mean ± std val loss, all (arch × n_samples) groups
  2. Boxplot            — per-group distribution with individual run points
  3. Violin plot        — same distribution as box but with density shape
  4. CDF                — empirical cumulative distribution of val loss per group
  5. Learning curve     — mean val loss vs n_samples (with CI band) per arch
  6. Improvement ratio  — how much better ResUNet v9 is over AntennaNN at each n

Run:
    python -m streamlit run updates/compare_nsamples_charts_app.py
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
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
import torch
from sklearn.exceptions import InconsistentVersionWarning

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from compare_antenna_vs_tcnn_sdd11 import AntennaNeuralNet
from train_resunet_big_v2 import SmoothResUNet1D, INPUT_COLUMNS as _INPUT_COLUMNS

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = PROJECT_ROOT / "NNModel" / "nsamples_summary.json"
NN_DIR       = PROJECT_ROOT / "NNModel"
NEWDATA      = PROJECT_ROOT / "NewData"
TARGET_LEN   = 201

SAMPLE_SIZES = [100, 250, 500, 1000]
ARCHS        = ["resunet_v9", "antenna_nn"]
ARCH_LABELS  = {"resunet_v9": "ResUNet", "antenna_nn": "AntennaNN"}

# Colour palettes — dark anchor + 5 lighter shades for individual runs
ARCH_PALETTE = {
    "resunet_v9": {
        "main":  "#7B1FA2",
        "light": "#CE93D8",
        "runs":  ["#4A148C", "#6A1B9A", "#8E24AA", "#AB47BC", "#CE93D8"],
        "fill":  "rgba(123,31,162,0.15)",
    },
    "antenna_nn": {
        "main":  "#1565C0",
        "light": "#90CAF9",
        "runs":  ["#0D47A1", "#1565C0", "#1976D2", "#42A5F5", "#90CAF9"],
        "fill":  "rgba(21,101,192,0.15)",
    },
}

TEMPLATE = "plotly_white"

# ---------------------------------------------------------------------------
# Data loading & RSE magnitude computation
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading NewData/LHS test set…")
def load_test_data():
    x_list, r_list, i_list = [], [], []
    for p in sorted((NEWDATA / "inputs").glob("inputs_LHS_n50_seed*.csv")):
        seed = p.stem.split("seed")[-1]
        rp   = NEWDATA / "reals"     / f"real_LHS_n50_seed{seed}.csv"
        ip   = NEWDATA / "imaginary" / f"imag_LHS_n50_seed{seed}.csv"
        if not (rp.exists() and ip.exists()):
            continue
        x    = pd.read_csv(p)[_INPUT_COLUMNS].values.astype(np.float32)
        real = pd.read_csv(rp).values.astype(np.float32)
        imag = pd.read_csv(ip).values.astype(np.float32)
        n    = min(len(x), len(real), len(imag))
        x_list.append(x[:n]); r_list.append(real[:n]); i_list.append(imag[:n])
    return np.concatenate(x_list), np.concatenate(r_list), np.concatenate(i_list)


def _rse_mag(rp, ip, rt, it, eps=1e-6):
    mag_pred = np.sqrt(rp**2 + ip**2)
    mag_true = np.sqrt(rt**2 + it**2)
    return float(np.mean((mag_pred - mag_true)**2 / (mag_true**2 + eps)))


@st.cache_data(show_spinner="Evaluating all models…")
def build_df(_x_test, _r_test, _i_test) -> pd.DataFrame:
    """Load every n-samples model and compute mean RSE magnitude on the test set."""
    rows = []
    for arch in ARCHS:
        for n in SAMPLE_SIZES:
            for run_i in range(1, 6):
                tag = f"{arch}_n{n}_run{run_i}"
                model_path  = NN_DIR / f"trained_model_{tag}.pt"
                scaler_path = NN_DIR / f"scaler_{tag}.gz"
                if not (model_path.exists() and scaler_path.exists()):
                    continue

                scaler = joblib.load(scaler_path)
                x_sc   = scaler.transform(_x_test).astype(np.float32)

                if arch == "antenna_nn":
                    model = AntennaNeuralNet()
                else:
                    model = SmoothResUNet1D(input_dim=len(_INPUT_COLUMNS),
                                           target_len=TARGET_LEN)
                model.load_state_dict(torch.load(model_path, map_location="cpu"))
                model.eval()

                with torch.no_grad():
                    out = model(torch.tensor(x_sc)).numpy()
                rp, ip = out[:, 0, :], out[:, 1, :]

                rse = _rse_mag(rp, ip, _r_test, _i_test)
                rows.append({
                    "arch":       arch,
                    "arch_label": ARCH_LABELS[arch],
                    "n_samples":  n,
                    "run":        run_i,
                    "val_loss":   rse,
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def chart_bar(df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart — mean ± std, individual run dots overlaid."""
    fig = go.Figure()

    x_labels = [str(n) for n in SAMPLE_SIZES]

    for arch in ARCHS:
        pal   = ARCH_PALETTE[arch]
        label = ARCH_LABELS[arch]
        sub   = df[df["arch"] == arch]

        means = sub.groupby("n_samples")["val_loss"].mean().reindex(SAMPLE_SIZES).values
        stds  = sub.groupby("n_samples")["val_loss"].std(ddof=1).reindex(SAMPLE_SIZES).values

        # Bar
        fig.add_trace(go.Bar(
            name=label,
            x=x_labels,
            y=means,
            error_y=dict(type="data", array=stds, visible=True,
                         thickness=2, width=6, color=pal["main"]),
            marker=dict(color=pal["main"], opacity=0.82,
                        line=dict(color="white", width=1.2)),
            legendgroup=arch,
        ))

        # Individual run dots
        for run_i in range(1, 6):
            sub_r = sub[sub["run"] == run_i]
            fig.add_trace(go.Scatter(
                x=[str(n) for n in sub_r["n_samples"]],
                y=sub_r["val_loss"].values,
                mode="markers",
                marker=dict(size=9, color=pal["runs"][run_i - 1],
                            line=dict(width=1, color="white"), opacity=0.95),
                name=f"{label} — run {run_i}",
                legendgroup=f"{arch}_runs",
                showlegend=(run_i == 1),
                legendgrouptitle_text=f"{label} runs" if run_i == 1 else None,
            ))

    fig.update_layout(
        barmode="group",
        xaxis_title="Training sample size  (n)",
        yaxis_title="Mean RSE Magnitude",
        template=TEMPLATE,
        height=480,
        legend=dict(groupclick="toggleitem", tracegroupgap=4),
        margin=dict(t=40),
        font=dict(color="black", size=14),
        xaxis=dict(title_font=dict(color="black"), tickfont=dict(color="black")),
        yaxis=dict(title_font=dict(color="black"), tickfont=dict(color="black")),
    )
    return fig


def chart_box(df: pd.DataFrame) -> go.Figure:
    """Boxplot — one box per (arch, n_samples), colour-coded by arch."""
    fig = go.Figure()

    for arch in ARCHS:
        pal   = ARCH_PALETTE[arch]
        label = ARCH_LABELS[arch]
        sub   = df[df["arch"] == arch]

        for n in SAMPLE_SIZES:
            vals = sub[sub["n_samples"] == n]["val_loss"].values
            fig.add_trace(go.Box(
                y=vals,
                x=[f"n={n}"] * len(vals),
                name=f"{label}  n={n}",
                marker_color=pal["main"],
                fillcolor=pal["fill"].replace("0.15", "0.30"),
                line_color=pal["main"],
                boxmean="sd",          # show mean + SD marker
                boxpoints="all",       # show all 5 run points
                jitter=0.25,
                pointpos=0,
                marker=dict(size=8, opacity=0.9,
                            line=dict(width=1, color="white")),
                legendgroup=arch,
                showlegend=(n == SAMPLE_SIZES[0]),
                offsetgroup=arch,
            ))

    fig.update_layout(
        boxmode="group",
        xaxis_title="Training sample size",
        yaxis_title="Mean RSE Magnitude",
        template=TEMPLATE,
        height=480,
        legend=dict(tracegroupgap=8),
        margin=dict(t=40),
    )
    return fig


def chart_violin(df: pd.DataFrame) -> go.Figure:
    """Violin plot — same grouping as boxplot but shows density shape."""
    fig = go.Figure()

    for arch in ARCHS:
        pal   = ARCH_PALETTE[arch]
        label = ARCH_LABELS[arch]
        sub   = df[df["arch"] == arch]

        for n in SAMPLE_SIZES:
            vals = sub[sub["n_samples"] == n]["val_loss"].values
            fig.add_trace(go.Violin(
                y=vals,
                x=[f"n={n}"] * len(vals),
                name=f"{label}  n={n}",
                fillcolor=pal["fill"].replace("0.15", "0.35"),
                line_color=pal["main"],
                meanline_visible=True,
                box_visible=True,
                points="all",
                jitter=0.25,
                marker=dict(size=8, color=pal["main"], opacity=0.9,
                            line=dict(width=1, color="white")),
                legendgroup=arch,
                showlegend=(n == SAMPLE_SIZES[0]),
                offsetgroup=arch,
            ))

    fig.update_layout(
        violinmode="group",
        xaxis_title="Training sample size",
        yaxis_title="Mean RSE Magnitude",
        template=TEMPLATE,
        height=480,
        legend=dict(tracegroupgap=8),
        margin=dict(t=40),
    )
    return fig


def chart_cdf(df: pd.DataFrame, per_arch: bool = False) -> go.Figure:
    """Empirical CDF of val loss — one curve per group or per arch."""
    fig = go.Figure()

    if per_arch:
        # One CDF per architecture (aggregate over all n_samples)
        for arch in ARCHS:
            pal   = ARCH_PALETTE[arch]
            label = ARCH_LABELS[arch]
            vals  = np.sort(df[df["arch"] == arch]["val_loss"].values)
            cdf   = np.arange(1, len(vals) + 1) / len(vals)
            fig.add_trace(go.Scatter(
                x=vals, y=cdf * 100,
                mode="lines+markers",
                name=label,
                line=dict(color=pal["main"], width=3),
                marker=dict(size=8, color=pal["main"],
                            line=dict(width=1, color="white")),
            ))
    else:
        # One CDF per (arch, n_samples) — 8 curves total
        dash_map = {100: "solid", 250: "dash", 500: "dot", 1000: "dashdot"}
        for arch in ARCHS:
            pal   = ARCH_PALETTE[arch]
            label = ARCH_LABELS[arch]
            for n in SAMPLE_SIZES:
                sub  = df[(df["arch"] == arch) & (df["n_samples"] == n)]
                vals = np.sort(sub["val_loss"].values)
                cdf  = np.arange(1, len(vals) + 1) / len(vals)
                # Extend to draw step CDF
                x_step = np.repeat(vals, 2)[1:]
                y_step = np.repeat(cdf, 2)[:-1]
                fig.add_trace(go.Scatter(
                    x=x_step, y=y_step * 100,
                    mode="lines",
                    name=f"{label}  n={n}",
                    line=dict(color=pal["runs"][SAMPLE_SIZES.index(n)],
                              width=2.5, dash=dash_map[n]),
                    legendgroup=arch,
                ))
                # Dots at actual observations
                fig.add_trace(go.Scatter(
                    x=vals, y=cdf * 100,
                    mode="markers",
                    marker=dict(size=9, color=pal["runs"][SAMPLE_SIZES.index(n)],
                                line=dict(width=1, color="white")),
                    showlegend=False,
                    legendgroup=arch,
                ))

    # Reference lines at 25%, 50%, 75%
    for pct in [25, 50, 75]:
        fig.add_hline(y=pct, line=dict(color="rgba(0,0,0,0.18)", dash="dot", width=1))

    fig.update_layout(
        xaxis_title="Mean RSE Magnitude",
        yaxis_title="Cumulative frequency (%)",
        yaxis=dict(range=[0, 105], ticksuffix="%"),
        template=TEMPLATE,
        height=480,
        legend=dict(groupclick="toggleitem", tracegroupgap=4),
        margin=dict(t=40),
    )
    return fig


def chart_learning_curve(df: pd.DataFrame) -> go.Figure:
    """Mean val loss vs n_samples with ±1 SD ribbon."""
    fig = go.Figure()

    for arch in ARCHS:
        pal   = ARCH_PALETTE[arch]
        label = ARCH_LABELS[arch]
        sub   = df[df["arch"] == arch]

        ns    = SAMPLE_SIZES
        means = [sub[sub["n_samples"] == n]["val_loss"].mean() for n in ns]
        stds  = [sub[sub["n_samples"] == n]["val_loss"].std(ddof=1) for n in ns]

        upper = [m + s for m, s in zip(means, stds)]
        lower = [max(0, m - s) for m, s in zip(means, stds)]

        # Confidence ribbon
        fig.add_trace(go.Scatter(
            x=ns + ns[::-1],
            y=upper + lower[::-1],
            fill="toself",
            fillcolor=pal["fill"],
            line=dict(color="rgba(0,0,0,0)"),
            name=f"{label} ±1 SD",
            legendgroup=arch,
            showlegend=True,
        ))

        # Mean line
        fig.add_trace(go.Scatter(
            x=ns, y=means,
            mode="lines+markers",
            name=label,
            line=dict(color=pal["main"], width=3),
            marker=dict(size=11, color=pal["main"],
                        line=dict(width=2, color="white")),
            legendgroup=arch,
        ))

        # Individual run traces (thin, semi-transparent)
        for run_i in range(1, 6):
            sub_r = sub[sub["run"] == run_i]
            yvals = [sub_r[sub_r["n_samples"] == n]["val_loss"].values[0]
                     if len(sub_r[sub_r["n_samples"] == n]) else np.nan
                     for n in ns]
            fig.add_trace(go.Scatter(
                x=ns, y=yvals,
                mode="lines+markers",
                name=f"{label} run {run_i}",
                line=dict(color=pal["runs"][run_i - 1], width=1.2, dash="dot"),
                marker=dict(size=6, color=pal["runs"][run_i - 1], opacity=0.8),
                legendgroup=f"{arch}_runs",
                showlegend=(run_i == 1),
                opacity=0.65,
            ))

    fig.update_layout(
        xaxis=dict(title="Training sample size  (n)",
                   tickvals=SAMPLE_SIZES,
                   ticktext=[str(n) for n in SAMPLE_SIZES]),
        yaxis_title="Mean RSE Magnitude",
        template=TEMPLATE,
        height=480,
        legend=dict(groupclick="toggleitem", tracegroupgap=4),
        margin=dict(t=40),
    )
    return fig


def chart_improvement(df: pd.DataFrame) -> go.Figure:
    """Relative improvement of ResUNet v9 over AntennaNN per n_samples."""
    ns, impr_mean, impr_runs = [], [], []

    for n in SAMPLE_SIZES:
        rsu = df[(df["arch"] == "resunet_v9") & (df["n_samples"] == n)]["val_loss"]
        ann = df[(df["arch"] == "antenna_nn") & (df["n_samples"] == n)]["val_loss"]
        if len(rsu) == 0 or len(ann) == 0:
            continue
        ratio_mean = (ann.mean() - rsu.mean()) / ann.mean() * 100
        # Per-run ratio (paired by seed order)
        ratios = [(a - r) / a * 100 for r, a in zip(rsu.values, ann.values)]
        ns.append(n)
        impr_mean.append(ratio_mean)
        impr_runs.append(ratios)

    fig = go.Figure()

    # Bar for mean improvement
    bar_colors = ["#43A047" if v >= 0 else "#E53935" for v in impr_mean]
    fig.add_trace(go.Bar(
        x=[str(n) for n in ns],
        y=impr_mean,
        name="Mean improvement",
        marker_color=bar_colors,
        marker_line=dict(color="white", width=1),
        opacity=0.82,
        text=[f"{v:+.1f}%" for v in impr_mean],
        textposition="outside",
    ))

    # Individual run dots
    run_colors = ["#1B5E20", "#2E7D32", "#388E3C", "#43A047", "#66BB6A"]
    for run_i, ratios_per_n in enumerate(zip(*impr_runs)):
        fig.add_trace(go.Scatter(
            x=[str(n) for n in ns],
            y=list(ratios_per_n),
            mode="markers",
            marker=dict(size=9, color=run_colors[run_i],
                        line=dict(width=1, color="white"), opacity=0.9),
            name=f"Run {run_i + 1}",
        ))

    fig.add_hline(y=0, line=dict(color="black", width=1.2, dash="dot"))

    fig.update_layout(
        xaxis_title="Training sample size  (n)",
        yaxis_title="Relative improvement (%)",
        yaxis_ticksuffix="%",
        template=TEMPLATE,
        height=420,
        legend=dict(tracegroupgap=4),
        margin=dict(t=40),
        title_text="ResUNet v9 improvement over AntennaNN  (positive = ResUNet v9 wins)",
        title_font_size=14,
    )
    return fig


def chart_heat(summary: dict) -> go.Figure:
    """Heatmap of mean val loss — architecture × sample size."""
    z_vals, text_vals = [], []
    y_labels = [ARCH_LABELS[a] for a in ARCHS]

    for arch in ARCHS:
        row, trow = [], []
        for n in SAMPLE_SIZES:
            key = f"{arch}_n{n}"
            if key in summary:
                m = summary[key]["mean"]
                s = summary[key]["std"]
                row.append(m)
                trow.append(f"{m:.4f}<br>±{s:.4f}")
            else:
                row.append(None)
                trow.append("N/A")
        z_vals.append(row)
        text_vals.append(trow)

    fig = go.Figure(go.Heatmap(
        z=z_vals,
        x=[str(n) for n in SAMPLE_SIZES],
        y=y_labels,
        text=text_vals,
        texttemplate="%{text}",
        colorscale="Purples_r",
        colorbar=dict(title="Mean val loss"),
        hoverongaps=False,
    ))

    fig.update_layout(
        xaxis_title="Training sample size  (n)",
        yaxis_title="Architecture",
        template=TEMPLATE,
        height=250,
        margin=dict(t=40, b=60),
    )
    return fig


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def build_summary_table(summary: dict) -> pd.DataFrame:
    rows = []
    for arch in ARCHS:
        for n in SAMPLE_SIZES:
            key = f"{arch}_n{n}"
            if key not in summary:
                continue
            d = summary[key]
            rows.append({
                "Architecture": ARCH_LABELS[arch],
                "n_samples":    n,
                "Mean":         d["mean"],
                "Std":          d["std"],
                "Min":          d["mean"],
                "Median":       d["mean"],
                "Max":          d["mean"],
                "CV (%)":       d["std"] / d["mean"] * 100 if d["mean"] else 0,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Streamlit app
# ---------------------------------------------------------------------------

st.set_page_config(page_title="N-Samples Visual Analysis", layout="wide")
st.title("Sample-Size Study — Visualisation Dashboard")
st.caption(
    "AntennaNN vs ResUNet v9  ·  n = 100 / 250 / 500 / 1000  ·  5 independent seeds each"
)

x_test, r_test, i_test = load_test_data()
if len(x_test) == 0:
    st.error("No NewData/LHS samples found. Check the NewData/ directory.")
    st.stop()

st.info(f"Test set: **{len(x_test)} samples** (NewData / LHS)")

df = build_df(x_test, r_test, i_test)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_bar, tab_box, tab_vio, tab_cdf, tab_lc, tab_impr, tab_heat, tab_tbl = st.tabs([
    "Bar chart",
    "Boxplot",
    "Violin",
    "CDF",
    "Learning curve",
    "Improvement",
    "Heatmap",
    "Summary table",
])

# ── Bar chart ─────────────────────────────────────────────────────────────────
with tab_bar:
    st.subheader("Grouped bar chart — mean ± std validation loss")
    st.caption(
        "Bars show mean best-val-loss across 5 seeds.  "
        "Error bars = ±1 standard deviation.  "
        "Dots = individual run values."
    )
    st.plotly_chart(chart_bar(df), use_container_width=True)

# ── Boxplot ───────────────────────────────────────────────────────────────────
with tab_box:
    st.subheader("Boxplot — validation loss distribution per group")
    st.caption(
        "Box = 25th–75th percentile  ·  Horizontal line = median  "
        "·  X marker = mean  ·  Whiskers extend to min/max  ·  Dots = individual runs."
    )
    st.plotly_chart(chart_box(df), use_container_width=True)

# ── Violin ────────────────────────────────────────────────────────────────────
with tab_vio:
    st.subheader("Violin plot — distribution shape + embedded box")
    st.caption(
        "Width of violin represents the kernel-density estimate.  "
        "Inner box and mean line are also shown.  Dots = individual runs."
    )
    st.plotly_chart(chart_violin(df), use_container_width=True)

# ── CDF ───────────────────────────────────────────────────────────────────────
with tab_cdf:
    st.subheader("Empirical CDF of validation loss")
    cdf_mode = st.radio(
        "Granularity",
        ["Per architecture (aggregate)", "Per (arch, n_samples)"],
        horizontal=True,
    )
    st.caption(
        "CDF shows what fraction of runs achieved at most a given val loss.  "
        "A curve shifted left means lower (better) losses.  "
        "Dashed reference lines at 25 %, 50 %, 75 %."
    )
    per_arch = cdf_mode.startswith("Per arch")
    st.plotly_chart(chart_cdf(df, per_arch=per_arch), use_container_width=True)

# ── Learning curve ────────────────────────────────────────────────────────────
with tab_lc:
    st.subheader("Learning curve — mean val loss vs training sample size")
    st.caption(
        "Shaded ribbon = mean ± 1 SD across 5 seeds.  "
        "Thin dotted lines = individual runs.  "
        "Steeper descent → stronger data-efficiency benefit."
    )
    st.plotly_chart(chart_learning_curve(df), use_container_width=True)

# ── Improvement ───────────────────────────────────────────────────────────────
with tab_impr:
    st.subheader("Relative improvement of ResUNet v9 over AntennaNN")
    st.caption(
        "Improvement (%) = (AntennaNN_loss − ResUNet_loss) / AntennaNN_loss × 100.  "
        "Positive = ResUNet v9 wins.  Computed on mean val loss per n_samples."
    )
    st.plotly_chart(chart_improvement(df), use_container_width=True)

# ── Heatmap ───────────────────────────────────────────────────────────────────
with tab_heat:
    st.subheader("Heatmap — mean RSE Magnitude (architecture × sample size)")
    st.caption("Each cell shows mean ± std.  Darker = lower (better).")
    # Build summary dict from df for the heatmap
    heat_summary = {}
    for arch in ARCHS:
        for n in SAMPLE_SIZES:
            key = f"{arch}_n{n}"
            sub = df[(df["arch"] == arch) & (df["n_samples"] == n)]["val_loss"]
            if len(sub):
                heat_summary[key] = {"mean": float(sub.mean()), "std": float(sub.std(ddof=1))}
    st.plotly_chart(chart_heat(heat_summary), use_container_width=True)

# ── Summary table ─────────────────────────────────────────────────────────────
with tab_tbl:
    st.subheader("Summary statistics table")
    tbl = build_summary_table(heat_summary)
    st.dataframe(
        tbl.style.format({
            "Mean":    "{:.5f}",
            "Std":     "{:.5f}",
            "Min":     "{:.5f}",
            "Median":  "{:.5f}",
            "Max":     "{:.5f}",
            "CV (%)":  "{:.1f}",
        }).background_gradient(subset=["Mean"], cmap="Purples_r"),
        use_container_width=True,
    )
    st.caption("CV = coefficient of variation (std / mean × 100 %) — lower = more consistent.")
