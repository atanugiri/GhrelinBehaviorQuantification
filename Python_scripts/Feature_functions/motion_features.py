import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
from psycopg2.extensions import connection as PGConnection


def compute_motion_features(conn: PGConnection, trial_id: int, 
                            bodypart_x: str = 'head_x_norm', 
                            bodypart_y: str = 'head_y_norm', 
                            time_limit: Optional[float] = None, 
                            smooth: bool = False, 
                            window: int = 5) -> Tuple[List[float], List[float], List[float]]:
    """
    Compute framewise motion features: distance, velocity, and acceleration.

    Args:
        conn: Active PostgreSQL database connection.
        trial_id: Integer ID of the trial.
        bodypart_x: Column name for x-coordinates.
        bodypart_y: Column name for y-coordinates.
        time_limit: Maximum time (in seconds) to include.
        smooth: Whether to apply smoothing to coordinates.
        window: Window size for smoothing.

    Returns:
        Tuple of (distance, velocity, acceleration), each a list of floats.

    Raises:
        ValueError: If data is missing, invalid, or too short for computation.
    """
    query = f"""
    SELECT {bodypart_x}, {bodypart_y}, frame_rate
    FROM dlc_table
    WHERE id = %s;
    """
    df = pd.read_sql_query(query, conn, params=(trial_id,))
    if df.empty:
        raise ValueError(f"No data found for trial ID {trial_id}")

    x_vals = np.array(df[bodypart_x][0])
    y_vals = np.array(df[bodypart_y][0])
    frame_rate = df['frame_rate'][0]

    if not isinstance(frame_rate, (int, float)) or frame_rate <= 0:
        raise ValueError(f"Invalid frame rate for ID {trial_id}")

    t_vals = np.arange(len(x_vals)) / frame_rate

    if time_limit is not None:
        mask = (t_vals >= 0) & (t_vals <= time_limit)
        if not np.any(mask):
            raise ValueError(f"No frames in time range for ID {trial_id}")
        x_vals = x_vals[mask]
        y_vals = y_vals[mask]
        t_vals = t_vals[mask]

    if len(t_vals) < 3:
        raise ValueError(f"Not enough valid frames for ID {trial_id}")

    if smooth:
        from scipy.ndimage import uniform_filter1d
        x_vals = uniform_filter1d(x_vals, size=window)
        y_vals = uniform_filter1d(y_vals, size=window)

    dx = np.diff(x_vals)
    dy = np.diff(y_vals)
    dt = np.diff(t_vals)

    distance = np.sqrt(dx**2 + dy**2)
    velocity = np.divide(distance, dt, out=np.zeros_like(distance), where=dt != 0)

    acc = np.diff(velocity)
    dt2 = dt[1:]
    acceleration = np.divide(acc, dt2, out=np.zeros_like(acc), where=dt2 != 0)

    return (
        np.round(distance, 4).tolist(),
        np.round(velocity, 4).tolist(),
        np.round(acceleration, 4).tolist()
    )


def batch_compute_motion_feature(
    conn: PGConnection, 
    trial_ids: List[int], 
    feature: str = 'distance',  # or 'velocity', 'acceleration'
    bodypart_x: str = 'head_x_norm', 
    bodypart_y: str = 'head_y_norm', 
    time_limit: Optional[float] = None, 
    smooth: bool = False, 
    window: int = 5
) -> List[np.ndarray]:
    """
    Compute a specified motion feature ('distance', 'velocity', 'acceleration') for a batch of trials.

    Returns:
        List of 1D numpy arrays corresponding to the chosen feature per trial.
    """
    assert feature in ['distance', 'velocity', 'acceleration'], "Invalid feature name"

    results = []
    for trial_id in trial_ids:
        try:
            dis, vel, acc = compute_motion_features(conn, trial_id, bodypart_x, bodypart_y, time_limit, smooth, window)
            feature_map = {'distance': dis, 'velocity': vel, 'acceleration': acc}
            results.append(np.array(feature_map[feature]))
        except Exception as e:
            print(f"⚠️ Skipping ID {trial_id}: {e}")
            continue
    return results
