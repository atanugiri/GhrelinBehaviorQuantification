def get_radial_distances(trial_id, conn, center=(0, 1), table='dlc_table', 
                         bodypart='Head', max_time=None, radius_limit=None):
    """
    Compute radial distances of a bodypart trajectory from the specified center.

    Args:
        trial_id: Trial ID
        conn: Database connection
        center: Tuple (x0, y0) center of maze (unit space)
        table: DB table name (used only to query frame_rate)
        bodypart: Bodypart name to track
        max_time: Time cutoff (in seconds)
        radius_limit: Optional max distance from center to include

    Returns:
        r: 1D numpy array of radial distances
    """

    from Python_scripts.Data_analysis.normalized_bodypart import get_normalized_bodypart
    from Python_scripts.Feature_functions.get_center_for_trial import get_center_for_trial
    import numpy as np
    import pandas as pd

    # Get normalized trajectory
    x, y = get_normalized_bodypart(
        trial_id=trial_id, 
        conn=conn, 
        bodypart=bodypart, 
        normalize=True, 
        interpolate=True
    )
    if x is None or y is None:
        return np.array([])

    # Get frame rate
    query = f"SELECT frame_rate FROM {table} WHERE id = %s;"
    df = pd.read_sql_query(query, conn, params=(trial_id,))
    if df.empty or pd.isna(df['frame_rate'][0]):
        print(f"[WARNING] Missing frame_rate for trial {trial_id}")
        return np.array([])
    frame_rate = df['frame_rate'][0]

    # Compute time array
    t = np.arange(len(x)) / frame_rate
    if max_time is not None:
        mask = t <= max_time
        x = x[mask]
        y = y[mask]

    # Compute distance from center
    traj = np.stack((x, y), axis=1)
    r = np.linalg.norm(traj - center, axis=1)

    if radius_limit is not None:
        r = r[r <= radius_limit]

    return r


def get_batch_radial_distances(id_list, conn, table='dlc_table', 
                               center=None, bodypart='Head', 
                               max_time=None, radius_limit=None):
    """
    Compute radial distances for multiple trials.

    Args:
        id_list: List of trial IDs
        conn: DB connection
        table: DB table name
        center: Fixed center tuple or None (if per-trial center)
        bodypart: Bodypart to use
        max_time: Optional time limit
        radius_limit: Optional radial cutoff

    Returns:
        List of 1D numpy arrays (one per trial)
    """
    all_r = []
    for trial_id in id_list:
        trial_center = get_center_for_trial(trial_id, conn, table) if center is None else center
        r = get_radial_distances(
            trial_id=trial_id,
            conn=conn,
            center=trial_center,
            table=table,
            bodypart=bodypart,
            max_time=max_time,
            radius_limit=radius_limit
        )
        all_r.append(r)
        
    return all_r
