import pandas as pd
import numpy as np
from scipy.stats import zscore
import os
import matplotlib.pyplot as plt

def calculate_acc_jerk_outliers(file_path, z_thresh=3, likelihood_thresh=0.9, plot=False):
    """
    Calculates acceleration and jerk outliers based on Head position in a DLC-normalized CSV.

    Parameters:
        file_path (str): Full path to the normalized CSV file.
        z_thresh (float): Z-score threshold for detecting outliers.
        likelihood_thresh (float): Likelihood threshold to filter low-confidence points.
        plot (bool): If True, show trajectory and mark acceleration outliers.

    Returns:
        acc_outliers_count (int): Number of acceleration outliers.
        jerk_outliers_count (int): Number of jerk outliers.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        df = pd.read_csv(file_path, header=[0, 1])

        # Filter to first 20 minutes (s <= 1200)
        df_20min = df[df[('Unnamed: 1_level_0', 's')] <= 1200].copy()

        # Extract Head x, y, likelihood
        x = df_20min[('Head', 'x')].to_numpy()
        y = df_20min[('Head', 'y')].to_numpy()
        likelihood = df_20min[('Head', 'likelihood')].to_numpy()

        # Apply likelihood threshold and NaN filtering
        mask = (likelihood >= likelihood_thresh) & ~np.isnan(x) & ~np.isnan(y)
        x = x[mask]
        y = y[mask]

        if len(x) < 5:
            return np.nan, np.nan

        pos = np.stack([x, y], axis=1)
        vel = np.gradient(pos, axis=0)
        acc = np.gradient(vel, axis=0)
        jerk = np.gradient(acc, axis=0)

        acc_mag = np.linalg.norm(acc, axis=1)
        jerk_mag = np.linalg.norm(jerk, axis=1)

        acc_z = zscore(acc_mag, nan_policy='omit')
        jerk_z = zscore(jerk_mag, nan_policy='omit')

        acc_outliers = np.where(np.abs(acc_z) > z_thresh)[0]
        jerk_outliers = np.where(np.abs(jerk_z) > z_thresh)[0]

        # Optional plot
        if plot:
            plt.figure(figsize=(8, 6))
            plt.plot(x, y, color='black', linewidth=1, label='Trajectory')
            if len(acc_outliers) > 0:
                plt.scatter(x[acc_outliers], y[acc_outliers], color='red', s=20, label='Acc Outliers')
            plt.xlabel('X position')
            plt.ylabel('Y position')
            plt.title('Trajectory with Acceleration Outliers')
            plt.legend()
            plt.axis('equal')
            plt.tight_layout()
            plt.show()

        return len(acc_outliers), len(jerk_outliers)

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return np.nan, np.nan
