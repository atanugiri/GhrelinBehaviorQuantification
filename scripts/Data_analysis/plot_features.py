"""
Exploratory plotting functions for feature visualization.
Combines barplot, distribution, and histogram/boxplot utilities.
"""

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


def plot_feature_barplot(conn, *id_lists, feature='distance', group_labels=None, ax=None):
    """
    Plots a bar plot for a given feature across multiple groups of IDs using a colormap.

    Parameters:
        conn: psycopg2 connection object to the database
        *id_lists: Variable number of ID lists, each representing a group
        feature (str): Column name in dlc_table to plot
        group_labels (list of str): Optional labels for each ID group
        ax (matplotlib axis): Optional axis to plot on

    Returns:
        ax: Matplotlib axis object for further customization
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 4))

    means, sems = [], []

    for id_list in id_lists:
        query = f"""
        SELECT {feature}
        FROM dlc_table
        WHERE id = ANY(%s) AND {feature} IS NOT NULL;
        """
        df = pd.read_sql_query(query, conn, params=(id_list,))
        values = df[feature].dropna().values
        means.append(values.mean() if len(values) > 0 else np.nan)
        sems.append(values.std(ddof=1) / np.sqrt(len(values)) if len(values) > 1 else np.nan)

    x = range(len(id_lists))

    # Use colormap to assign different colors
    cmap = cm.get_cmap('tab10')
    colors = [cmap(i / max(1, len(id_lists) - 1)) for i in range(len(id_lists))]

    ax.bar(x, means, yerr=sems, capsize=5, alpha=0.8, color=colors)

    if group_labels:
        ax.set_xticks(x)
        ax.set_xticklabels(group_labels)

    ax.set_ylabel(feature)

    return ax


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


def plot_feature_histogram_and_boxplot(conn, column_name, bins=50):
    """
    Plots a histogram and a box plot for a scalar feature column in the 'dlc_table'.

    Parameters:
        conn: psycopg2 connection object
        column_name (str): The name of the scalar column (e.g., 'mean_curv')
        bins (int): Number of histogram bins (default: 50)

    Returns:
        fig: Matplotlib Figure object
    """
    # Query non-null values
    query = f"""
    SELECT {column_name}
    FROM dlc_table
    WHERE {column_name} IS NOT NULL;
    """
    df = pd.read_sql_query(query, conn)

    if df.empty:
        raise ValueError(f"No non-null data found for column '{column_name}'.")

    # Convert to float array
    values = np.array([float(v) for v in df[column_name]])

    # Plotting
    fig, axes = plt.subplots(nrows=2, figsize=(6, 6), gridspec_kw={'height_ratios': [3, 1]})
    
    # Histogram
    axes[0].hist(values, bins=bins, color='steelblue', edgecolor='black')
    axes[0].set_title(f'Histogram of {column_name}')
    axes[0].set_ylabel('Count')
    
    # Box plot
    axes[1].boxplot(values, vert=False, patch_artist=True,
                    boxprops=dict(facecolor='skyblue'))
    axes[1].set_xlabel(column_name)
    axes[1].set_yticks([])

    plt.tight_layout()
    plt.show()
    # return fig
