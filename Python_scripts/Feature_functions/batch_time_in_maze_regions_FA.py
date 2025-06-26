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
from compute_time_in_maze_regions_FA import compute_time_in_maze_regions_FA


def batch_time_in_maze_regions_FA(conn, trial_ids, radius=0.1):
    """
    Computes region-wise time spent in maze for a list of trial IDs.

    Args:
        conn: psycopg2 or SQLAlchemy database connection.
        trial_ids: list of int, trial IDs to process.
        radius: float, radius of circular region for each ROI.
    Returns:
        pd.DataFrame with one row per trial and columns for each region.
    """
    
    results = []

    for trial_id in trial_ids:
        try:
            time_spent = compute_time_in_maze_regions_FA(
                conn, trial_id, radius=0.1, bodypart_x='head_x_norm', 
                bodypart_y='head_y_norm', use_circle=False, return_fraction=True, plot_maze=False
            )
            time_spent['id'] = trial_id
            results.append(time_spent)
        except Exception as e:
            print(f"⚠️ Skipping trial {trial_id}: {e}")

    return pd.DataFrame(results)
