import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def count_stopping_points(filename, likelihood_threshold=0.9, time_window=3.0,
                          max_displacement=0.1, plot=False):
    """
    Counts stopping points where movement < max_displacement in both x and y over a time_window.
    Optionally plots trajectory and detected stops.

    Parameters:
        filename (str): Path to the normalized CSV file.
        likelihood_threshold (float): Minimum likelihood to accept a point.
        time_window (float): Minimum time (in seconds) to consider for stopping.
        max_displacement (float): Max movement in both x and y to count as a stop.
        plot (bool): If True, plot trajectory and stop locations.

    Returns:
        int or None: Number of stopping points, or None if error occurs.
    """
    try:
        # Load DLC CSV with MultiIndex
        df = pd.read_csv(filename, header=[0, 1])
        
        # Filter to first 20 minutes (s <= 1200)
        df_20min = df[df[('Unnamed: 1_level_0', 's')] <= 1200].copy()

        # Extract relevant columns
        time = df_20min[('Unnamed: 1_level_0', 's')].to_numpy()
        x = df_20min[('Head', 'x')].to_numpy()
        y = df_20min[('Head', 'y')].to_numpy()
        likelihood = df_20min[('Head', 'likelihood')].to_numpy()

        # Mask low-confidence predictions
        valid = likelihood >= likelihood_threshold
        x[~valid] = np.nan
        y[~valid] = np.nan

        stop_count = 0
        stop_points = []  # to collect coordinates of stops for plotting
        i = 0
        n = len(time)

        while i < n:
            future_indices = np.where((time - time[i]) >= time_window)[0]
            future_indices = future_indices[future_indices > i]
            if len(future_indices) == 0:
                break
            j = future_indices[0]

            if not (np.isnan(x[i]) or np.isnan(x[j]) or np.isnan(y[i]) or np.isnan(y[j])):
                dx = abs(x[j] - x[i])
                dy = abs(y[j] - y[i])
                if dx < max_displacement and dy < max_displacement:
                    stop_count += 1
                    stop_points.append((x[i], y[i]))
                    i = j
                    continue

            i += 1

        # Plotting
        if plot:
            plt.figure(figsize=(6, 6))
            plt.plot(x, y, 'k-', linewidth=1, label="Trajectory")
            if stop_points:
                sx, sy = zip(*stop_points)
                plt.plot(sx, sy, 'ro', markersize=5, label="Stops")
            plt.xlabel("X Position")
            plt.ylabel("Y Position")
            plt.title(f"Trajectory with Stops (n={stop_count})")
            plt.axis("equal")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.show()

        return stop_count

    except Exception as e:
        print(f"❌ Error processing file {filename}: {e}")
        return None
