def compute_binned_total_distance_by_group(
    conn, ids, group_label, bin_size=120, time_limit=1200):
    """
    Computes per-bin total distance per trial, then averages across trials per group.

    Returns:
        DataFrame: group, bin_index, mean_total_distance, sem_total_distance
    """
    import numpy as np
    import pandas as pd

    all_rows = []

    for id_ in ids:
        query = "SELECT t, distance FROM dlc_table WHERE id = %s;"
        df = pd.read_sql_query(query, conn, params=(id_,))
        if df.empty:
            continue

        t_vals = np.array(df['t'][0])
        distance = np.array(df['distance'][0])
        t_vals = t_vals[1:]  # align with distance

        num_bins = int(time_limit // bin_size)
        for i in range(num_bins):
            t_start = i * bin_size
            t_end = t_start + bin_size
            mask = (t_vals >= t_start) & (t_vals < t_end)
            total = np.sum(distance[mask]) if np.any(mask) else np.nan

            all_rows.append({
                'id': id_,
                'group': group_label,
                'bin_index': i,
                'total_distance': total
            })

    df_all = pd.DataFrame(all_rows)

    # Group-wise bin stats
    summary = df_all.groupby(['group', 'bin_index'])['total_distance'].agg(['mean', 'sem']).reset_index()
    summary = summary.rename(columns={'mean': 'mean_total_distance', 'sem': 'sem_total_distance'})
    return summary
