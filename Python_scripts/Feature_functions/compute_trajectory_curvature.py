import numpy as np
import pandas as pd
from scipy.ndimage import uniform_filter1d

def compute_trajectory_curvature(conn, id, bodypart_x='head_x_norm', bodypart_y='head_y_norm',
                                 time_limit=1200.0, smooth=True, window=5, speed_thresh=1e-2):
    """
    Compute curvature of the trajectory for a given trial ID from database.

    Parameters:
        conn: psycopg2 or SQLAlchemy connection object.
        id: Integer trial ID.
        bodypart_x, bodypart_y: Column names of x and y coordinates.
        time_limit: Only consider points with t <= time_limit.
        smooth: Whether to smooth x and y before computing curvature.
        window: Window size for moving average smoothing.
        speed_thresh: Curvature set to 0 where speed < this threshold.

    Returns:
        curvature: List of curvature values (NaN where undefined)
        mean_curv: Mean curvature over valid (non-NaN) values
    """
    
    query = f"""
    SELECT t, {bodypart_x}, {bodypart_y}
    FROM dlc_table
    WHERE id = {id};
    """
    df = pd.read_sql_query(query, conn)
    if df.empty:
        raise ValueError(f"No data for ID {id}")

    t_vals = np.array(df['t'][0])
    x_vals = np.array(df[bodypart_x][0])
    y_vals = np.array(df[bodypart_y][0])

    # Filter within [0, time_limit]
    mask = (t_vals >= 0) & (t_vals <= time_limit)
    t_vals = t_vals[mask]
    x_vals = x_vals[mask]
    y_vals = y_vals[mask]

    if len(t_vals) < 5:
        raise ValueError("Trajectory must have at least 5 points to compute curvature reliably.")

    # Optional smoothing
    if smooth:
        x_vals = uniform_filter1d(x_vals, size=window)
        y_vals = uniform_filter1d(y_vals, size=window)

    dx = np.gradient(x_vals, t_vals)
    dy = np.gradient(y_vals, t_vals)
    ddx = np.gradient(dx, t_vals)
    ddy = np.gradient(dy, t_vals)

    # Compute speed
    speed = np.sqrt(dx**2 + dy**2)

    # Curvature
    numerator = np.abs(dx * ddy - dy * ddx)
    denominator = (dx**2 + dy**2)**1.5

    with np.errstate(divide='ignore', invalid='ignore'):
        curvature = np.where(denominator != 0, numerator / denominator, np.nan)

    # Suppress curvature where speed is too low
    curvature[speed < speed_thresh] = 0

    # Summary stats
    valid = ~np.isnan(curvature)
    if np.any(valid):
        mean_curv = np.mean(curvature[valid])
    else:
        mean_curv = np.nan

    return curvature.astype(float).tolist(), float(mean_curv)
