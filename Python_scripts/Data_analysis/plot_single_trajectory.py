import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def plot_single_trajectory(conn, trial_id, bodypart_x='head_x_norm', bodypart_y='head_y_norm', 
                           label=None, color=None, style='line', max_points=None, 
                           color_by_time=True, ax=None):
    """
    Plot a trajectory (line or scatter) from the database, optionally subsampled and color-coded by time.

    Args:
        conn: psycopg2 or SQLAlchemy connection.
        trial_id: Integer ID of the trial in the database.
        bodypart_x: Name of x-coordinate column.
        bodypart_y: Name of y-coordinate column.
        label: Optional label for legend.
        color: Fixed color to use (ignored if color_by_time=True and style='scatter').
        style: 'line' or 'scatter' (default: 'line').
        max_points: Maximum number of points to plot (default: 1000).
        color_by_time: If True and style='scatter', colors points by time progression.
        ax: Optional matplotlib axis. Creates one if None.

    Returns:
        ax: The matplotlib axis with the plotted trajectory.
    """
    query = f"""
    SELECT {bodypart_x}, {bodypart_y}, video_name
    FROM dlc_table
    WHERE id = {trial_id}
    """
    df = pd.read_sql_query(query, conn)

    if df.empty:
        print(f"❌ No data found for ID {trial_id}")
        return ax

    try:
        x = np.array(df[bodypart_x][0])
        y = np.array(df[bodypart_y][0])
        video_name = df['video_name'][0]
    except Exception as e:
        print(f"⚠️ Error parsing data for ID {trial_id}: {e}")
        return ax

    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 5))

    ax.set_title(video_name)
    ax.invert_yaxis()
    ax.set_aspect('equal')

    # Downsample if needed
    if max_points is not None and len(x) > max_points:
        idx = np.linspace(0, len(x) - 1, max_points).astype(int)
        x, y = x[idx], y[idx]

    # Plotting
    if style == 'scatter':
        if color is not None or not color_by_time:
            # Fixed color scatter
            ax.scatter(x, y, s=2, label=label or f"ID {trial_id}", color=color)
        else:
            # Time-based gradient color scatter
            c = np.linspace(0, 1, len(x))  # normalized time
            sc = ax.scatter(x, y, c=c, cmap='viridis', s=2)
            plt.colorbar(sc, ax=ax, label='Progression')

    else:
        # Line plot
        ax.plot(x, y, label=label or f"ID {trial_id}", color=color)

    if label:
        ax.legend()

    return ax
