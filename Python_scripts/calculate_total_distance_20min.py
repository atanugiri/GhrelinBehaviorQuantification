import pandas as pd
import numpy as np

def calculate_total_distance_20min(filename, likelihood_threshold=0.9):
    """
    Calculates total distance traveled based on 'Head' x/y coordinates
    over the first 20 minutes of data, after filtering by likelihood.

    Parameters:
        filename (str): Path to the normalized CSV file.
        likelihood_threshold (float): Minimum likelihood to accept a point (default 0.9).

    Returns:
        total_distance (float or None): Total cumulative distance in first 20 minutes,
                                        or None if file could not be processed.
    """
    try:
        # Load CSV with MultiIndex
        df = pd.read_csv(filename, header=[0, 1])

        # Filter to first 20 minutes (s <= 1200)
        df_20min = df[df[('Unnamed: 1_level_0', 's')] <= 1200].copy()

        # Extract Head x, y, likelihood
        x = df_20min[('Head', 'x')].to_numpy()
        y = df_20min[('Head', 'y')].to_numpy()
        likelihood = df_20min[('Head', 'likelihood')].to_numpy()

        # Mask low likelihood points
        x[likelihood < likelihood_threshold] = np.nan
        y[likelihood < likelihood_threshold] = np.nan

        # Calculate frame-to-frame distance
        frame_distance = np.sqrt(np.diff(x)**2 + np.diff(y)**2)

        # Mask distances if NaN
        valid = ~np.isnan(frame_distance)
        frame_distance[~valid] = np.nan

        # Cumulative distance
        cumulative_distance = np.nancumsum(frame_distance)

        # Total distance = final cumulative distance value
        total_distance = cumulative_distance[-1] if len(cumulative_distance) > 0 else 0.0

        return total_distance

    except Exception as e:
        print(f"⚠️ Error processing {filename}: {e}")
        return None
