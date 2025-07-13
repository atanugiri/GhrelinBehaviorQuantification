from Python_scripts.Feature_functions.get_center_for_trial import get_center_for_trial

def get_radial_distances(trial_id, conn, center=(0, 1), table='dlc_table', max_time=None, radius_limit=None):
    import pandas as pd
    import numpy as np

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

    num_frames = len(x)
    t = np.round(np.arange(num_frames) / frame_rate, 3)

    if max_time is not None:
        mask = t <= max_time
        x = x[mask]
        y = y[mask]

    traj = np.stack((x, y), axis=1)
    r = np.linalg.norm(traj - center, axis=1)

    if radius_limit is not None:
        r = r[r <= radius_limit]

    return r


def get_batch_radial_distances(id_list, conn, table='dlc_table', center=None, max_time=None, radius_limit=None):
    import numpy as np
    from Python_scripts.Feature_functions.get_center_for_trial import get_center_for_trial

    all_r = []
    for trial_id in id_list:
        trial_center = get_center_for_trial(trial_id, conn, table) if center is None else center
        r = get_radial_distances(
            trial_id, conn, center=trial_center,
            table=table, max_time=max_time,
            radius_limit=radius_limit
        )
        all_r.append(r)
    return all_r
