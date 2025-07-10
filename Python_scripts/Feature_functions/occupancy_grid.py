# occupancy_grid.py

import numpy as np
import pandas as pd

def compute_occupancy_grid(trial_id, conn, table='dlc_table', 
                           max_time=None, grid_size=10):
    """
    Compute normalized occupancy grid for a single trial.

    Parameters:
        trial_id (int): Trial ID.
        conn: DB connection.
        table (str): Table name with normalized DLC coordinates.
        max_time (float or None): Only include frames with t <= max_time.
        grid_size (int): Number of bins per axis (e.g., 10 -> 10x10 grid).

    Returns:
        grid (2D np.array): Normalized occupancy probability map (sum = 1),
                            or None if the trial is empty/invalid.
    """
    q = f"""SELECT head_x_norm, head_y_norm, frame_rate FROM {table} WHERE id = %s"""
    df = pd.read_sql_query(q, conn, params=(trial_id,))
    if df.empty:
        return None

    try:
        x = np.array(df['head_x_norm'][0])
        y = np.array(df['head_y_norm'][0])
        frame_rate = df['frame_rate'][0]
    except Exception as e:
        print(f"[DEBUG] Error in trial {trial_id}: {e}")
        return None

    # Compute timestamps
    t = np.arange(len(x)) / frame_rate
    if max_time is not None:
        mask = t <= max_time
        x, y = x[mask], y[mask]

    # Drop NaNs
    valid = (~np.isnan(x)) & (~np.isnan(y))
    x, y = x[valid], y[valid]
    if len(x) == 0:
        return None

    # 2D histogram
    grid, _, _ = np.histogram2d(x, y, bins=grid_size, range=[[0, 1], [0, 1]])
    grid = grid.T  # (rows = y, cols = x)
    total = grid.sum()

    return grid / total if total > 0 else None


def get_batch_occupancy_grids(id_list, conn, table='dlc_table', 
                              max_time=None, grid_size=10):
    """
    Compute and collect occupancy grids for a list of trial IDs.

    Parameters:
        id_list (list): List of trial IDs.
        conn: psycopg2 or SQLAlchemy connection.
        table (str): Table name in the database.
        max_time (float): Optional maximum time in seconds to include.
        grid_size (int): Number of bins along each axis.

    Returns:
        List of np.array occupancy grids (one per trial).
    """
    import numpy as np

    results = []
    for trial_id in id_list:
        grid = compute_occupancy_grid(trial_id, conn, table=table, max_time=max_time, grid_size=grid_size)
        if grid is not None:
            results.append(grid)
    return results

