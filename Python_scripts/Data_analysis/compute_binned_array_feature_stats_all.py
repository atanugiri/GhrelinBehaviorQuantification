def compute_binned_array_feature_stats_all(
    conn, ids, feature_name, group_label,
    time_limit=1200.0, bin_size=120, t_offset=1):
    """
    Compute per-trial, per-bin sum, mean, and mean absolute z-score of an array-valued feature.

    Args:
        conn: psycopg2 connection
        ids (list of int): Trial IDs
        feature_name (str): Array-valued column name (e.g., 'velocity', 'distance')
        group_label (str): Label for the group
        time_limit (float): Max time to consider (default 1200)
        bin_size (float): Width of each time bin (default 120)
        t_offset (int): Use 1 if feature is derived from np.diff (to align with time)

    Returns:
        pd.DataFrame: One row per (trial, bin) with sum, mean, and z-score stats
    """
    import numpy as np
    import pandas as pd

    all_rows = []

    for id_ in ids:
        query = f"SELECT t, {feature_name} FROM dlc_table WHERE id = %s;"
        df = pd.read_sql_query(query, conn, params=(id_,))
        if df.empty:
            continue

        t_vals = np.array(df['t'][0])
        feature_array = np.array(df[feature_name][0])

        if t_offset > 0:
            t_vals = t_vals[t_offset:]

        if len(t_vals) != len(feature_array):
            print(f"⚠️ Length mismatch for ID {id_}")
            continue

        num_bins = int(time_limit // bin_size)
        for i in range(num_bins):
            t_start = i * bin_size
            t_end = t_start + bin_size
            mask = (t_vals >= t_start) & (t_vals < t_end)
            segment = feature_array[mask]

            if len(segment) == 0:
                feature_sum = feature_mean = z_mean_abs = np.nan
            else:
                feature_sum = np.sum(segment)
                feature_mean = np.mean(segment)
                std = np.std(segment)
                z_mean_abs = np.mean(np.abs((segment - feature_mean) / std)) if std > 0 else 0.0

            all_rows.append({
                'id': id_,
                'bin_index': i,
                'group': group_label,
                f'{feature_name}_sum': feature_sum,
                f'{feature_name}_mean': feature_mean,
                f'{feature_name}_z_mean_abs': z_mean_abs
            })

    return pd.DataFrame(all_rows)
