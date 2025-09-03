import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Iterable, List, Tuple, Dict, Optional
from scipy.stats import ranksums, ttest_ind, f_oneway

# ---------------- Utilities ----------------

def _p_to_star(p: float) -> str:
    if p < 1e-4: return '****'
    if p < 1e-3: return '***'
    if p < 1e-2: return '**'
    if p < 5e-2: return '*'
    return 'n.s.'

def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    # Welch's d (uses group variances; pooled with weights)
    na, nb = len(a), len(b)
    va, vb = a.var(ddof=1), b.var(ddof=1)
    sp2 = ((na-1)*va + (nb-1)*vb) / (na + nb - 2) if na+nb-2 > 0 else np.nan
    if sp2 <= 0 or np.isnan(sp2): 
        return np.nan
    return (a.mean() - b.mean()) / np.sqrt(sp2)

def _rank_biserial_from_ranksums(a: np.ndarray, b: np.ndarray) -> float:
    # Convert rank-sum z to rank-biserial effect size using Cliff’s delta equivalence
    # Safer to compute Cliff's delta directly:
    from math import isnan
    if len(a) == 0 or len(b) == 0: return np.nan
    # fast approximate RB via pairwise comparisons (O(n*m)); okay for modest n
    A = np.asarray(a)
    B = np.asarray(b)
    # To avoid O(n*m) blowup, fallback to an efficient estimate if very large
    if len(A)*len(B) > 250000:
        # fallback: use z / sqrt(N) approximation (rough)
        z, p = ranksums(A, B)
        N = len(A) + len(B)
        return float(z / np.sqrt(N))
    gt = (A[:, None] > B[None, :]).sum()
    lt = (A[:, None] < B[None, :]).sum()
    ties = (A[:, None] == B[None, :]).sum()
    delta = (gt - lt) / (len(A) * len(B))
    return float(delta)  # rank-biserial = Cliff’s delta for two groups

def _bh_fdr(pvals: List[float]) -> List[float]:
    # Benjamini–Hochberg FDR
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    adj = ranked * n / (np.arange(1, n+1))
    # enforce monotonicity
    adj[::-1] = np.minimum.accumulate(adj[::-1])
    out = np.empty_like(adj)
    out[order] = np.clip(adj, 0, 1)
    return out.tolist()

def _pair_stats(a: pd.Series, b: pd.Series, tests=("ranksums","ttest")) -> Dict[str, float]:
    avals = a.dropna().values
    bvals = b.dropna().values
    out = {
        "n_a": len(avals), "n_b": len(bvals),
        "mean_a": float(np.mean(avals)) if len(avals) else np.nan,
        "mean_b": float(np.mean(bvals)) if len(bvals) else np.nan,
        "cohens_d": np.nan, "rank_biserial": np.nan,
        "t": np.nan, "p_ttest": np.nan, "z_rs": np.nan, "p_rs": np.nan,
        "F": np.nan, "p_anova": np.nan,
    }
    if "ttest" in tests and len(avals) > 1 and len(bvals) > 1:
        t, p = ttest_ind(avals, bvals, equal_var=False, nan_policy="omit")
        out["t"], out["p_ttest"] = float(t), float(p)
        out["cohens_d"] = _cohens_d(avals, bvals)
    if "ranksums" in tests and len(avals) > 0 and len(bvals) > 0:
        z, p = ranksums(avals, bvals)
        out["z_rs"], out["p_rs"] = float(z), float(p)
        out["rank_biserial"] = _rank_biserial_from_ranksums(avals, bvals)
    if "anova" in tests and len(avals) > 1 and len(bvals) > 1:
        F, p = f_oneway(avals, bvals)
        out["F"], out["p_anova"] = float(F), float(p)
    return out

# ---------------- Main plot function ----------------

def plot_groupwise_bar(
    df: pd.DataFrame, 
    y: str = 'total_distance', 
    title: Optional[str] = None, 
    ylabel: Optional[str] = None,
    figsize: Tuple[int, int] = (6, 4), 
    plot_type: str = 'bar', 
    order: Optional[List[str]] = None,
    show_stats: bool = True, 
    show_points: bool = True,
    compare_to_first: bool = True,           # if False and k>2 you can still set pairwise='all'
    tests_to_show: Tuple[str, ...] = ("ranksums","ttest"),
    text_fontsize: int = 11, 
    pad_frac: float = 0.03,
    pairwise: str = 'vs_first',              # 'vs_first' | 'all' | 'none'
    fdr_correction: bool = False,            # Benjamini–Hochberg on displayed p-values
    annotate_mode: str = 'stars',            # 'stars' | 'exact' | 'both'
    show_nsizes: bool = True                 # print n per group under tick labels
):
    """
    Compare groups and annotate results. Returns (fig, ax, stats_df).

    stats_df columns:
        ['test', 'group_a', 'group_b', 'n_a','n_b','mean_a','mean_b',
         'cohens_d','rank_biserial','t','p_ttest','z_rs','p_rs','F','p_anova',
         'p_displayed','stars']
    """
    if y not in df.columns or 'group' not in df.columns:
        raise ValueError("DataFrame must contain columns: 'group' and the feature column.")
    if order is None:
        order = list(pd.unique(df['group']))
    df = df.copy()
    df['group'] = pd.Categorical(df['group'], categories=order, ordered=True)

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

    if show_points:
        sns.stripplot(
            data=df, x='group', y=y, order=order,
            dodge=False, alpha=0.5, size=4, ax=ax, color='k'
        )

    # Optional: show n under ticks
    if show_nsizes:
        ns = df.groupby('group')[y].apply(lambda s: s.dropna().size).reindex(order)
        ax.set_xticklabels([f"{g}\n(n={int(ns[g]) if pd.notna(ns[g]) else 0})" for g in order])

    # --- Build list of comparisons ---
    comps = []
    if pairwise == 'none' or not show_stats:
        comps = []
    elif pairwise == 'vs_first' or compare_to_first:
        if len(order) >= 2:
            for g in order[1:]:
                comps.append((order[0], g))
    elif pairwise == 'all':
        for i in range(len(order)):
            for j in range(i+1, len(order)):
                comps.append((order[i], order[j]))

    # --- Compute stats for each comparison ---
    stats_rows = []
    for a_lbl, b_lbl in comps:
        a_vals = df.loc[df['group'] == a_lbl, y]
        b_vals = df.loc[df['group'] == b_lbl, y]
        row = _pair_stats(a_vals, b_vals, tests=tests_to_show + (('anova',) if len(order) > 2 else ()))
        row.update({"group_a": a_lbl, "group_b": b_lbl})
        # choose a primary p to display
        p_candidates = [row.get('p_rs'), row.get('p_ttest')]
        p_show = next((p for p in p_candidates if isinstance(p, float) and not np.isnan(p)), np.nan)
        row['p_displayed'] = p_show
        row['stars'] = _p_to_star(p_show) if pd.notna(p_show) else 'n.a.'
        stats_rows.append(row)

    # Optional FDR on displayed p’s
    if fdr_correction and stats_rows:
        pvals = [r['p_displayed'] if pd.notna(r['p_displayed']) else 1.0 for r in stats_rows]
        padj = _bh_fdr(pvals)
        for r, q in zip(stats_rows, padj):
            r['p_displayed_fdr'] = q
            r['stars'] = _p_to_star(q)

    stats_df = pd.DataFrame(stats_rows, columns=[
        'group_a','group_b','n_a','n_b','mean_a','mean_b',
        'cohens_d','rank_biserial','t','p_ttest','z_rs','p_rs','F','p_anova',
        'p_displayed','stars','p_displayed_fdr'
    ]).fillna(value={'p_displayed_fdr': np.nan})

    # --- Annotations on the plot ---
    if show_stats and comps:
        ymin, ymax = ax.get_ylim()
        yspan = ymax - ymin
        base_pad = pad_frac * yspan
        line_sep = 0.9 * base_pad
        group_means = df.groupby('group', as_index=True)[y].mean()

        for (a_lbl, b_lbl), row in zip(comps, stats_rows):
            # place annotation above the higher of the two group means
            ai, bi = order.index(a_lbl), order.index(b_lbl)
            anchor = max(group_means.get(a_lbl, np.nan), group_means.get(b_lbl, np.nan))
            if np.isnan(anchor): 
                continue
            y_anchor = min(anchor + base_pad, ymax - base_pad)
            if annotate_mode in ('stars', 'both'):
                ax.text((ai+bi)/2, y_anchor, row['stars'], ha='center', va='bottom',
                        fontsize=text_fontsize, fontweight='bold')
            if annotate_mode in ('exact', 'both'):
                exact = []
                if not np.isnan(row.get('p_rs', np.nan)):
                    exact.append(f"RS p={row['p_rs']:.2e}")
                if not np.isnan(row.get('p_ttest', np.nan)):
                    exact.append(f"t={row['t']:.2f}, p={row['p_ttest']:.2e}")
                ax.text((ai+bi)/2, y_anchor + line_sep, "\n".join(exact),
                        ha='center', va='bottom', fontsize=max(text_fontsize-1, 8))

    ax.set_ylabel(ylabel if ylabel else y.replace('_', ' ').capitalize())
    ax.set_xlabel('')
    ax.set_title(title if title else f'{y.replace("_", " ").capitalize()} by Group', pad=12)
    fig.tight_layout()
    return fig, ax, stats_df
