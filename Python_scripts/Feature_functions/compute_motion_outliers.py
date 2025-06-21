import numpy as np
import pandas as pd
from scipy.signal import medfilt

def compute_motion_outliers(conn, id, bodypart_x='head_x_norm', bodypart_y='head_y_norm', time_limit=1200.0):
    """
    Compute motion outliers based on acceleration and jerk using moving median method.

    Returns:
        acc_outlier_count (int): Number of acceleration outliers
        jerk_outlier_count (int): Number of jerk outliers
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

    # Filter by time limit
    mask = (t_vals >= 0) & (t_vals <= time_limit)
    t_vals = t_vals[mask]
    x_vals = x_vals[mask]
    y_vals = y_vals[mask]

    if len(t_vals) < 3:
        raise ValueError(f"Not enough frames for acceleration/jerk computation for ID {id}")

    dt = np.diff(t_vals)
    dx = np.diff(x_vals)
    dy = np.diff(y_vals)
    distance = np.sqrt(dx**2 + dy**2)
    velocity = np.divide(distance, dt, out=np.zeros_like(distance), where=dt != 0)

    # Acceleration
    dt_mid = (dt[:-1] + dt[1:]) / 2  # midpoint time intervals for acceleration
    acc = np.diff(velocity) / dt_mid

    # Jerk
    dt_jerk = (dt_mid[:-1] + dt_mid[1:]) / 2
    jerk = np.diff(acc) / dt_jerk

    # Detect outliers using movmedian window size = 5
    def count_movmedian_outliers(arr, window=5):
        arr = np.asarray(arr)
        if len(arr) < window:
            return 0
        med = medfilt(arr, kernel_size=window)
        deviation = np.abs(arr - med)
        mad = np.median(deviation)
        threshold = 3 * mad if mad != 0 else 0.001
        return int(np.sum(deviation > threshold))

    acc_outliers = count_movmedian_outliers(acc, window=5)
    jerk_outliers = count_movmedian_outliers(jerk, window=5)

    return acc_outliers, jerk_outliers
