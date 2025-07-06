import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Union, List, Dict
from psycopg2.extensions import connection as PGConnection


def compute_time_in_maze_regions_FA(conn: PGConnection,
                                    trial_id: int,
                                    radius: float = 0.1,
                                    bodypart_x: str = 'head_x_norm',
                                    bodypart_y: str = 'head_y_norm',
                                    use_circle: bool = False,
                                    return_fraction: bool = True,
                                    plot_maze: bool = False) -> Dict[str, Union[float, int]]:
    """
    Compute fraction or duration of time spent inside vs. outside a central region (circle or square).

    Args:
        conn: Active PostgreSQL connection.
        trial_id: Trial ID to query.
        radius: Radius of the region (circle) or half-side (square).
        bodypart_x: Column name for x-coordinate.
        bodypart_y: Column name for y-coordinate.
        use_circle: If True, use circle; else use square.
        return_fraction: If True, return fraction of total time. Else return time in seconds.
        plot_maze: If True, plot trajectory and the region.

    Returns:
        Dictionary with keys 'inside' and 'outside', values in fraction or seconds.
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
    n_frames = len(x)

    if use_circle:
        inside = ((x - 0.5) ** 2 + (y - 0.5) ** 2) <= radius ** 2
    else:
        inside = (
            (x >= 0.5 - radius) & (x <= 0.5 + radius) &
            (y >= 0.5 - radius) & (y <= 0.5 + radius)
        )

    n_inside = np.sum(inside)
    n_outside = n_frames - n_inside

    if return_fraction:
        result = {
            'inside': n_inside / n_frames,
            'outside': n_outside / n_frames
        }
    else:
        result = {
            'inside': n_inside * dt,
            'outside': n_outside * dt
        }

    if plot_maze:
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.scatter(x, y, s=2, alpha=0.6, label='Trajectory')

        if use_circle:
            from matplotlib.patches import Circle
            shape = Circle((0.5, 0.5), radius, edgecolor='blue', fill=False,
                           linestyle='--', label='Center Circle')
        else:
            from matplotlib.patches import Rectangle
            shape = Rectangle((0.5 - radius, 0.5 - radius), 2 * radius, 2 * radius,
                              edgecolor='red', fill=False, linestyle='--', label='Center Square')

        ax.add_patch(shape)
        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(1.1, -0.1)
        ax.set_aspect('equal')
        ax.set_title(f'Trial {trial_id}: Inside vs Outside')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.show()

    return result


def batch_time_in_maze_regions_FA(conn: PGConnection,
                                  trial_ids: List[int],
                                  radius: float = 0.1,
                                  bodypart_x: str = 'head_x_norm',
                                  bodypart_y: str = 'head_y_norm',
                                  use_circle: bool = False,
                                  return_fraction: bool = True) -> pd.DataFrame:
    """
    Compute time spent in center region for multiple trials.

    Args:
        conn: Active PostgreSQL connection.
        trial_ids: List of trial IDs to process.
        radius: Radius (or half-side) of region of interest.
        bodypart_x: Column name for x-coordinate.
        bodypart_y: Column name for y-coordinate.
        use_circle: If True, use a circular region; else use square.
        return_fraction: If True, return fraction of total time; else seconds.

    Returns:
        DataFrame with one row per trial: columns ['id', 'inside', 'outside']
    """
    results = []

    for trial_id in trial_ids:
        try:
            region_data = compute_time_in_maze_regions_FA(
                conn, trial_id, radius, bodypart_x, bodypart_y,
                use_circle, return_fraction, plot_maze=False
            )
            region_data['id'] = trial_id
            results.append(region_data)
        except Exception as e:
            print(f"⚠️ Skipping trial {trial_id}: {e}")

    return pd.DataFrame(results)
