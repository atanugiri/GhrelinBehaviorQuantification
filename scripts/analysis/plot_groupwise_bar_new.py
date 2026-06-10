import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.stats import ttest_ind, f_oneway, sem
from statsmodels.stats.multicomp import pairwise_tukeyhsd


def _format_p(p):
    """Format p-value for plot annotation."""
    if pd.isna(p):
        return "p = nan"
    elif p < 0.001:
        return "p < 0.001"
    else:
        return f"p = {p:.3f}"


def _add_stat_bracket(ax, x1, x2, y, h, text, fontsize=9):
    """Draw bracket with text between two x positions."""
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], color="black", linewidth=1)
    ax.text(
        (x1 + x2) / 2,
        y + h,
        text,
        ha="center",
        va="bottom",
        fontsize=fontsize,
    )


def plot_groupwise_bar(
    df,
    y,
    group_col="group",
    order=None,
    title=None,
    ylabel=None,
    figsize=(6, 4),
    point_jitter=0.08,
    point_alpha=0.6,
    point_size=30,
    capsize=5,
    annotate=True,
    random_seed=0,
    show_points=True,
):
    """
    Plot group means as bars with SEM, overlay individual points,
    run statistics automatically, and annotate results.

    Rules:
    - If exactly 2 groups: Welch's t-test
    - If >= 3 groups: one-way ANOVA + Tukey HSD post-hoc comparisons
    - If < 2 valid groups: no statistical test

    Returns
    -------
    fig, ax, stats_df

    stats_df contains:
    - For 2 groups: Welch t-test result
    - For >=3 groups: Tukey post-hoc results
    - Overall ANOVA is stored in stats_df.attrs["anova"]
    """

    if group_col not in df.columns:
        raise ValueError(f"DataFrame must contain group column: {group_col}")

    if y not in df.columns:
        raise ValueError(f"DataFrame must contain y column: {y}")

    plot_df = df[[group_col, y]].dropna().copy()

    if order is None:
        order = list(pd.unique(plot_df[group_col]))
    else:
        order = [g for g in order if g in plot_df[group_col].unique()]

    # Important: restrict data to the groups being plotted/statistically tested
    plot_df = plot_df[plot_df[group_col].isin(order)].copy()

    # Match old logic: make group categorical using the requested order
    plot_df[group_col] = pd.Categorical(
        plot_df[group_col],
        categories=order,
        ordered=True,
    )

    if len(order) == 0:
        raise ValueError("No valid groups found after removing NaN values.")

    group_data = {
        g: plot_df.loc[plot_df[group_col] == g, y].dropna().values
        for g in order
    }

    valid_groups = [g for g in order if len(group_data[g]) > 0]

    means = [np.mean(group_data[g]) for g in valid_groups]
    sems = [
        sem(group_data[g], nan_policy="omit") if len(group_data[g]) > 1 else 0
        for g in valid_groups
    ]
    ns = [len(group_data[g]) for g in valid_groups]

    x = np.arange(len(valid_groups))

    fig, ax = plt.subplots(figsize=figsize)

    # Bars with SEM
    ax.bar(
        x,
        means,
        yerr=sems,
        capsize=capsize,
        edgecolor="black",
        linewidth=1,
        alpha=0.75,
    )

    # Individual data points
    if show_points:
        rng = np.random.default_rng(random_seed)

        for i, g in enumerate(valid_groups):
            vals = group_data[g]
            jitter = rng.normal(loc=0, scale=point_jitter, size=len(vals))

            ax.scatter(
                np.full(len(vals), i) + jitter,
                vals,
                color="black",
                alpha=point_alpha,
                s=point_size,
                zorder=3,
            )

    # X labels with n
    ax.set_xticks(x)
    ax.set_xticklabels([f"{g}\n(n={n})" for g, n in zip(valid_groups, ns)])

    ax.set_ylabel(ylabel if ylabel is not None else y.replace("_", " ").capitalize())
    ax.set_xlabel("")
    ax.set_title(title if title is not None else f"{y.replace('_', ' ').capitalize()} by group")

    stats_rows = []
    anova_result = None

    # -------------------------
    # Statistics
    # -------------------------
    if len(valid_groups) == 2:
        g1, g2 = valid_groups
        a = group_data[g1]
        b = group_data[g2]

        if len(a) > 1 and len(b) > 1:
            t_stat, p_val = ttest_ind(a, b, equal_var=False, nan_policy="omit")
        else:
            t_stat, p_val = np.nan, np.nan

        stats_rows.append({
            "test": "Welch t-test",
            "group1": g1,
            "group2": g2,
            "n1": len(a),
            "n2": len(b),
            "mean1": np.mean(a),
            "mean2": np.mean(b),
            "t": t_stat,
            "p": p_val,
        })

        stats_df = pd.DataFrame(stats_rows)
        stats_df.attrs["anova"] = None

        print(f"Welch t-test: {g1} vs {g2}")
        print(f"t = {t_stat:.4f}, p = {p_val:.4g}")

        if annotate:
            y_max = max(np.max(a), np.max(b))
            y_range = plot_df[y].max() - plot_df[y].min()
            if y_range == 0:
                y_range = 1

            bracket_y = y_max + 0.08 * y_range
            bracket_h = 0.04 * y_range

            _add_stat_bracket(
                ax,
                0,
                1,
                bracket_y,
                bracket_h,
                _format_p(p_val),
            )

    elif len(valid_groups) >= 3:
        arrays = [group_data[g] for g in valid_groups]

        if all(len(arr) > 1 for arr in arrays):
            f_stat, p_anova = f_oneway(*arrays)
        else:
            f_stat, p_anova = np.nan, np.nan

        anova_result = {
            "test": "one-way ANOVA",
            "groups": valid_groups,
            "df_between": len(valid_groups) - 1,
            "df_within": sum(len(arr) for arr in arrays) - len(valid_groups),
            "F": f_stat,
            "p": p_anova,
        }

        print("One-way ANOVA")
        print(
            f"F({anova_result['df_between']}, {anova_result['df_within']}) = "
            f"{f_stat:.4f}, p = {p_anova:.4g}"
        )

        # Tukey HSD post-hoc
        tukey = pairwise_tukeyhsd(
            endog=plot_df[y],
            groups=plot_df[group_col],
            alpha=0.05,
        )

        tukey_table = pd.DataFrame(
            data=tukey.summary().data[1:],
            columns=tukey.summary().data[0],
        )

        tukey_table = tukey_table.rename(columns={
            "group1": "group1",
            "group2": "group2",
            "meandiff": "mean_diff",
            "p-adj": "p",
            "lower": "ci_low",
            "upper": "ci_high",
            "reject": "reject",
        })

        for col in ["mean_diff", "p", "ci_low", "ci_high"]:
            tukey_table[col] = tukey_table[col].astype(float)

        tukey_table["test"] = "Tukey HSD"

        stats_df = tukey_table[
            ["test", "group1", "group2", "mean_diff", "p", "ci_low", "ci_high", "reject"]
        ].copy()

        stats_df.attrs["anova"] = anova_result

        print("\nTukey HSD post-hoc:")
        print(stats_df.to_string(index=False))

        if annotate:
            y_range = plot_df[y].max() - plot_df[y].min()
            if y_range == 0:
                y_range = 1

            current_y = plot_df[y].max() + 0.08 * y_range
            bracket_h = 0.04 * y_range
            bracket_gap = 0.13 * y_range

            group_to_x = {g: i for i, g in enumerate(valid_groups)}

            for _, row in stats_df.iterrows():
                g1 = row["group1"]
                g2 = row["group2"]
                p_val = row["p"]

                if g1 not in group_to_x or g2 not in group_to_x:
                    continue

                x1 = group_to_x[g1]
                x2 = group_to_x[g2]

                _add_stat_bracket(
                    ax,
                    x1,
                    x2,
                    current_y,
                    bracket_h,
                    _format_p(p_val),
                )

                current_y += bracket_gap

    else:
        stats_df = pd.DataFrame()
        stats_df.attrs["anova"] = None
        print("Only one valid group found. No statistical test was performed.")

    # Add space on top for annotations
    if annotate and len(valid_groups) >= 2:
        y_min, y_max = ax.get_ylim()
        ax.set_ylim(y_min, y_max * 1.15 if y_max > 0 else y_max + 1)

    fig.tight_layout()

    return fig, ax, stats_df