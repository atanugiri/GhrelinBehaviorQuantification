import numpy as np
import pandas as pd
from scipy.stats import entropy
from Python_scripts.Feature_functions.get_center_for_trial import get_center_for_trial

def get_entropy_by_distance_to_center(trial_id, conn, center=None,
                                      bins=np.arange(0, 1.1, 0.1),
                                      table='dlc_table', max_time=None,
                                      grid_size=10, normalize=False):
    """
    Compute (optionally normalized) spatial entropy within distance bins from a task-specific center.

    Args:
        trial_id (int): Trial ID in the database.
        conn: Database connection.
        center (tuple or None): (x, y) coordinate of stimulus; if None, inferred from trial.
        bins (np.array): Bin edges for distance from center.
        table (str): SQL table.
        max_time (float): Optional max time (in seconds).
        grid_size (int): Grid resolution (e.g., 10 for 10x10 grid).
        normalize (bool): If True, normalize entropy by max entropy for occupied cells.

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
            occupied_cells = np.count_nonzero(probs)

            if occupied_cells > 1:
                h_raw = entropy(probs[probs > 0], base=2)
                h_max = np.log2(occupied_cells)
                h = h_raw / h_max if normalize else h_raw
            else:
                h = 0.0

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
                                            normalize=False,
                                            group_label=None,
                                            verbose=False):
    """
    Compute (optionally normalized) entropy-by-distance for all trials in a list.

    Args:
        id_list (list): Trial IDs.
        conn: Database connection.
        center (tuple or None): (x, y) stimulus center or None to auto-detect.
        bins (np.array): Distance bin edges.
        table (str): SQL table name.
        max_time (float): Optional max time (s).
        grid_size (int): Grid resolution.
        normalize (bool): Whether to normalize entropy per bin.
        group_label (str): Optional label (e.g., 'Saline' or 'Ghrelin').
        verbose (bool): Print progress.

    Returns:
        pd.DataFrame: ['trial_id', 'bin_start', 'bin_end', 'entropy', 'group']
    """
    dfs = []
    for tid in id_list:
        if verbose:
            print(f"Processing trial {tid}")
        df = get_entropy_by_distance_to_center(
            trial_id=tid, conn=conn, center=center, bins=bins,
            table=table, max_time=max_time, grid_size=grid_size,
            normalize=normalize
        )
        if group_label is not None:
            df['group'] = group_label
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)
