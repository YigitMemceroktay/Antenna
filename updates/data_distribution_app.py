"""
data_distribution_app.py

Input feature distribution analysis:
  - old_excel vs LHS (all seeds) per-feature histograms
  - PCA 2D scatter (old_excel=blue, LHS=orange)
  - Sequential order check (feature vs row index)
  - Correlation heatmaps

Run:
    python3 -m streamlit run updates/data_distribution_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import streamlit as st

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.append(str(THIS_DIR))

from train_resunet_dual import INPUT_COLUMNS

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

@st.cache_data
def load_old_excel_inputs() -> pd.DataFrame:
    p = PROJECT_ROOT / "old" / "data" / "input_parameters.xlsx"
    df = pd.read_excel(p)[INPUT_COLUMNS].copy()
    df["source"] = "old_excel"
    df["row_idx"] = np.arange(len(df))
    return df


@st.cache_data
def load_all_lhs_inputs() -> pd.DataFrame:
    files = sorted((PROJECT_ROOT / "data" / "LHS").glob(
        "input_trials_done_LHS_n20_rounded_seed*.csv"
    ))
    parts = []
    for p in files:
        seed = p.stem.split("seed")[-1]
        tmp = pd.read_csv(p)[INPUT_COLUMNS].copy()
        tmp["source"] = f"LHS seed{seed}"
        tmp["seed"] = int(seed)
        tmp["row_idx"] = np.arange(len(tmp))
        parts.append(tmp)
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="Input Distribution Analysis", layout="wide")
    st.title("Input Feature Distribution: old_excel vs LHS")

    df_excel = load_old_excel_inputs()
    df_lhs_all = load_all_lhs_inputs()

    if df_lhs_all.empty:
        st.error("No LHS files found in data/LHS.")
        return

    seeds_available = sorted(df_lhs_all["seed"].unique())
    selected_seeds = st.multiselect(
        "LHS seeds to include", seeds_available, default=seeds_available
    )
    df_lhs = df_lhs_all[df_lhs_all["seed"].isin(selected_seeds)].copy()
    df_lhs_agg = df_lhs[INPUT_COLUMNS].copy()
    df_lhs_agg["source"] = "LHS (all selected)"

    n_excel = len(df_excel)
    n_lhs = len(df_lhs)
    st.markdown(f"**old_excel**: {n_excel} samples &nbsp;|&nbsp; **LHS (selected)**: {n_lhs} samples")

    # Combined for convenience
    df_combined = pd.concat(
        [df_excel[INPUT_COLUMNS + ["source"]], df_lhs_agg],
        ignore_index=True,
    )

    # -----------------------------------------------------------------------
    # 1. Per-feature histograms
    # -----------------------------------------------------------------------
    st.subheader("Per-feature distributions")
    st.caption("Blue = old_excel, Orange = LHS. Overlapping = similar coverage.")

    n_cols = 3
    n_rows = -(-len(INPUT_COLUMNS) // n_cols)  # ceiling division
    fig_hist = make_subplots(rows=n_rows, cols=n_cols,
                             subplot_titles=INPUT_COLUMNS,
                             vertical_spacing=0.12)

    for fi, feat in enumerate(INPUT_COLUMNS):
        r = fi // n_cols + 1
        c = fi % n_cols + 1
        fig_hist.add_trace(
            go.Histogram(
                x=df_excel[feat], name="old_excel",
                opacity=0.6,
                marker_color="royalblue",
                nbinsx=30,
                showlegend=(fi == 0),
                legendgroup="old_excel",
            ),
            row=r, col=c,
        )
        fig_hist.add_trace(
            go.Histogram(
                x=df_lhs[feat], name="LHS",
                opacity=0.6,
                marker_color="darkorange",
                nbinsx=30,
                showlegend=(fi == 0),
                legendgroup="LHS",
            ),
            row=r, col=c,
        )

    fig_hist.update_layout(
        barmode="overlay",
        height=300 * n_rows,
        template="plotly_white",
        legend=dict(orientation="h", y=1.02),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # -----------------------------------------------------------------------
    # 2. PCA 2D scatter
    # -----------------------------------------------------------------------
    st.subheader("PCA — 2D projection of 11-dimensional input space")
    st.caption("If old_excel and LHS clusters overlap → similar distribution. Separated → distribution shift.")

    x_all = df_combined[INPUT_COLUMNS].values
    scaler_pca = StandardScaler()
    x_scaled = scaler_pca.fit_transform(x_all)

    pca = PCA(n_components=3)
    comps = pca.fit_transform(x_scaled)
    var_exp = pca.explained_variance_ratio_

    df_pca = pd.DataFrame({
        "PC1": comps[:, 0],
        "PC2": comps[:, 1],
        "PC3": comps[:, 2],
        "source": df_combined["source"].values,
    })

    col_pca1, col_pca2 = st.columns(2)

    with col_pca1:
        st.markdown(f"**PC1 vs PC2** ({var_exp[0]*100:.1f}% + {var_exp[1]*100:.1f}% = {(var_exp[0]+var_exp[1])*100:.1f}% variance)")
        colors_src = {"old_excel": "royalblue", "LHS (all selected)": "darkorange"}
        fig_pca = go.Figure()
        for src, grp in df_pca.groupby("source"):
            fig_pca.add_trace(go.Scatter(
                x=grp["PC1"], y=grp["PC2"],
                mode="markers",
                name=src,
                marker=dict(color=colors_src.get(src, "gray"), size=5, opacity=0.6),
            ))
        fig_pca.update_layout(
            xaxis_title=f"PC1 ({var_exp[0]*100:.1f}%)",
            yaxis_title=f"PC2 ({var_exp[1]*100:.1f}%)",
            template="plotly_white",
            height=420,
        )
        st.plotly_chart(fig_pca, use_container_width=True)

    with col_pca2:
        st.markdown(f"**PC1 vs PC3** ({var_exp[0]*100:.1f}% + {var_exp[2]*100:.1f}%)")
        fig_pca2 = go.Figure()
        for src, grp in df_pca.groupby("source"):
            fig_pca2.add_trace(go.Scatter(
                x=grp["PC1"], y=grp["PC3"],
                mode="markers",
                name=src,
                marker=dict(color=colors_src.get(src, "gray"), size=5, opacity=0.6),
            ))
        fig_pca2.update_layout(
            xaxis_title=f"PC1 ({var_exp[0]*100:.1f}%)",
            yaxis_title=f"PC3 ({var_exp[2]*100:.1f}%)",
            template="plotly_white",
            height=420,
        )
        st.plotly_chart(fig_pca2, use_container_width=True)

    with st.expander("PCA component loadings (which features drive each PC)"):
        loadings = pd.DataFrame(
            pca.components_.T,
            index=INPUT_COLUMNS,
            columns=["PC1", "PC2", "PC3"],
        )
        st.dataframe(loadings.style.format("{:.3f}").background_gradient(cmap="RdBu", axis=None),
                     use_container_width=True)

    # -----------------------------------------------------------------------
    # 3. Sequential order check — old_excel
    # -----------------------------------------------------------------------
    st.subheader("Sequential order check — old_excel")
    st.caption(
        "If features change smoothly with row index → old_excel is sequentially ordered "
        "(e.g., a grid sweep). This is fine for training but confirms the data isn't i.i.d."
    )

    feat_seq = st.selectbox("Feature to plot vs row index", INPUT_COLUMNS, index=0)
    fig_seq = go.Figure()
    fig_seq.add_trace(go.Scatter(
        x=df_excel["row_idx"],
        y=df_excel[feat_seq],
        mode="lines+markers",
        name="old_excel",
        marker=dict(size=3, color="royalblue"),
        line=dict(color="royalblue", width=1),
    ))
    fig_seq.update_layout(
        xaxis_title="Row index",
        yaxis_title=feat_seq,
        template="plotly_white",
        height=350,
    )
    st.plotly_chart(fig_seq, use_container_width=True)

    st.markdown("**All features vs row index (small multiples)**")
    fig_seq_all = make_subplots(rows=n_rows, cols=n_cols,
                                subplot_titles=INPUT_COLUMNS,
                                vertical_spacing=0.12)
    for fi, feat in enumerate(INPUT_COLUMNS):
        r = fi // n_cols + 1
        c = fi % n_cols + 1
        fig_seq_all.add_trace(
            go.Scatter(
                x=df_excel["row_idx"],
                y=df_excel[feat],
                mode="lines",
                line=dict(color="royalblue", width=1),
                showlegend=False,
            ),
            row=r, col=c,
        )
    fig_seq_all.update_layout(
        height=280 * n_rows,
        template="plotly_white",
    )
    st.plotly_chart(fig_seq_all, use_container_width=True)

    # -----------------------------------------------------------------------
    # 4. LHS — seed-to-seed consistency
    # -----------------------------------------------------------------------
    st.subheader("LHS seed-to-seed consistency")
    st.caption("Each LHS seed is an independent Latin Hypercube sample. Distributions should look similar across seeds.")

    feat_lhs = st.selectbox("Feature", INPUT_COLUMNS, key="feat_lhs", index=0)
    fig_seeds = go.Figure()
    palette = px.colors.qualitative.Plotly
    for si, seed in enumerate(seeds_available):
        sub = df_lhs_all[df_lhs_all["seed"] == seed]
        fig_seeds.add_trace(go.Box(
            y=sub[feat_lhs],
            name=f"seed{seed}",
            marker_color=palette[si % len(palette)],
        ))
    fig_seeds.update_layout(
        yaxis_title=feat_lhs,
        template="plotly_white",
        height=350,
        showlegend=False,
    )
    st.plotly_chart(fig_seeds, use_container_width=True)

    # -----------------------------------------------------------------------
    # 5. Descriptive stats comparison
    # -----------------------------------------------------------------------
    st.subheader("Descriptive statistics: old_excel vs LHS")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("**old_excel**")
        st.dataframe(df_excel[INPUT_COLUMNS].describe().T.style.format("{:.4g}"),
                     use_container_width=True)
    with col_s2:
        st.markdown("**LHS (all selected seeds)**")
        st.dataframe(df_lhs[INPUT_COLUMNS].describe().T.style.format("{:.4g}"),
                     use_container_width=True)

    # -----------------------------------------------------------------------
    # 6. Range coverage comparison
    # -----------------------------------------------------------------------
    st.subheader("Feature range coverage")
    st.caption("Does old_excel cover the full LHS range? If LHS has values outside old_excel's range → extrapolation territory.")

    range_rows = []
    for feat in INPUT_COLUMNS:
        ex_min, ex_max = df_excel[feat].min(), df_excel[feat].max()
        lhs_min, lhs_max = df_lhs[feat].min(), df_lhs[feat].max()
        lhs_below = lhs_min < ex_min
        lhs_above = lhs_max > ex_max
        range_rows.append({
            "Feature": feat,
            "old_excel min": ex_min,
            "old_excel max": ex_max,
            "LHS min": lhs_min,
            "LHS max": lhs_max,
            "LHS below excel?": "⚠ YES" if lhs_below else "ok",
            "LHS above excel?": "⚠ YES" if lhs_above else "ok",
        })
    range_df = pd.DataFrame(range_rows).set_index("Feature")
    st.dataframe(
        range_df.style.format({c: "{:.4g}" for c in range_df.columns if range_df[c].dtype != object}),
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
