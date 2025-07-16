import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from Python_scripts.Extract_db_columns.find_csv_for_video import find_csv_for_video

def plot_single_trajectory_from_csv(conn, trial_id,
                                    bodypart_x='head_x', bodypart_y='head_y',
                                    label=None, color=None, style='line',
                                    max_points=None, color_by_time=True,
                                    likelihood_threshold=0.4, ax=None):
    """
    Plot a trajectory from the filtered DLC CSV using specified bodypart (case-insensitive).

    Args:
        conn: psycopg2 or SQLAlchemy connection.
        trial_id: Trial ID in database.
        bodypart_x: Column name like 'head_x'.
        bodypart_y: Column name like 'head_y'.
        label: Label for legend.
        color: Line or scatter color.
        style: 'line' or 'scatter'.
        max_points: Max number of points to plot.
        color_by_time: Whether to color by time gradient (for scatter).
        likelihood_threshold: Filter points below this confidence.
        ax: Optional matplotlib axis.
    """
    # 1. Extract base bodypart name (e.g., 'head' from 'head_x')
    base_part = bodypart_x.lower().split('_')[0]

    # 2. Get video_name
    query = f"SELECT video_name FROM dlc_table WHERE id = {trial_id};"
    df = pd.read_sql_query(query, conn)
    if df.empty:
        print(f"❌ No video_name found for ID {trial_id}")
        return ax
    video_name = df['video_name'].iloc[0]

    # 3. Get CSV path
    csv_path = find_csv_for_video(video_name)
    if not csv_path:
        print(f"❌ CSV not found for {video_name}")
        return ax

    # 4. Load CSV
    try:
        df_dlc = pd.read_csv(csv_path, header=[1, 2])
    except Exception as e:
        print(f"⚠️ Failed to load CSV {csv_path}: {e}")
        return ax

    # 5. Find matching bodypart column (case-insensitive)
    part_names = [col[0] for col in df_dlc.columns]
    part_map = {p.lower(): p for p in set(part_names)}
    matched = part_map.get(base_part)
    if matched is None:
        print(f"❌ Bodypart '{base_part}' not found in CSV: {csv_path}")
        return ax

    try:
        x = df_dlc[(matched, 'x')]
        y = df_dlc[(matched, 'y')]
        p = df_dlc[(matched, 'likelihood')]
    except KeyError:
        print(f"❌ Missing x/y/likelihood for bodypart '{matched}' in CSV")
        return ax

    # 6. Apply likelihood threshold
    mask = p >= likelihood_threshold
    x = x[mask]
    y = y[mask]

    # 7. Limit points if needed
    if max_points is not None:
        x = x.iloc[:max_points]
        y = y.iloc[:max_points]

    # 8. Plotting
    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 5))

    ax.set_title(video_name)
    ax.invert_yaxis()
    ax.set_aspect('equal')

    if style == 'scatter':
        if color is not None or not color_by_time:
            ax.scatter(x, y, s=2, label=label or f"ID {trial_id}", color=color)
        else:
            c = np.linspace(0, 1, len(x))
            sc = ax.scatter(x, y, c=c, cmap='viridis', s=2)
            plt.colorbar(sc, ax=ax, label='Progression')
    else:
        ax.plot(x, y, label=label or f"ID {trial_id}", color=color)

    if label:
        ax.legend()

    return ax
