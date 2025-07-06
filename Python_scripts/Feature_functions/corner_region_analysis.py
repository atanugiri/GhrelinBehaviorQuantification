import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List
from psycopg2.extensions import connection as PGConnection


def compute_time_in_maze_regions(conn: PGConnection,
                                  trial_id: int,
                                  radius: float = 0.1,
                                  bodypart_x: str = 'head_x_norm',
                                  bodypart_y: str = 'head_y_norm',
                                  plot_maze: bool = False,
                                  return_fraction: bool = False) -> Dict[str, float]:
    """
    Compute time spent in each corner and center of a square maze.

    Args:
        conn: Active PostgreSQL connection.
        trial_id: Trial ID to process.
        radius: Radius of circular region.
        bodypart_x: X-coordinate column name.
        bodypart_y: Y-coordinate column name.
        plot_maze: If True, show trajectory with region overlays.
        return_fraction: If True, return fraction of total time instead of seconds.

    Returns:
        Dictionary with keys:
        {'corner_UL', 'corner_UR', 'corner_LL', 'corner_LR', 'center', 'total_corners'}
        — values in seconds or fractions.
    """
    query = f"""
        SELECT {bodypart_x}, {bodypart_y}, frame_rate
        FROM dlc_table
        WHERE id = %s
    """
    df = pd.read_sql_query(query, conn, params=(trial_id,))
    if df.empty:
        raise ValueError(f"No data found for trial ID {trial_id}")

    x = np.array(df[bodypart_x][0])
    y = np.array(df[bodypart_y][0])
    fps = df['frame_rate'].iloc[0]

    if not isinstance(fps, (int, float)) or fps <= 0:
        raise ValueError(f"Invalid frame rate for ID {trial_id}")

    dt = 1.0 / fps
    total_frames = len(x)
    total_time = total_frames * dt

    regions = {
        'corner_UL': (0.0, 0.0),
        'corner_UR': (1.0, 0.0),
        'corner_LL': (0.0, 1.0),
        'corner_LR': (1.0, 1.0),
        'center': (0.5, 0.5),
    }

    time_spent = {}
    total_corner = 0.0

    for label, (cx, cy) in regions.items():
        dist = np.sqrt((x - cx)**2 + (y - cy)**2)
        inside = dist <= radius
        count = np.sum(inside)

        value = count / total_frames if return_fraction else count * dt
        time_spent[label] = value

        if 'corner' in label:
            total_corner += count

    time_spent['total_corners'] = (
        total_corner / total_frames if return_fraction else total_corner * dt
    )

    if plot_maze:
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.plot(x, y, lw=1, alpha=0.6, label='Trajectory')
        for label, (cx, cy) in regions.items():
            circle = plt.Circle((cx, cy), radius,
                                color='red' if 'corner' in label else 'blue',
                                fill=False, linestyle='--', label=label)
            ax.add_patch(circle)
            ax.text(cx, cy, label, fontsize=8, ha='center', va='center')

        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(1.1, -0.1)
        ax.set_aspect('equal')
        ax.set_title(f'Trial {trial_id}: Trajectory + Region Overlay')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.show()

    return time_spent



def batch_time_in_maze_regions(conn: PGConnection,
                                trial_ids: List[int],
                                radius: float = 0.1,
                                bodypart_x: str = 'head_x_norm',
                                bodypart_y: str = 'head_y_norm',
                                return_fraction: bool = False) -> pd.DataFrame:
    """
    Compute region-wise time (or fraction) for multiple trials.

    Args:
        conn: Active PostgreSQL connection.
        trial_ids: List of trial IDs.
        radius: Radius of region.
        bodypart_x: X-coordinate column name.
        bodypart_y: Y-coordinate column name.
        return_fraction: If True, return fraction of time instead of seconds.

    Returns:
        DataFrame: each row = one trial; columns = time or fraction in each region.
    """
    results = []

    for trial_id in trial_ids:
        try:
            res = compute_time_in_maze_regions(
                conn, trial_id, radius, bodypart_x, bodypart_y,
                plot_maze=False, return_fraction=return_fraction
            )
            res['id'] = trial_id
            results.append(res)
        except Exception as e:
            print(f"⚠️ Skipping trial {trial_id}: {e}")

    return pd.DataFrame(results)
