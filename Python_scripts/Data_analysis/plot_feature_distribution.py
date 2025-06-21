def plot_feature_distribution(conn, *id_lists, feature='cumulative_distance',
                              group_labels=None, mode='pdf', ax=None):
    """
    Plots a distribution (PDF or CDF) for a given feature across groups of trials.

    Supports both array-valued (FLOAT[]) and scalar (FLOAT) columns.

    Parameters:
        conn: psycopg2 connection to PostgreSQL database
        *id_lists: Variable number of ID lists (one per group)
        feature (str): Name of the column to analyze
        group_labels (list): Optional list of labels for the groups
        mode (str): 'pdf' or 'cdf'
        ax: Optional matplotlib axis

    Returns:
        ax: The matplotlib axis with plotted distributions
    """
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from scipy.stats import gaussian_kde
    import matplotlib.cm as cm

    # --- Detect column type ---
    check_query = """
        SELECT data_type, udt_name
        FROM information_schema.columns
        WHERE table_name = 'dlc_table' AND column_name = %s;
    """
    col_info = pd.read_sql_query(check_query, conn, params=(feature,))
    if col_info.empty:
        raise ValueError(f"Column '{feature}' does not exist in 'dlc_table'.")
    is_array = col_info['data_type'].iloc[0] == 'ARRAY'

    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 4))

    cmap = cm.get_cmap('tab10')
    colors = [cmap(i / max(1, len(id_lists) - 1)) for i in range(len(id_lists))]

    for i, id_list in enumerate(id_lists):
        if is_array:
            query = f"""
            SELECT unnest({feature}) AS val
            FROM dlc_table
            WHERE id = ANY(%s) AND {feature} IS NOT NULL;
            """
        else:
            query = f"""
            SELECT {feature} AS val
            FROM dlc_table
            WHERE id = ANY(%s) AND {feature} IS NOT NULL;
            """
        df = pd.read_sql_query(query, conn, params=(id_list,))
        values = df['val'].dropna().values

        if len(values) < 2:
            continue

        label = group_labels[i] if group_labels and i < len(group_labels) else f'Group {i+1}'

        if mode == 'pdf':
            kde = gaussian_kde(values)
            x_vals = np.linspace(min(values), max(values), 200)
            y_vals = kde(x_vals)
            ax.plot(x_vals, y_vals, label=label, color=colors[i])
            ax.set_ylabel('Density')
        elif mode == 'cdf':
            sorted_vals = np.sort(values)
            cdf = np.linspace(0, 1, len(sorted_vals))
            ax.plot(sorted_vals, cdf, label=label, color=colors[i])
            ax.set_ylabel('Cumulative Probability')
        else:
            raise ValueError("mode must be 'pdf' or 'cdf'")

    ax.set_xlabel(feature)
    ax.set_title(f'{feature} {mode.upper()} by group')
    ax.legend()
    ax.grid(True)

    return ax
