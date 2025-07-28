import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from Python_scripts.Extract_db_columns.find_csv_for_video import find_csv_for_video

def plot_single_trajectory_from_csv(
    conn, trial_id, base_data_dir, bodyparts=['head'], 
    style='line', max_points=None, color_by_time=True,
    likelihood_threshold=0.4, ax=None
):
    """
    Plot trajectories for multiple bodyparts from the filtered DLC CSV.

    Args:
        conn: psycopg2 or SQLAlchemy connection.
        trial_id: Trial ID in database.
        bodyparts: List of bodypart base names (e.g., ['head', 'corner1']).
        style: 'line' or 'scatter'.
        max_points: Max number of points to plot per bodypart.
        color_by_time: Whether to color by time gradient (for scatter).
        likelihood_threshold: Filter points below this confidence.
        ax: Optional matplotlib axis.
    """
    # 1. Get video_name
    query = f"SELECT video_name FROM dlc_table WHERE id = {trial_id};"
    df = pd.read_sql_query(query, conn)
    if df.empty:
        print(f"❌ No video_name found for ID {trial_id}")
        return ax
    video_name = df['video_name'].iloc[0]

    # 2. Get CSV path
    csv_path = find_csv_for_video(video_name, base_data_dir)
    if not csv_path:
        print(f"❌ CSV not found for {video_name}")
        return ax

    # 3. Load CSV with multi-index
    try:
        df_dlc = pd.read_csv(csv_path, header=[1, 2])
    except Exception as e:
        print(f"⚠️ Failed to load CSV {csv_path}: {e}")
        return ax

    part_names = [col[0] for col in df_dlc.columns]
    part_map = {p.lower(): p for p in set(part_names)}

    # 4. Create plot
    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 5))

    ax.set_title(video_name)
    ax.invert_yaxis()
    ax.set_aspect('equal')

    # 5. Plot each bodypart
    for part in bodyparts:
        matched = part_map.get(part.lower())
        if matched is None:
            print(f"❌ Bodypart '{part}' not found in CSV: {csv_path}")
            continue

        try:
            x = df_dlc[(matched, 'x')]
            y = df_dlc[(matched, 'y')]
            p = df_dlc[(matched, 'likelihood')]
        except KeyError:
            print(f"❌ Missing x/y/likelihood for bodypart '{matched}'")
            continue

        # Filter and trim
        mask = p >= likelihood_threshold
        x = x[mask]
        y = y[mask]
        if max_points is not None:
            x = x.iloc[:max_points]
            y = y.iloc[:max_points]

        # Plot
        label = matched
        if style == 'scatter':
            if not color_by_time:
                ax.scatter(x, y, s=3, label=label)
            else:
                c = np.linspace(0, 1, len(x))
                sc = ax.scatter(x, y, c=c, cmap='viridis', s=3)
                plt.colorbar(sc, ax=ax, label='Progression')
        else:
            ax.plot(x, y, label=label)

    ax.legend()
    return ax
