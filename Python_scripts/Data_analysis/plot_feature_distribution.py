def plot_feature_distribution(conn, *id_lists, feature='cumulative_distance',
                              group_labels=None, mode='pdf', ax=None):
    """
    Plots a distribution (PDF or CDF) for a given array-valued feature across groups.

    Parameters:
        conn: psycopg2 connection
        *id_lists: Variable number of ID lists
        feature (str): Array-valued column in dlc_table (e.g., 'cumulative_distance')
        group_labels (list): Optional group labels
        mode (str): 'pdf' (default) or 'cdf'
        ax: Optional matplotlib axis

    Returns:
        ax: Matplotlib axis with plotted distributions
    """
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from scipy.stats import gaussian_kde
    import matplotlib.cm as cm

    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 4))

    cmap = cm.get_cmap('tab10')
    colors = [cmap(i / max(1, len(id_lists) - 1)) for i in range(len(id_lists))]

    for i, id_list in enumerate(id_lists):
        query = f"""
        SELECT unnest({feature}) AS val
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
