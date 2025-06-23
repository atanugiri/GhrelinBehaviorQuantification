import numpy as np
import pandas as pd

def compute_motion_features(conn, id, bodypart_x='head_x_norm', bodypart_y='head_y_norm', 
                            time_limit=None, smooth=False, window=5):
    """
    Compute framewise distance, velocity, and acceleration arrays.

    Args:
        conn: psycopg2 or SQLAlchemy DB connection
        id (int): Trial ID
        bodypart_x (str): Column name for x-coordinate
        bodypart_y (str): Column name for y-coordinate
        time_limit (float): Upper bound on time values to analyze
        smooth (bool): Whether to smooth the coordinates before differentiation
        window (int): Window size for smoothing if enabled

    Returns:
        distance (list of float): Framewise distances
        velocity (list of float): Framewise velocities
        acceleration (list of float): Framewise accelerations
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

    if time_limit is not None:
        mask = (t_vals >= 0) & (t_vals <= time_limit)
        t_vals = t_vals[mask]
        x_vals = x_vals[mask]
        y_vals = y_vals[mask]

    if len(t_vals) < 3:
        raise ValueError(f"Not enough frames in time range for ID {id}")

    if smooth:
        from scipy.ndimage import uniform_filter1d
        x_vals = uniform_filter1d(x_vals, size=window)
        y_vals = uniform_filter1d(y_vals, size=window)

    dx = np.diff(x_vals)
    dy = np.diff(y_vals)
    dt = np.diff(t_vals)

    distance = np.sqrt(dx**2 + dy**2)
    velocity = np.divide(distance, dt, out=np.zeros_like(distance), where=dt != 0)

    # Acceleration from diff(velocity) / diff(time)
    dt2 = dt[1:]  # dt[i] corresponds to t_{i+1} - t_i
    acc = np.diff(velocity)
    acceleration = np.divide(acc, dt2, out=np.zeros_like(acc), where=dt2 != 0)

    # Round and convert to list
    distance = np.round(distance, 4).astype(float).tolist()
    velocity = np.round(velocity, 4).astype(float).tolist()
    acceleration = np.round(acceleration, 4).astype(float).tolist()

    return distance, velocity, acceleration
