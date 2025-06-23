def compute_binned_array_feature_stats(
    conn, ids, feature_name, group_label, time_limit=1200.0, bin_size=120, zscore=True, t_offset=1):
    """
    Compute binned statistics (mean and z-score mean abs) for a given array-valued feature.

    Args:
        conn: psycopg2 connection
        ids (list of int): Trial IDs
        feature_name (str): Name of array-valued column (e.g., 'velocity', 'curvature')
        group_label (str): Label for the group (for plotting/grouping)
        time_limit (float): Max time to include
        bin_size (float): Bin width
        zscore (bool): Whether to compute z-score mean absolute
        t_offset (int): Time alignment offset; use 1 if feature is from np.diff

    Returns:
        DataFrame: One row per (trial, bin)
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

            if len(segment) < 2:
                mean_val = np.nan
                z_mean_abs = np.nan
            else:
                mean_val = np.mean(segment)
                z_mean_abs = np.mean(np.abs((segment - np.mean(segment)) / np.std(segment))) if zscore else np.nan

            all_rows.append({
                'id': id_,
                'bin_index': i,
                'group': group_label,
                f'{feature_name}_mean': mean_val,
                f'{feature_name}_z_mean_abs': z_mean_abs
            })

    return pd.DataFrame(all_rows)
