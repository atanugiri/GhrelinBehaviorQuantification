import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import ks_2samp

def compare_radial_distributions(
        r1, r2,
        label1='Saline', label2='Ghrelin',
        bins=100, kind='pdf', return_data=False, compute_auc_split=True):
    """
    Compare two radial distributions using PDF or CDF with KS test and (optionally) AUC difference split.

    Parameters
    ----------
    r1, r2 : array-like
        1D arrays of radial distances.
    label1, label2 : str
        Labels for the two groups.
    bins : int
        Number of histogram bins.
    kind : str
        'pdf' or 'cdf' (default: 'pdf').
    return_data : bool
        Whether to return histogram, KS, and AUC data.
    compute_auc_split : bool
        If kind='cdf', compute AUC difference before and after intersection.

    Returns
    -------
    fig, ax : matplotlib Figure and Axes objects
    dict (optional) : if return_data=True
    """
    # Determine common range for both histograms
    hist_range = (min(r1.min(), r2.min()), max(r1.max(), r2.max()))

    fig, ax = plt.subplots(figsize=(8, 5))

    if kind == 'pdf':
        # Plot overlapping PDFs using histograms
        ax.hist(r1, bins=bins, range=hist_range, density=True, alpha=0.5, label=label1)
        ax.hist(r2, bins=bins, range=hist_range, density=True, alpha=0.5, label=label2)
        ylabel = 'Density'
        title = 'Radial Distribution (PDF)'
        x = None  # Not needed for KS or AUC here
        y1 = y2 = None

    elif kind == 'cdf':
        # Histogram counts
        counts1, bin_edges = np.histogram(r1, bins=bins, range=hist_range, density=True)
        counts2, _ = np.histogram(r2, bins=bins, range=hist_range, density=True)
        x = bin_edges[:-1] + np.diff(bin_edges) / 2
        dx = np.diff(bin_edges)[0]
        y1 = np.cumsum(counts1) * dx
        y2 = np.cumsum(counts2) * dx

        ax.plot(x, y1, label=label1)
        ax.plot(x, y2, label=label2)

        ylabel = 'Cumulative Probability'
        title = 'Radial Distribution (CDF)'

    else:
        raise ValueError("`kind` must be 'pdf' or 'cdf'")

    # KS Test
    ks_result = ks_2samp(r1, r2)
    ks_stat = ks_result.statistic
    ks_pval = ks_result.pvalue

    # AUC difference split (only relevant for CDF)
    x_intersect = None
    auc_diff_before = None
    auc_diff_after = None

    if kind == 'cdf' and compute_auc_split:
        diff = y1 - y2
        intersect_idx = np.where(np.diff(np.sign(diff)))[0]
        if len(intersect_idx) > 0:
            x_intersect = x[intersect_idx[0]]
            idx_before = np.where(x <= x_intersect)[0]
            idx_after = np.where(x > x_intersect)[0]

            if len(idx_before) > 1:
                y1_before = y1[idx_before[:-1]]
                y2_before = y2[idx_before[:-1]]
                dx_before = np.diff(x[idx_before])
                auc_diff_before = np.sum(np.abs(y1_before - y2_before) * dx_before)
            else:
                auc_diff_before = 0.0

            if len(idx_after) > 1:
                y1_after = y1[idx_after[:-1]]
                y2_after = y2[idx_after[:-1]]
                dx_after = np.diff(x[idx_after])
                auc_diff_after = np.sum(np.abs(y1_after - y2_after) * dx_after)
            else:
                auc_diff_after = 0.0

            # Optionally show vertical line
            # ax.axvline(x_intersect, color='gray', linestyle='--', label='Intersection')

    ax.set_xlabel('Radial distance from corner')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()

    if return_data:
        return fig, ax, {
            'x': x,
            'y1': y1, 'y2': y2,
            'ks_stat': ks_stat,
            'ks_pval': ks_pval,
            'x_intersect': x_intersect,
            'auc_diff_before': auc_diff_before,
            'auc_diff_after': auc_diff_after
        }
    else:
        return fig, ax
