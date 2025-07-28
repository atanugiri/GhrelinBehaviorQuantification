import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def plot_single_trajectory_optogen(conn, trial_id, bodypart_x='head_x_norm', bodypart_y='head_y_norm', 
                                   label=None, color='red', style='line', max_points=None, 
                                   ax=None, error_level=0.1, introduce_nans=True, spike_chance=0.00):
    """
    Plot a trajectory from the database and inject artificial noise to simulate poor optogen data.

    Args:
        conn: psycopg2 or SQLAlchemy connection.
        trial_id: Integer ID of the trial in the database.
        bodypart_x, bodypart_y: Columns for x and y coordinates.
        label: Label for the plot.
        color: Line or scatter color.
        style: 'line' or 'scatter'.
        max_points: Number of points to plot (default: 1000).
        ax: Matplotlib axis.
        error_level: Std dev of Gaussian noise to add.
        introduce_nans: If True, randomly replace some points with NaN.
        spike_chance: Probability of inserting a huge spike at a point.

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

    # Truncate to max_points
    if max_points is not None and len(x) > max_points:
        x = x[:max_points]
        y = y[:max_points]

    # Inject noise
    noise_x = np.random.normal(0, error_level, size=len(x))
    noise_y = np.random.normal(0, error_level, size=len(y))
    x += noise_x
    y += noise_y

    # Introduce spikes and NaNs
    for i in range(len(x)):
        if introduce_nans and np.random.rand() < 0.01:
            x[i], y[i] = np.nan, np.nan
        elif np.random.rand() < spike_chance:
            x[i] += np.random.uniform(-10, 10)
            y[i] += np.random.uniform(-10, 10)

    # Plot
    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 5))

    ax.set_title(f"{video_name}")
    ax.invert_yaxis()
    ax.set_aspect('equal')

    if style == 'scatter':
        ax.scatter(x, y, s=2, label=label or f"ID {trial_id}", color=color)
    else:
        ax.plot(x, y, label=label or f"ID {trial_id}", color=color)

    if label:
        ax.legend()

    return ax
