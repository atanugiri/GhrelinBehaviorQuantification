import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import pandas as pd

def plot_feature_barplot(conn, *id_lists, feature='distance', group_labels=None, ax=None):
    """
    Plots a bar plot for a given feature across multiple groups of IDs using a colormap.

    Parameters:
        conn: psycopg2 connection object to the database
        *id_lists: Variable number of ID lists, each representing a group
        feature (str): Column name in dlc_table to plot
        group_labels (list of str): Optional labels for each ID group
        colormap (str): Name of matplotlib colormap (default: 'tab10')
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
