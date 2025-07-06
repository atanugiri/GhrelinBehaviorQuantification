import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d

def detect_sparse_band(r_all, bins=200, smooth_sigma=2, threshold_frac=0.5,
                       search_range=(0.2, 0.8), plot=True):
    """
    Improved: only detects sparse band within a given radial search range.
    """
    hist, bin_edges = np.histogram(r_all, bins=bins, range=(0, 1), density=True)
    r_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    smoothed = gaussian_filter1d(hist, sigma=smooth_sigma)

    threshold = threshold_frac * np.max(smoothed)

    # Mask by search range
    mask = (r_centers >= search_range[0]) & (r_centers <= search_range[1])
    is_sparse = (smoothed < threshold) & mask

    from itertools import groupby
    from operator import itemgetter

    indices = np.where(is_sparse)[0]
    groups = []
    for k, g in groupby(enumerate(indices), lambda i: i[0] - i[1]):
        group = list(map(itemgetter(1), g))
        groups.append(group)

    if not groups:
        print("⚠️ No sparse region detected")
        return None

    widest = max(groups, key=lambda g: r_centers[g[-1]] - r_centers[g[0]])
    r_min = r_centers[widest[0]]
    r_max = r_centers[widest[-1]]

    if plot:
        plt.plot(r_centers, smoothed, label='Radial density')
        plt.axhline(threshold, color='gray', linestyle='--', label='Threshold')
        plt.axvspan(r_min, r_max, color='orange', alpha=0.3, label='Detected Sparse Band')
        plt.xlabel('Radial distance (r)')
        plt.ylabel('Density')
        plt.title('Detected Sparse Band')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    return (r_min, r_max)

