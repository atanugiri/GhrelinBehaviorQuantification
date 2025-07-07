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
    dict or None
        Returns a dict with histogram/CDF and KS results (and AUCs if applicable), or None if return_data is False.
    """
    # Common range and binning
    hist_range = (min(r1.min(), r2.min()), max(r1.max(), r2.max()))
    counts1, bin_edges = np.histogram(r1, bins=bins, range=hist_range, density=True)
    counts2, _ = np.histogram(r2, bins=bins, range=hist_range, density=True)
    x = bin_edges[:-1] + np.diff(bin_edges)/2

    # Compute PDF or CDF
    if kind == 'pdf':
        y1 = counts1
        y2 = counts2
        ylabel = 'Density'
        title = 'Radial Distribution (PDF)'
    elif kind == 'cdf':
        dx = np.diff(bin_edges)[0]
        y1 = np.cumsum(counts1) * dx
        y2 = np.cumsum(counts2) * dx
        ylabel = 'Cumulative Probability'
        title = 'Radial Distribution (CDF)'
    else:
        raise ValueError("`kind` must be 'pdf' or 'cdf'")

    # Plot
    plt.figure(figsize=(8, 5))
    plt.plot(x, y1, label=label1)
    plt.plot(x, y2, label=label2)

    # KS Test
    ks_result = ks_2samp(r1, r2)
    ks_stat = ks_result.statistic
    ks_pval = ks_result.pvalue

    # AUC difference before and after intersection (for CDF only)
    x_intersect = None
    auc_diff_before = None
    auc_diff_after = None

    if kind == 'cdf' and compute_auc_split:
        diff = y1 - y2
        intersect_idx = np.where(np.diff(np.sign(diff)))[0]
        if len(intersect_idx) > 0:
            x_intersect = x[intersect_idx[0]]
            idx_before = x <= x_intersect
            idx_after = x > x_intersect
            # Convert boolean masks to integer indices
            idx_before = np.where(x <= x_intersect)[0]
            idx_after = np.where(x > x_intersect)[0]
            
            # For area calculation, we must drop the last point to match dx length
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


            plt.axvline(x_intersect, color='gray', linestyle='--', label='Intersection')

    plt.xlabel('Radial distance from light')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Return useful data
    if return_data:
        return {
            'x': x,
            'y1': y1, 'y2': y2,
            'ks_stat': ks_stat,
            'ks_pval': ks_pval,
            'x_intersect': x_intersect,
            'auc_diff_before': auc_diff_before,
            'auc_diff_after': auc_diff_after
        }
