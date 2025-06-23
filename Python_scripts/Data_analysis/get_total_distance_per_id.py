def get_total_distance_per_id(conn, ids, group_label, max_time=None):
    """
    For each ID, compute total distance (sum of distance array),
    optionally filtering to time <= max_time.
    """
    import pandas as pd
    import numpy as np

    results = []

    for id_ in ids:
        query = "SELECT t, distance FROM dlc_table WHERE id = %s;"
        df = pd.read_sql_query(query, conn, params=(id_,))
        if df.empty:
            continue

        t_vals = np.array(df['t'][0])
        distance = np.array(df['distance'][0])

        # Align time with distance (from np.diff)
        t_vals = t_vals[1:]

        if max_time is not None:
            mask = (t_vals <= max_time)
            distance = distance[mask]

        total = np.sum(distance)

        results.append({'id': id_, 'group': group_label, 'total_distance': total})

    return pd.DataFrame(results)
