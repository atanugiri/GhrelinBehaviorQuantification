import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.signal import find_peaks
from sklearn.mixture import GaussianMixture


def project_onto_diagonal(id, conn, bodypart_x='head_x_norm', bodypart_y='head_y_norm',
                          p1=(0, 1), p2=(1, 0), table='dlc_table_temp'):
    """
    Fetch (x, y) list-columns for a given ID from the database and project
    them onto the diagonal from p1 to p2.

    Returns:
        1D NumPy array of projected positions.
    """
    import pandas as pd
    import numpy as np

    query = f"""
        SELECT {bodypart_x}, {bodypart_y}
        FROM {table}
        WHERE id = %s;
    """
    df = pd.read_sql_query(query, conn, params=(id,))

    if df.empty:
        print(f"⚠️ No data for ID {id}")
        return np.array([])

    try:
        x_vals = np.array(df[bodypart_x][0])
        y_vals = np.array(df[bodypart_y][0])
    except Exception as e:
        print(f"⚠️ Failed to extract arrays for ID {id}: {e}")
        return np.array([])

    if len(x_vals) != len(y_vals):
        print(f"⚠️ x and y arrays are unequal length for ID {id}")
        return np.array([])

    points = np.stack((x_vals, y_vals), axis=1)

    # Diagonal projection
    p1 = np.array(p1)
    p2 = np.array(p2)
    v = p2 - p1
    v = v / np.linalg.norm(v)
    projections = (points - p1) @ v

    return projections


def plot_projection_and_analyze(points, bins=200, smoothing=2):
    """
    Plots density of projected points along diagonal and detects sparse band width.
    """
    proj = project_onto_diagonal(points, p1=np.array([0,1]), p2=np.array([1,0]))
    
    # Histogram binning
    counts, edges = np.histogram(proj, bins=bins, density=True)
    centers = (edges[:-1] + edges[1:]) / 2

    # Smooth histogram
    kernel = np.ones(smoothing) / smoothing
    smoothed = np.convolve(counts, kernel, mode='same')

    # Peak & trough detection
    peak_indices, _ = find_peaks(smoothed)
    trough_indices, _ = find_peaks(-smoothed)

    result = None
    if len(peak_indices) >= 2 and len(trough_indices) >= 1:
        top_two = peak_indices[np.argsort(smoothed[peak_indices])[-2:]]
        left_peak, right_peak = np.sort(top_two)
        trough_candidates = [i for i in trough_indices if left_peak < i < right_peak]

        if trough_candidates:
            trough_idx = trough_candidates[np.argmin(smoothed[trough_candidates])]
            width = centers[right_peak] - centers[left_peak]

            result = {
                "left_peak_pos": centers[left_peak],
                "trough_pos": centers[trough_idx],
                "right_peak_pos": centers[right_peak],
                "band_width": width
            }

    # Plotting
    plt.figure(figsize=(6,4))
    plt.plot(centers, smoothed, label='Smoothed density', color='slateblue')
    if result:
        plt.axvline(result["left_peak_pos"], color='green', linestyle='--', label='Left peak')
        plt.axvline(result["trough_pos"], color='red', linestyle='--', label='Trough')
        plt.axvline(result["right_peak_pos"], color='green', linestyle='--', label='Right peak')
    plt.xlabel("Projected position along diagonal (0,1) → (1,0)")
    plt.ylabel("Density")
    plt.title("Peak–Trough–Peak Analysis of Diagonal Occupancy")
    plt.legend()
    plt.grid(True)
    plt.show()

    return result


def fit_and_plot_gmm_overlay(projections, result=None, n_components=2):
    """
    Fits a GMM to the 1D projected data and overlays it on the existing histogram/density.
    """
    # Fit GMM
    gmm = GaussianMixture(n_components=n_components, random_state=0)
    gmm.fit(projections.reshape(-1, 1))
    means = np.sort(gmm.means_.flatten())
    stds = np.sqrt(gmm.covariances_.flatten())
    weights = gmm.weights_

    # Plot the histogram
    counts, bins = np.histogram(projections, bins=200, density=True)
    centers = (bins[:-1] + bins[1:]) / 2
    plt.figure(figsize=(6,4))
    plt.plot(centers, counts, label='Histogram density', color='gray', alpha=0.4)

    # Plot each Gaussian component
    x = np.linspace(min(projections), max(projections), 500)
    for i in range(n_components):
        y = weights[i] * (1 / (stds[i] * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - means[i]) / stds[i])**2)
        plt.plot(x, y, label=f'Gaussian {i+1}', linestyle='--')

    # Plot total GMM density
    gmm_density = np.exp(gmm.score_samples(x.reshape(-1, 1)))
    plt.plot(x, gmm_density, color='black', label='GMM fit', linewidth=2)

    # Optionally show PTP peaks
    if result:
        plt.axvline(result["left_peak_pos"], color='green', linestyle='--', label='PTP left peak')
        plt.axvline(result["trough_pos"], color='red', linestyle='--', label='PTP trough')
        plt.axvline(result["right_peak_pos"], color='green', linestyle='--', label='PTP right peak')

    plt.title("GMM Fit vs. Peak–Trough–Peak Overlay")
    plt.xlabel("Projected position along diagonal")
    plt.ylabel("Density")
    plt.legend()
    plt.grid(True)
    plt.show()

    return {
        "gmm_means": means,
        "gmm_width": means[1] - means[0]
    }
