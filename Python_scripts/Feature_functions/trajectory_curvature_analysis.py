import numpy as np
import pandas as pd
from scipy.ndimage import uniform_filter1d
from typing import Tuple, List
from psycopg2.extensions import connection as PGConnection


def compute_trajectory_curvature(conn: PGConnection,
                                 id: int,
                                 bodypart_x: str = 'head_x_norm',
                                 bodypart_y: str = 'head_y_norm',
                                 time_limit: float = 1200.0,
                                 smooth: bool = True,
                                 window: int = 5,
                                 speed_thresh: float = 1e-2) -> Tuple[List[float], float]:
    """
    Compute trajectory curvature for a given trial.

    Args:
        conn: Active PostgreSQL connection.
        id: Trial ID.
        bodypart_x: Name of x-coordinate column.
        bodypart_y: Name of y-coordinate column.
        time_limit: Only use data up to this time (seconds).
        smooth: If True, smooth coordinates before computing curvature.
        window: Smoothing window size (ignored if smooth=False).
        speed_thresh: Set curvature to 0 where speed < threshold.

    Returns:
        Tuple:
            curvature: List of per-frame curvature values (float, NaN where undefined).
            mean_curv: Mean of valid curvature values (float).
    """
    query = f"""
    SELECT {bodypart_x}, {bodypart_y}, frame_rate
    FROM dlc_table
    WHERE id = %s;
    """
    df = pd.read_sql_query(query, conn, params=(id,))
    x_vals = np.array(df[bodypart_x][0])
    y_vals = np.array(df[bodypart_y][0])
    frame_rate = df['frame_rate'].iloc[0]
    
    t_vals = np.arange(len(x_vals)) / frame_rate

    mask = (t_vals >= 0) & (t_vals <= time_limit)
    t_vals = t_vals[mask]
    x_vals = x_vals[mask]
    y_vals = y_vals[mask]

    if len(t_vals) < 5:
        raise ValueError(f"Not enough data points for ID {id}")

    if smooth:
        x_vals = uniform_filter1d(x_vals, size=window)
        y_vals = uniform_filter1d(y_vals, size=window)

    dx = np.gradient(x_vals, t_vals)
    dy = np.gradient(y_vals, t_vals)
    ddx = np.gradient(dx, t_vals)
    ddy = np.gradient(dy, t_vals)

    speed = np.sqrt(dx**2 + dy**2)
    numerator = np.abs(dx * ddy - dy * ddx)
    denominator = (dx**2 + dy**2)**1.5

    with np.errstate(divide='ignore', invalid='ignore'):
        curvature = np.where(denominator != 0, numerator / denominator, np.nan)

    curvature[speed < speed_thresh] = 0

    valid = ~np.isnan(curvature)
    mean_curv = np.mean(curvature[valid]) if np.any(valid) else np.nan

    return curvature.astype(float).tolist(), float(mean_curv)


def batch_trajectory_curvature(conn: PGConnection,
                               trial_ids: List[int],
                               bodypart_x: str = 'head_x_norm',
                               bodypart_y: str = 'head_y_norm',
                               time_limit: float = 1200.0,
                               smooth: bool = True,
                               window: int = 5,
                               speed_thresh: float = 1e-2) -> pd.DataFrame:
    """
    Compute mean curvature for a list of trial IDs.

    Args:
        conn: Active PostgreSQL connection.
        trial_ids: List of trial IDs to process.
        bodypart_x, bodypart_y: Coordinate columns.
        time_limit: Time cap for analysis.
        smooth: Whether to smooth trajectory.
        window: Smoothing window size.
        speed_thresh: Speed threshold to suppress curvature.

    Returns:
        DataFrame with columns ['id', 'mean_curvature']
    """
    results = []

    for trial_id in trial_ids:
        try:
            _, mean_curv = compute_trajectory_curvature(
                conn, trial_id,
                bodypart_x=bodypart_x,
                bodypart_y=bodypart_y,
                time_limit=time_limit,
                smooth=smooth,
                window=window,
                speed_thresh=speed_thresh
            )
            results.append({'id': trial_id, 'mean_curvature': mean_curv})
        except Exception as e:
            print(f"⚠️ Skipping ID {trial_id}: {e}")

    return pd.DataFrame(results)
