import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from scipy.stats import ranksums, ttest_ind, f_oneway

def _p_to_star(pval: float) -> str:
    if pval < 1e-4: return '****'
    if pval < 1e-3: return '***'
    if pval < 1e-2: return '**'
    if pval < 5e-2: return '*'
    return 'n.s.'

def _pair_pstrings(a: pd.Series, b: pd.Series, tests=("ranksums","ttest","anova")):
    a = a.dropna().values
    b = b.dropna().values
    out = []
    if "ranksums" in tests:
        _, p = ranksums(a, b)
        out.append(f"RS: {_p_to_star(p)}")
    if "ttest" in tests:
        _, p = ttest_ind(a, b, equal_var=False, nan_policy="omit")
        out.append(f"t: {_p_to_star(p)}")
    if "anova" in tests:
        # two-group ANOVA ≈ t-test; included only if requested
        _, p = f_oneway(a, b)
        out.append(f"ANOVA: {_p_to_star(p)}")
    return out

def plot_groupwise_bar(
    df, y='total_distance', title=None, ylabel=None,
    figsize=(6, 4), plot_type='bar', order=None,
    show_stats=True, show_points=True,
    compare_to_first=True, tests_to_show=("ranksums","ttest"),
    text_fontsize=11, pad_frac=0.03
):
    """
    Compare each non-reference group (2..k) to the first group in `order`
    and print results atop each group's bar/box.
    """
    if y not in df.columns or 'group' not in df.columns:
        raise ValueError("DataFrame must contain columns: 'group' and the feature column.")

    if order is None:
        # Keep appearance stable: use group order of appearance in the df
        order = pd.Categorical(df['group'], ordered=True).categories.tolist()

    fig, ax = plt.subplots(figsize=figsize)
    palette = sns.color_palette("Set2", n_colors=len(order))

    if plot_type == 'bar':
        sns.barplot(
            data=df, x='group', y=y, order=order,
            errorbar='se', capsize=0.15, errwidth=1.2,
            palette=palette, ax=ax
        )
    elif plot_type == 'box':
        sns.boxplot(
            data=df, x='group', y=y, order=order,
            palette=palette, ax=ax, showcaps=True,
            boxprops=dict(alpha=0.7), medianprops=dict(color='black')
        )
    else:
        raise ValueError("plot_type must be either 'bar' or 'box'.")

    # Optional overlay of individual points
    if show_points:
        sns.stripplot(
            data=df, x='group', y=y, order=order,
            dodge=False, alpha=0.5, size=4, ax=ax, color='k'
        )

    # === Stats annotations: compare every group vs the first ===
    if show_stats and compare_to_first and len(order) >= 2:
        ref_label = order[0]
        ref_vals = df[df['group'] == ref_label][y]

        # y positioning helper
        ymin, ymax = ax.get_ylim()
        yspan = ymax - ymin
        # base pad above each bar = pad_frac * yspan
        base_pad = pad_frac * yspan
        line_sep = 0.9 * base_pad  # spacing between stacked lines

        # precompute means by group for a bar-top anchor
        group_means = df.groupby('group', as_index=True)[y].mean()

        for i, label in enumerate(order[1:], start=1):
            grp_vals = df[df['group'] == label][y]
            if len(ref_vals.dropna()) == 0 or len(grp_vals.dropna()) == 0:
                continue

            # Which strings to print (e.g., RS and t)
            p_lines = _pair_pstrings(ref_vals, grp_vals, tests=tests_to_show)

            # anchor: bar i's mean (works for both bar/box visuals)
            anchor = group_means.get(label, np.nan)
            if np.isnan(anchor):
                continue

            # If anchor is too close to ymax, nudge inside limits
            y_anchor = min(anchor + base_pad, ymax - base_pad)

            # stack lines upward
            for j, line in enumerate(p_lines):
                ax.text(
                    i, y_anchor + j*line_sep, line,
                    ha='center', va='bottom',
                    fontsize=text_fontsize, fontweight='bold'
                )

    ax.set_ylabel(ylabel if ylabel else y.replace('_', ' ').capitalize())
    ax.set_xlabel('')
    ax.set_title(title if title else f'{y.replace("_", " ").capitalize()} by Group', pad=12)
    fig.tight_layout()
    return fig, ax
