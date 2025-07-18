import numpy as np
import pandas as pd
from scipy.stats import entropy

def get_spatial_entropy(trial_id, conn, table='dlc_table', grid_size=10, max_time=None, radius_limit=None):
    """
    Calculate spatial entropy of head position in unit square maze.
    
    Args:
        trial_id: Integer, trial ID in database.
        conn: psycopg2 or SQLAlchemy connection.
        table: Table name (default: 'dlc_table').
        grid_size: Grid resolution (e.g., 10 means 10x10 grid).
        max_time: Optional, max time in seconds.
        radius_limit: Optional, radial limit from center (e.g., 1.0).
        
    Returns:
        entropy_val: float, spatial entropy (base 2).
    """
    # Fetch normalized trajectory
    q = f"""SELECT head_x_norm, head_y_norm, frame_rate FROM {table} WHERE id = %s"""
    df = pd.read_sql_query(q, conn, params=(trial_id,))
    if df.empty:
        return np.nan

    try:
        x = np.array(df['head_x_norm'][0])
        y = np.array(df['head_y_norm'][0])
        frame_rate = df['frame_rate'][0]
    except Exception as e:
        print(f"[ERROR] Extraction failed for ID {trial_id}: {e}")
        return np.nan

    t = np.arange(len(x)) / frame_rate

    if max_time is not None:
        mask = t <= max_time
        x = x[mask]
        y = y[mask]

    if radius_limit is not None:
        # Use get_center_for_trial
        from Python_scripts.Feature_functions.get_center_for_trial import get_center_for_trial
        center = get_center_for_trial(trial_id, conn, table)
        r = np.linalg.norm(np.stack((x, y), axis=1) - center, axis=1)
        mask = r <= radius_limit
        x = x[mask]
        y = y[mask]

    # Discretize into grid bins
    x_bins = np.clip((x * grid_size).astype(int), 0, grid_size - 1)
    y_bins = np.clip((y * grid_size).astype(int), 0, grid_size - 1)
    indices = x_bins + y_bins * grid_size

    # Count visits to each bin
    counts = np.bincount(indices, minlength=grid_size**2)
    probs = counts / counts.sum()

    # Filter zero-prob bins to avoid log2(0)
    entropy_val = entropy(probs[probs > 0], base=2)
    return entropy_val


def get_batch_spatial_entropy_df(id_list, conn, table='dlc_table', grid_size=10, max_time=None, radius_limit=None, verbose=False):
    data = []
    for trial_id in id_list:
        if verbose:
            print(f"Processing trial {trial_id}")
        val = get_spatial_entropy(trial_id, conn, table, grid_size, max_time, radius_limit)
        data.append({'trial_id': trial_id, 'spatial_entropy': val})
    return pd.DataFrame(data)

