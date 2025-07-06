def get_radial_distances(trial_id, conn, center=(0, 1), table='dlc_table_temp'):
    import pandas as pd
    import numpy as np

    q = f"""SELECT head_x_norm, head_y_norm FROM {table} WHERE id = %s"""
    df = pd.read_sql_query(q, conn, params=(trial_id,))
    if df.empty:
        return np.array([])

    try:
        x = np.array(df['head_x_norm'][0])
        y = np.array(df['head_y_norm'][0])
    except:
        return np.array([])

    traj = np.stack((x, y), axis=1)
    r = np.linalg.norm(traj - center, axis=1)
    return r
