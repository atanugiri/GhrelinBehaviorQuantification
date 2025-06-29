import sys
import os
import pandas as pd

# Step 1: Construct full path to Feature_functions
feature_path = os.path.abspath(
    os.path.join(os.getcwd(), "..", "Python_scripts", "Feature_functions")
)

# Step 2: Append to sys.path if not already there
if feature_path not in sys.path:
    sys.path.append(feature_path)

# Step 3: Import the function
from compute_radial_zone_distribution import compute_radial_zone_distribution

def batch_radial_zone_distribution(conn, trial_ids,
                                   bodypart_x='head_x_norm', bodypart_y='head_y_norm',
                                   center=(0.0, 1.0), max_radius=1.0, n_bins=10,
                                   return_fraction=True, plot=False):
    """
    Run compute_radial_zone_distribution over a list of trial IDs.

    Args:
        conn: database connection
        trial_ids: list of int, trial IDs to analyze
        bodypart_x, bodypart_y: coordinate columns
        center: point to measure radial distance from (default: corner_LL)
        max_radius: outermost radius considered
        n_bins: number of radial bins (equal width)
        return_fraction: True for fraction of time, False for seconds
        plot: show barplot for each trial (usually False for batch)

    Returns:
        DataFrame: one row per trial, columns = radial bins, plus 'id'
    """
    from compute_radial_zone_distribution import compute_radial_zone_distribution

    all_results = []

    for trial_id in trial_ids:
        try:
            # Compute distribution for one trial
            series = compute_radial_zone_distribution(
                conn,
                trial_id,
                bodypart_x=bodypart_x,
                bodypart_y=bodypart_y,
                center=center,
                max_radius=max_radius,
                n_bins=n_bins,
                return_fraction=return_fraction,
                plot=plot  # optional for debugging
            )

            # Convert Series to dictionary, add trial ID
            result = series.to_dict()
            result['id'] = trial_id

            all_results.append(result)

        except Exception as e:
            print(f"⚠️ Skipping trial {trial_id}: {e}")

    # Combine all trial results into one DataFrame
    return pd.DataFrame(all_results)
