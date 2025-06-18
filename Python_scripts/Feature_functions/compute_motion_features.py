import numpy as np
import pandas as pd

def compute_motion_features(conn, id, bodypart_x='head_x_norm', bodypart_y='head_y_norm', time_limit=480.0):
    """
    Compute total distance, average velocity, and cumulative distance array
    from body part coordinates and time stored as arrays.

    Args:
        conn: psycopg2 or SQLAlchemy DB connection
        id (int): Trial ID
        bodypart_x (str): Column name for x-coordinate
        bodypart_y (str): Column name for y-coordinate
        time_limit (float): Upper bound on time values to analyze

    Returns:
        total_distance (float): Total path length over [0, time_limit]
        average_velocity (float): Mean velocity over time
        cumulative_distance (np.ndarray): Array of cumulative distances
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

    if len(t_vals) < 2:
        raise ValueError(f"Not enough frames in time range for ID {id}")

    dx = np.diff(x_vals)
    dy = np.diff(y_vals)
    dt = np.diff(t_vals)

    distance = np.sqrt(dx**2 + dy**2)
    total_distance = np.sum(distance)
    
    velocity = np.divide(distance, dt, out=np.zeros_like(distance), where=dt != 0)
    average_velocity = np.mean(velocity)

    cumulative_distance = np.cumsum(np.insert(distance, 0, 0))

    return total_distance, average_velocity, cumulative_distance
