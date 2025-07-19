import numpy as np
import pandas as pd
from scipy.stats import entropy
from Python_scripts.Feature_functions.get_center_for_trial import get_center_for_trial

def get_entropy_by_distance_to_center(trial_id, conn, center=None,
                                      bins=np.arange(0, 1.1, 0.1),
                                      table='dlc_table', max_time=None, grid_size=10):
    """
    Compute spatial entropy within distance bins from a task-specific center.

    Args:
        trial_id (int): Trial ID in the database.
        conn: Database connection (psycopg2 or SQLAlchemy).
        center (tuple): (x, y) coordinate of the stimulus (e.g., light/toy corner).
        bins (np.array): Bin edges for distance from center.
        table (str): Name of the database table.
        max_time (float): Optional max time (in seconds) to include.
        grid_size (int): Size of grid to compute entropy (e.g., 10 for 10x10).

    Returns:
        pd.DataFrame: ['trial_id', 'bin_start', 'bin_end', 'entropy']
    """

    if center is None:
        center = get_center_for_trial(trial_id, conn, table)
        
    q = f"SELECT head_x_norm, head_y_norm, frame_rate FROM {table} WHERE id = %s"
    df = pd.read_sql_query(q, conn, params=(trial_id,))
    if df.empty:
        return pd.DataFrame(columns=['trial_id', 'bin_start', 'bin_end', 'entropy'])

    try:
        x = np.array(df['head_x_norm'][0])
        y = np.array(df['head_y_norm'][0])
        frame_rate = df['frame_rate'][0]
    except Exception as e:
        print(f"[ERROR] Trial {trial_id}: {e}")
        return pd.DataFrame(columns=['trial_id', 'bin_start', 'bin_end', 'entropy'])

    t = np.arange(len(x)) / frame_rate
    if max_time is not None:
        mask = t <= max_time
        x = x[mask]
        y = y[mask]

    traj = np.stack((x, y), axis=1)
    dists = np.linalg.norm(traj - np.array(center), axis=1)

    rows = []
    for i in range(len(bins) - 1):
        bin_start, bin_end = bins[i], bins[i + 1]
        mask = (dists >= bin_start) & (dists < bin_end)
        sub_traj = traj[mask]

        if len(sub_traj) == 0:
            h = np.nan
        else:
            x_bins = np.clip((sub_traj[:, 0] * grid_size).astype(int), 0, grid_size - 1)
            y_bins = np.clip((sub_traj[:, 1] * grid_size).astype(int), 0, grid_size - 1)
            indices = x_bins + y_bins * grid_size
            counts = np.bincount(indices, minlength=grid_size ** 2)
            probs = counts / counts.sum()
            h = entropy(probs[probs > 0], base=2)

        rows.append({
            'trial_id': trial_id,
            'bin_start': bin_start,
            'bin_end': bin_end,
            'entropy': h
        })

    return pd.DataFrame(rows)


def get_batch_entropy_by_distance_to_center(id_list, conn, center=None,
                                            bins=np.arange(0, 1.1, 0.1),
                                            table='dlc_table',
                                            max_time=None,
                                            grid_size=10,
                                            group_label=None,
                                            verbose=False):
    """
    Compute entropy-by-distance for all trials in a list.

    Args:
        id_list (list): List of trial IDs.
        conn: Database connection.
        center (tuple): (x, y) of stimulus center for this task.
        bins (np.array): Distance bin edges.
        table (str): SQL table.
        max_time (float): Optional time limit.
        grid_size (int): Grid resolution.
        group_label (str): Optional 'Saline' or 'Ghrelin' label for grouping.
        verbose (bool): Print trial progress.

    Returns:
        pd.DataFrame: ['trial_id', 'bin_start', 'bin_end', 'entropy', 'group']
    """
    dfs = []
    for tid in id_list:
        if verbose:
            print(f"Processing trial {tid}")
        df = get_entropy_by_distance_to_center(
            trial_id=tid, conn=conn, center=center, bins=bins,
            table=table, max_time=max_time, grid_size=grid_size
        )
        if group_label is not None:
            df['group'] = group_label
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)
