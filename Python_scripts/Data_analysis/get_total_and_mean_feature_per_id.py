def get_total_and_mean_feature_per_id(
    conn, ids, group_label, feature_name='distance', max_time=None):
    """
    For each ID, compute total and mean of a given array-like feature (e.g., distance, velocity),
    optionally filtering to time <= max_time.

    Args:
        conn: Database connection object
        ids (list): List of trial IDs
        group_label (str): Group label to include in the output
        feature_name (str): Name of the feature column (e.g., 'distance', 'velocity')
        max_time (float or None): If provided, only include timepoints <= max_time

    Returns:
        pd.DataFrame: Columns = ['id', 'group', f'total_{feature_name}', f'mean_{feature_name}']
    """
    import pandas as pd
    import numpy as np

    results = []

    for id_ in ids:
        query = f"SELECT t, {feature_name} FROM dlc_table WHERE id = %s;"
        df = pd.read_sql_query(query, conn, params=(id_,))
        
        if df.empty:
            continue

        t_vals_raw = df['t'][0]
        feature_vals_raw = df[feature_name][0]

        if not isinstance(feature_vals_raw, (list, np.ndarray)) or len(feature_vals_raw) == 0:
            continue

        t_vals = np.array(t_vals_raw)
        feature_vals = np.array(feature_vals_raw)

        # Align time with feature if feature was computed from np.diff
        t_vals = t_vals[1:]

        if max_time is not None:
            mask = (t_vals <= max_time)
            feature_vals = feature_vals[mask]

        total = np.sum(feature_vals)
        
        if len(feature_vals) > 0:
            total_time = t_vals[-1] - t_vals[0]
            mean_val = total / total_time if total_time > 0 else np.nan
        else:
            mean_val = np.nan

        results.append({
            'id': id_,
            'group': group_label,
            f'total_{feature_name}': total,
            f'mean_{feature_name}': mean_val
        })

    return pd.DataFrame(results)
