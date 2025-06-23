def compute_binned_curvature_stats(
    conn, ids, group_label, bodypart_x='head_x_norm', bodypart_y='head_y_norm', 
    time_limit=1200.0, bin_size=120, smooth=True, window=11, speed_thresh=1e-2):
    """
    Computes curvature summaries for time bins within each trial.

    Returns:
        A long-format DataFrame with one row per (trial, bin).
    """
    import numpy as np
    import pandas as pd
    from scipy.ndimage import uniform_filter1d

    all_rows = []

    for id_ in ids:
        # Load trajectory
        query = f"""
        SELECT t, {bodypart_x}, {bodypart_y}
        FROM dlc_table
        WHERE id = %s;
        """
        df = pd.read_sql_query(query, conn, params=(id_,))
        if df.empty:
            continue

        t_vals = np.array(df['t'][0])
        x_vals = np.array(df[bodypart_x][0])
        y_vals = np.array(df[bodypart_y][0])

        if smooth:
            x_vals = uniform_filter1d(x_vals, size=window)
            y_vals = uniform_filter1d(y_vals, size=window)

        dx = np.gradient(x_vals, t_vals)
        dy = np.gradient(y_vals, t_vals)
        ddx = np.gradient(dx, t_vals)
        ddy = np.gradient(dy, t_vals)

        speed = np.sqrt(dx**2 + dy**2)
        numerator = np.abs(dx * ddy - dy * ddx)
        denominator = ((dx**2 + dy**2) + 1e-4) ** 1.5
        with np.errstate(divide='ignore', invalid='ignore'):
            curvature = np.where(denominator != 0, numerator / denominator, np.nan)
        curvature[speed < speed_thresh] = 0

        # Bin and compute stats
        num_bins = int(time_limit // bin_size)
        for i in range(num_bins):
            t_start = i * bin_size
            t_end = t_start + bin_size
            mask = (t_vals >= t_start) & (t_vals < t_end)
            curv_segment = curvature[mask]
            speed_segment = speed[mask]
            valid = (~np.isnan(curv_segment)) & (~np.isnan(speed_segment))
            
            curv_segment = curv_segment[valid]
            speed_segment = speed_segment[valid]
            
            if len(curv_segment) < 2:
                stats = [np.nan, np.nan]
            else:
                weighted_mean = np.average(curv_segment, weights=speed_segment)
                z = (curv_segment - np.mean(curv_segment)) / np.std(curv_segment)
                stats = [weighted_mean, np.mean(np.abs(z))]

            all_rows.append({
                'id': id_,
                'bin_index': i,
                'group': group_label,
                'curvature_mean': stats[0],
                'curvature_z_mean_abs': stats[1]
            })

    return pd.DataFrame(all_rows)
