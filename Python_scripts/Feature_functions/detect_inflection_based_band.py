import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d

def detect_inflection_based_band(r_all, bins=200, smooth_sigma=2, plot=True):
    hist, bin_edges = np.histogram(r_all, bins=bins, range=(0, 1), density=True)
    r_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    smoothed = gaussian_filter1d(hist, sigma=smooth_sigma)

    # First and second derivative
    d1 = np.gradient(smoothed)
    d2 = np.gradient(d1)

    # Find valley (min of smoothed)
    valley_idx = np.argmin(smoothed)
    r_valley = r_centers[valley_idx]

    # Find left & right peaks (uphill from valley)
    left_peak = np.argmax(smoothed[:valley_idx]) if valley_idx > 0 else None
    right_peak = np.argmax(smoothed[valley_idx:]) + valley_idx if valley_idx < len(smoothed)-1 else None

    r_left = r_centers[left_peak] if left_peak is not None else None
    r_right = r_centers[right_peak] if right_peak is not None else None

    if plot:
        plt.plot(r_centers, smoothed, label='Smoothed Density')
        plt.axvline(r_centers[valley_idx], linestyle='--', color='gray', label='Valley')
        if r_left is not None:
            plt.axvline(r_left, linestyle='--', color='blue', label='Left Peak')
        if r_right is not None:
            plt.axvline(r_right, linestyle='--', color='green', label='Right Peak')
        if r_left is not None and r_right is not None:
            plt.fill_between(r_centers, 0, smoothed,
                             where=(r_centers >= r_left) & (r_centers <= r_right),
                             color='orange', alpha=0.3, label='Sparse Band')
        plt.title('Inflection Point-Based Sparse Band Detection')
        plt.xlabel('Radial Distance')
        plt.ylabel('Density')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    if r_left is not None and r_right is not None:
        return (r_left, r_right, r_right - r_left)
    else:
        print("⚠️ Failed to detect both left and right peaks.")
        return (None, None, None)

