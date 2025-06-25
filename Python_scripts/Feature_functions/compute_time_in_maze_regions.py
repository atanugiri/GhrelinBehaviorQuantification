import numpy as np
import pandas as pd

def compute_time_in_maze_regions(conn, trial_id, radius=0.1, bodypart_x='head_x_norm', bodypart_y='head_y_norm', plot_maze=False):
    """
    Compute time spent in each corner and the center of a square maze.

    Args:
        conn: psycopg2 or SQLAlchemy connection to database
        trial_id: int, trial ID in dlc_table
        radius: float, radius of each circular region (default = 0.1)
        bodypart_x: str, column name for x-coordinate (default = 'head_x_norm')
        bodypart_y: str, column name for y-coordinate (default = 'head_y_norm')
        plot_maze: bool, whether to show a visualization of maze regions and trajectory

    Returns:
        dict: {'corner_UL', 'corner_UR', 'corner_LL', 'corner_LR', 'center', 'total_corners'} with time (in sec)
    """
    query = f"""
        SELECT {bodypart_x}, {bodypart_y}, frame_rate
        FROM dlc_table
        WHERE id = {trial_id}
    """
    df = pd.read_sql_query(query, conn)

    x = np.array(df[bodypart_x][0])
    y = np.array(df[bodypart_y][0])
    fps = df['frame_rate'].iloc[0]
    dt = 1.0 / fps

    regions = {
        'corner_UL': (0.0, 0.0),
        'corner_UR': (1.0, 0.0),
        'corner_LL': (0.0, 1.0),
        'corner_LR': (1.0, 1.0),
        'center': (0.5, 0.5),
    }

    time_spent = {}
    total_corner_time = 0.0

    for label, (cx, cy) in regions.items():
        distance = np.sqrt((x - cx)**2 + (y - cy)**2)
        inside = distance <= radius
        seconds = np.sum(inside) * dt
        time_spent[label] = seconds

        if 'corner' in label:
            total_corner_time += seconds

    time_spent['total_corners'] = total_corner_time

    if plot_maze:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.plot(x, y, lw=1, alpha=0.6, label='Trajectory')

        for label, (cx, cy) in regions.items():
            circle = plt.Circle((cx, cy), radius, color='red' if 'corner' in label else 'blue',
                                fill=False, linestyle='--', label=label)
            ax.add_patch(circle)
            ax.text(cx, cy, label, fontsize=8, ha='center', va='center')

        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(1.1, -0.1)
        ax.set_aspect('equal')
        ax.set_title(f'Trial {trial_id}: Trajectory + Regions')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.show()

    return time_spent
