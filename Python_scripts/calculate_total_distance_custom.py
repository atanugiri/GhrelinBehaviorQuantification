import pandas as pd
import numpy as np

def calculate_total_distance_custom(
    filename,
    body_part='Head',
    likelihood_threshold=0.9,
    max_seconds=1200
):
    """
    Calculates cumulative distance over time for a given body part within a time window,
    filtering low-likelihood points.

    Parameters:
        filename (str): Path to the normalized CSV file.
        body_part (str): Body part name (e.g., 'Head', 'Tailbase').
        likelihood_threshold (float): Likelihood threshold (default = 0.9).
        max_seconds (float): Time window in seconds (default = 1200 = 20 minutes).

    Returns:
        total_distance (float): Final cumulative distance value.
        cumulative_distance (np.ndarray): Array of cumulative distances over time.
    """
    try:
        df = pd.read_csv(filename, header=[0, 1])

        # Filter time
        if ('Unnamed: 1_level_0', 's') not in df.columns:
            raise ValueError("Timestamp column ('s') not found.")

        df_time_filtered = df[df[('Unnamed: 1_level_0', 's')] <= max_seconds].copy()

        # Check body part
        required_cols = [(body_part, 'x'), (body_part, 'y'), (body_part, 'likelihood')]
        if not all(col in df_time_filtered.columns for col in required_cols):
            raise ValueError(f"Body part '{body_part}' not found in CSV.")

        x = df_time_filtered[(body_part, 'x')].to_numpy()
        y = df_time_filtered[(body_part, 'y')].to_numpy()
        likelihood = df_time_filtered[(body_part, 'likelihood')].to_numpy()

        # Apply likelihood mask
        x[likelihood < likelihood_threshold] = np.nan
        y[likelihood < likelihood_threshold] = np.nan

        # Frame-to-frame distance
        frame_distance = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
        frame_distance[~np.isfinite(frame_distance)] = np.nan

        # Cumulative distance
        cumulative_distance = np.nancumsum(frame_distance)
        total_distance = cumulative_distance[-1] if len(cumulative_distance) > 0 else 0.0

        return total_distance, cumulative_distance

    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return None, None