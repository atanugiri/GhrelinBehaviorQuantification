import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from typing import List, Tuple, Dict, Optional
from scipy.stats import ranksums, ttest_ind, f_oneway
from statsmodels.stats.multicomp import pairwise_tukeyhsd


# ---------------- Utilities ----------------

def _p_to_star(p: float) -> str:
    if pd.isna(p):
        return "n.a."
    if p < 1e-4:
        return "****"
    if p < 1e-3:
        return "***"
    if p < 1e-2:
        return "**"
    if p < 5e-2:
        return "*"
    return "n.s."


def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Compute Cohen's d using pooled variance."""
    na, nb = len(a), len(b)

    if na < 2 or nb < 2:
        return np.nan

    va, vb = a.var(ddof=1), b.var(ddof=1)
    sp2 = ((na - 1) * va + (nb - 1) * vb) / (na + nb - 2)

    if sp2 <= 0 or np.isnan(sp2):
        return np.nan

    return float((a.mean() - b.mean()) / np.sqrt(sp2))


def _rank_biserial_from_ranksums(a: np.ndarray, b: np.ndarray) -> float:
    """Compute rank-biserial effect size using Cliff's delta logic."""
    if len(a) == 0 or len(b) == 0:
        return np.nan

    A = np.asarray(a)
    B = np.asarray(b)

    if len(A) * len(B) > 250000:
        z, _ = ranksums(A, B)
        N = len(A) + len(B)
        return float(z / np.sqrt(N))

    gt = (A[:, None] > B[None, :]).sum()
    lt = (A[:, None] < B[None, :]).sum()

    delta = (gt - lt) / (len(A) * len(B))
    return float(delta)


def _bh_fdr(pvals: List[float]) -> List[float]:
    """Benjamini-Hochberg FDR correction."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)

    order = np.argsort(p)
    ranked = p[order]

    adj = ranked * n / (np.arange(1, n + 1))
    adj[::-1] = np.minimum.accumulate(adj[::-1])

    out = np.empty_like(adj)
    out[order] = np.clip(adj, 0, 1)

    return out.tolist()


def _pair_stats(
    a: pd.Series,
    b: pd.Series,
    tests=("ranksums", "ttest"),
) -> Dict[str, float]:
    """Compute pairwise statistics between two groups."""
    avals = a.dropna().values
    bvals = b.dropna().values

    out = {
        "n_a": len(avals),
        "n_b": len(bvals),
        "mean_a": float(np.mean(avals)) if len(avals) else np.nan,
        "mean_b": float(np.mean(bvals)) if len(bvals) else np.nan,
        "cohens_d": np.nan,
        "rank_biserial": np.nan,
        "t": np.nan,
        "p_ttest": np.nan,
        "z_rs": np.nan,
        "p_rs": np.nan,
    }

    if "ttest" in tests and len(avals) > 1 and len(bvals) > 1:
        t, p = ttest_ind(avals, bvals, equal_var=False, nan_policy="omit")
        out["t"] = float(t)
        out["p_ttest"] = float(p)
        out["cohens_d"] = _cohens_d(avals, bvals)

    if "ranksums" in tests and len(avals) > 0 and len(bvals) > 0:
        z, p = ranksums(avals, bvals)
        out["z_rs"] = float(z)
        out["p_rs"] = float(p)
        out["rank_biserial"] = _rank_biserial_from_ranksums(avals, bvals)

    return out


def _anova_stats(groups: List[np.ndarray]) -> Dict[str, float]:
    """Compute one-way ANOVA and eta squared."""
    groups = [np.asarray(g, dtype=float) for g in groups if len(g) > 0]

    out = {
        "df_between": np.nan,
        "df_within": np.nan,
        "f_anova": np.nan,
        "p_anova": np.nan,
        "eta_sq": np.nan,
    }

    if len(groups) < 2:
        return out

    n_total = sum(len(g) for g in groups)
    k = len(groups)

    if n_total <= k:
        return out

    f_stat, p_val = f_oneway(*groups)

    all_vals = np.concatenate(groups)
    grand_mean = np.mean(all_vals)

    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)
    ss_total = np.sum((all_vals - grand_mean) ** 2)

    out.update({
        "df_between": float(k - 1),
        "df_within": float(n_total - k),
        "f_anova": float(f_stat),
        "p_anova": float(p_val),
        "eta_sq": float(ss_between / ss_total) if ss_total > 0 else np.nan,
    })

    return out


# ---------------- Main plot function ----------------

def plot_groupwise_bar(
    df: pd.DataFrame,
    y: str = "total_distance",
    title: Optional[str] = None,
    ylabel: Optional[str] = None,
    figsize: Tuple[int, int] = (6, 4),
    plot_type: str = "bar",
    order: Optional[List[str]] = None,
    show_points: bool = True,
    pairwise: str = "vs_first",
    fdr_correction: bool = False,
    annotate_stats: bool = True,
):
    """
    Compare groups and annotate numeric statistics.

    Behavior
    --------
    - If there are 2 valid groups:
        Uses Welch's t-test.

    - If there are 3 or more valid groups:
        Uses one-way ANOVA + Tukey HSD post-hoc.

    - By default, pairwise='vs_first':
        Compares first group vs every other group.
        Example:
            Saline vs Ghrelin
            Saline vs Inhibitory
            Saline vs Excitatory

    Notes
    -----
    Star annotations above bars are intentionally removed.
    Numeric ANOVA and post-hoc results are shown on the figure when
    annotate_stats=True.

    Returns
    -------
    fig, ax, stats_df
    """

    if y not in df.columns or "group" not in df.columns:
        raise ValueError("DataFrame must contain columns: 'group' and the feature column.")

    if order is None:
        order = list(pd.unique(df["group"]))

    df = df.copy()
    df = df[df["group"].isin(order)].copy()
    df["group"] = pd.Categorical(df["group"], categories=order, ordered=True)

    fig, ax = plt.subplots(figsize=figsize)
    palette = sns.color_palette("Set2", n_colors=len(order))

    if plot_type == "bar":
        sns.barplot(
            data=df,
            x="group",
            y=y,
            order=order,
            errorbar="se",
            capsize=0.15,
            errwidth=1.2,
            palette=palette,
            ax=ax,
        )

    elif plot_type == "box":
        sns.boxplot(
            data=df,
            x="group",
            y=y,
            order=order,
            palette=palette,
            ax=ax,
            showcaps=True,
            boxprops=dict(alpha=0.7),
            medianprops=dict(color="black"),
        )

    else:
        raise ValueError("plot_type must be either 'bar' or 'box'.")

    if show_points:
        sns.stripplot(
            data=df,
            x="group",
            y=y,
            order=order,
            dodge=False,
            alpha=0.5,
            size=4,
            ax=ax,
            color="k",
        )

    # --- Group values ---
    group_values = [
        df.loc[df["group"] == g, y].dropna().values
        for g in order
    ]

    valid_order = [
        g for g, vals in zip(order, group_values)
        if len(vals) > 0
    ]

    group_count = len(valid_order)

    # --- Overall ANOVA only for 3+ valid groups ---
    if group_count >= 3:
        anova_res = _anova_stats([
            df.loc[df["group"] == g, y].dropna().values
            for g in valid_order
        ])
    else:
        anova_res = {}

    # --- Show sample sizes under tick labels ---
    ns = df.groupby("group")[y].apply(lambda s: s.dropna().size).reindex(order)

    ax.set_xticklabels([
        f"{g}\n(n={int(ns[g]) if pd.notna(ns[g]) else 0})"
        for g in order
    ])

    # --- Build requested comparisons ---
    comps = []

    if pairwise == "none":
        comps = []

    elif pairwise == "vs_first":
        if len(valid_order) >= 2:
            first_group = valid_order[0]
            for g in valid_order[1:]:
                comps.append((first_group, g))

    elif pairwise == "all":
        for i in range(len(valid_order)):
            for j in range(i + 1, len(valid_order)):
                comps.append((valid_order[i], valid_order[j]))

    else:
        raise ValueError("pairwise must be one of: 'vs_first', 'all', or 'none'.")

    # --- Compute post-hoc / pairwise stats ---
    stats_rows = []

    if group_count >= 3 and comps:
        # Tukey HSD post-hoc
        df_tukey = df[["group", y]].dropna().copy()

        tukey = pairwise_tukeyhsd(
            endog=df_tukey[y],
            groups=df_tukey["group"],
            alpha=0.05,
        )

        tukey_data = tukey.summary().data

        for row in tukey_data[1:]:
            g1, g2, meandiff, p_adj, lower, upper, reject = row

            # Keep only requested comparisons.
            # This preserves pairwise='vs_first' behavior.
            if (g1, g2) not in comps and (g2, g1) not in comps:
                continue

            p_show = float(p_adj)

            stats_rows.append({
                "group_a": g1,
                "group_b": g2,
                "n_a": int(df_tukey[df_tukey["group"] == g1].shape[0]),
                "n_b": int(df_tukey[df_tukey["group"] == g2].shape[0]),
                "mean_a": float(df_tukey.loc[df_tukey["group"] == g1, y].mean()),
                "mean_b": float(df_tukey.loc[df_tukey["group"] == g2, y].mean()),
                "cohens_d": np.nan,
                "rank_biserial": np.nan,
                "t": np.nan,
                "p_ttest": np.nan,
                "z_rs": np.nan,
                "p_rs": np.nan,
                "meandiff": float(meandiff),
                "p_tukey": p_show,
                "lower": float(lower),
                "upper": float(upper),
                "reject": bool(reject),
                "p_displayed": p_show,
                "stars": _p_to_star(p_show),
                "p_displayed_fdr": np.nan,
            })

    elif group_count == 2 and comps:
        # Welch t-test
        for a_lbl, b_lbl in comps:
            a_vals = df.loc[df["group"] == a_lbl, y]
            b_vals = df.loc[df["group"] == b_lbl, y]

            row = _pair_stats(a_vals, b_vals, tests=("ttest",))
            row.update({
                "group_a": a_lbl,
                "group_b": b_lbl,
                "meandiff": np.nan,
                "p_tukey": np.nan,
                "lower": np.nan,
                "upper": np.nan,
                "reject": np.nan,
            })

            p_show = row.get("p_ttest", np.nan)
            row["p_displayed"] = p_show
            row["stars"] = _p_to_star(p_show) if pd.notna(p_show) else "n.a."
            row["p_displayed_fdr"] = np.nan

            stats_rows.append(row)

        # Optional FDR only for pairwise Welch mode
        if fdr_correction and stats_rows:
            pvals = [
                r["p_displayed"] if pd.notna(r["p_displayed"]) else 1.0
                for r in stats_rows
            ]
            padj = _bh_fdr(pvals)

            for r, q in zip(stats_rows, padj):
                r["p_displayed_fdr"] = q
                r["p_displayed"] = q
                r["stars"] = _p_to_star(q)

    stats_df = pd.DataFrame(stats_rows)
    stats_df.attrs["anova"] = anova_res

    if group_count >= 3:
        stats_df.attrs["posthoc_method"] = "tukeyhsd"
    elif group_count == 2:
        stats_df.attrs["posthoc_method"] = "pairwise_welch_ttests"
    else:
        stats_df.attrs["posthoc_method"] = "none"

    # -------------------------
    # Print statistics to stdout
    # -------------------------
    if group_count >= 3 and pd.notna(anova_res.get("p_anova", np.nan)):
        print(
            f"1-way ANOVA: F({int(anova_res['df_between'])}, "
            f"{int(anova_res['df_within'])}) = "
            f"{anova_res['f_anova']:.3g}, p = {anova_res['p_anova']:.3g}"
        )

    if not stats_df.empty:
        method = stats_df.attrs.get("posthoc_method", "")

        if method == "tukeyhsd":
            print("\nTukey HSD post-hoc:")
            print(
                stats_df[
                    ["group_a", "group_b", "meandiff", "p_tukey", "lower", "upper", "reject"]
                ].to_string(index=False)
            )

        elif method == "pairwise_welch_ttests":
            print("\nWelch t-test:")
            print(
                stats_df[
                    ["group_a", "group_b", "t", "p_ttest", "p_displayed"]
                ].to_string(index=False)
            )

    # -------------------------
    # Numeric annotations on plot
    # -------------------------

    # ANOVA text
    if annotate_stats and group_count >= 3 and pd.notna(anova_res.get("p_anova", np.nan)):
        anova_text = (
            f"1-way ANOVA: F({int(anova_res['df_between'])}, "
            f"{int(anova_res['df_within'])}) = "
            f"{anova_res['f_anova']:.3g}, p = {anova_res['p_anova']:.3g}"
        )

        ax.text(
            0.01,
            0.99,
            anova_text,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor="white",
                alpha=0.8,
                edgecolor="none",
            ),
        )

    # Numeric post-hoc text on figure
    if annotate_stats and stats_rows:
        posthoc_lines = []

        if group_count >= 3:
            posthoc_lines.append("Tukey HSD post-hoc:")
        elif group_count == 2:
            posthoc_lines.append("Welch t-test:")

        for row in stats_rows:
            group_a = row["group_a"]
            group_b = row["group_b"]

            if group_count >= 3:
                p_val = row.get("p_tukey", np.nan)
                mean_diff = row.get("meandiff", np.nan)

                if pd.notna(p_val):
                    posthoc_lines.append(
                        f"{group_a} vs {group_b}: diff = {mean_diff:.3g}, p = {p_val:.3g}"
                    )

            elif group_count == 2:
                t_val = row.get("t", np.nan)
                p_val = row.get("p_ttest", np.nan)

                if pd.notna(t_val) and pd.notna(p_val):
                    posthoc_lines.append(
                        f"{group_a} vs {group_b}: t = {t_val:.3g}, p = {p_val:.3g}"
                    )

        if posthoc_lines:
            posthoc_text = "\n".join(posthoc_lines)

            ax.text(
                0.01,
                0.88,
                posthoc_text,
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=8,
                bbox=dict(
                    boxstyle="round,pad=0.25",
                    facecolor="white",
                    alpha=0.8,
                    edgecolor="none",
                ),
            )

    ax.set_ylabel(ylabel if ylabel else y.replace("_", " ").capitalize())
    ax.set_xlabel("")
    ax.set_title(title if title else f"{y.replace('_', ' ').capitalize()} by Group", pad=12)

    fig.tight_layout()

    return fig, ax, stats_df