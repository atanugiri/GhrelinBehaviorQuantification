def get_radial_distances(trial_id, conn, center=(0, 1), table='dlc_table', max_time=None):
    import pandas as pd
    import numpy as np

    # Step 1: Get normalized coordinates and frame rate
    q = f"""SELECT head_x_norm, head_y_norm, frame_rate FROM {table} WHERE id = %s"""
    df = pd.read_sql_query(q, conn, params=(trial_id,))
    if df.empty:
        return np.array([])

    try:
        x = np.array(df['head_x_norm'][0])
        y = np.array(df['head_y_norm'][0])
        frame_rate = df['frame_rate'][0]
    except Exception as e:
        print(f"[DEBUG] Data extraction error: {e}")
        return np.array([])

    # Step 2: Compute t using frame_rate
    num_frames = len(x)
    t = np.round(np.arange(num_frames) / frame_rate, 3)

    # Step 3: Optionally filter by max_time
    if max_time is not None:
        mask = t <= max_time
        x = x[mask]
        y = y[mask]

    # Step 4: Compute radial distance
    traj = np.stack((x, y), axis=1)
    r = np.linalg.norm(traj - center, axis=1)
    return r

def get_batch_radial_distances(id_list, conn, table='dlc_table_temp', center=(0, 1), max_time=None):
    """
    Compute and collect radial distances for a list of trial IDs.

    Parameters:
        id_list (list): List of trial IDs.
        conn: psycopg2 or SQLAlchemy connection.
        table (str): Table name in the database.
        center (tuple): Center point for radial distance calculation.
        max_time (float): Optional maximum time in seconds to include.

    Returns:
        List of np.array radial distance vectors (one per trial).
    """
    import numpy as np

    results = []
    for trial_id in id_list:
        r = get_radial_distances(trial_id, conn, center=center, table=table, max_time=max_time)
        if len(r) > 0:
            results.append(r)
    return results
