import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def plot_single_trajectory(ax, conn, trial_id, bodypart_x='head_x_norm', bodypart_y='head_y_norm', 
                           label=None, title=None, color=None):
    """
    Plot a single trajectory from the database on a given matplotlib axis.

    Args:
        ax: matplotlib.axes.Axes object to plot on.
        conn: Active psycopg2 or SQLAlchemy connection.
        trial_id: Integer ID of the trial in the database.
        bodypart_x: Column name for x-coordinates (default: 'head_x_norm').
        bodypart_y: Column name for y-coordinates (default: 'head_y_norm').
        label: Optional label for the legend.
        title: Optional title for the subplot.
        color: Optional matplotlib color.

    Returns:
        ax: The modified matplotlib axis.
    """
    query = f"""
    SELECT {bodypart_x}, {bodypart_y}
    FROM dlc_table
    WHERE id = {trial_id}
    """
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        print(f"No data found for ID {trial_id}")
        return ax

    try:
        x = np.array(df[bodypart_x][0])
        y = np.array(df[bodypart_y][0])
    except Exception as e:
        print(f"Error parsing trajectory for ID {trial_id}: {e}")
        return ax

    ax.plot(x, y, label=label or f"ID {trial_id}", color=color)
    ax.invert_yaxis()
    ax.set_aspect('equal')

    if title:
        ax.set_title(title)
    if label:
        ax.legend()

    return ax
