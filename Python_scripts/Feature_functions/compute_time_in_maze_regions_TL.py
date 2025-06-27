import numpy as np
import pandas as pd

def compute_time_in_maze_regions_TL(conn, trial_id, r1=0.1, r2=0.2, bodypart_x='head_x_norm', 
                                    bodypart_y='head_y_norm', plot_maze=False):
    """
    Compute time spent in 3 zones defined by 2 concentric circles centered at corner_LL.

    Args:
        conn: psycopg2 or SQLAlchemy connection to database
        trial_id: int, trial ID in dlc_table
        r1: float, inner radius
        r2: float, outer radius        
        bodypart_x: str, column name for x-coordinate
        bodypart_y: str, column name for y-coordinate
        plot_maze: bool, whether to show the trajectory and circular zones

    Returns:
        dict: {
            'zone_inner': time inside r1 (s),
            'zone_middle': time in annulus between r1 and r2 (s),
            'zone_outer': time outside r2
        }
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

    cx, cy = 0.0, 1.0  # center at corner_LL

    distance = np.sqrt((x - cx)**2 + (y - cy)**2)

    zone_inner = distance <= r1
    zone_middle = (distance > r1) & (distance <= r2)
    zone_outer = distance > r2

    total_time = len(x) * dt
    
    result = {
        'zone_inner_frac': np.sum(zone_inner) * dt / total_time,
        'zone_middle_frac': np.sum(zone_middle) * dt / total_time,
        'zone_outer_frac': np.sum(zone_outer) * dt / total_time,
        'total_time': total_time
    }

    if plot_maze:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.scatter(x, y, s=2, alpha=0.9, label='Trajectory')
        ax.add_patch(plt.Circle((cx, cy), r1, color='green', fill=False, linestyle='--'))
        ax.add_patch(plt.Circle((cx, cy), r2, color='red', fill=False, linestyle='--'))
        ax.text(cx, cy, 'corner_LL', fontsize=8, ha='center', va='center')

        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(1.1, -0.1)
        ax.set_aspect('equal')
        ax.set_title(f'Trial {trial_id}: Concentric Zone Analysis')
        plt.tight_layout()
        plt.show()

    return result
