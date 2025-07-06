import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Optional
from psycopg2.extensions import connection as PGConnection


def compute_time_in_maze_regions_TL(conn: PGConnection,
                                     trial_id: int,
                                     r1: float = 0.1,
                                     r2: float = 0.2,
                                     bodypart_x: str = 'head_x_norm',
                                     bodypart_y: str = 'head_y_norm',
                                     plot_maze: bool = False) -> Dict[str, float]:
    """
    Compute time fraction spent in 3 concentric zones (inner, middle, outer) centered at lower-left corner.

    Args:
        conn: Active PostgreSQL connection.
        trial_id: Trial ID to analyze.
        r1: Inner radius (for zone_inner).
        r2: Outer radius (for zone_outer).
        bodypart_x: Name of x-coordinate column.
        bodypart_y: Name of y-coordinate column.
        plot_maze: If True, show trajectory and zone overlays.

    Returns:
        Dict with fraction of time in each zone and total duration.
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
    cx, cy = 0.0, 1.0  # lower-left corner
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)

    zone_inner = dist <= r1
    zone_middle = (dist > r1) & (dist <= r2)
    zone_outer = dist > r2

    total_time = len(x) * dt
    result = {
        'zone_inner_frac': np.sum(zone_inner) * dt / total_time,
        'zone_middle_frac': np.sum(zone_middle) * dt / total_time,
        'zone_outer_frac': np.sum(zone_outer) * dt / total_time,
        'total_time': total_time
    }

    if plot_maze:
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.scatter(x, y, s=2, alpha=0.9, label='Trajectory')
        ax.add_patch(plt.Circle((cx, cy), r1, color='green', fill=False, linestyle='--', label=f'Inner (r={r1})'))
        ax.add_patch(plt.Circle((cx, cy), r2, color='red', fill=False, linestyle='--', label=f'Outer (r={r2})'))
        ax.text(cx, cy, 'corner_LL', fontsize=8, ha='center', va='center')

        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(1.1, -0.1)
        ax.set_aspect('equal')
        ax.set_title(f'Trial {trial_id}: Concentric Zone Analysis')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.show()

    return result


def batch_time_in_maze_regions_TL(conn: PGConnection,
                                   trial_ids: List[int],
                                   r1: float = 0.1,
                                   r2: float = 0.2,
                                   bodypart_x: str = 'head_x_norm',
                                   bodypart_y: str = 'head_y_norm') -> pd.DataFrame:
    """
    Compute concentric zone time fractions for multiple trials.

    Args:
        conn: Active PostgreSQL connection.
        trial_ids: List of trial IDs to process.
        r1: Inner radius.
        r2: Outer radius.
        bodypart_x: Name of x-coordinate column.
        bodypart_y: Name of y-coordinate column.

    Returns:
        DataFrame: one row per trial with zone fractions and total time.
    """
    results = []

    for trial_id in trial_ids:
        try:
            res = compute_time_in_maze_regions_TL(
                conn, trial_id, r1, r2, bodypart_x, bodypart_y, plot_maze=False
            )
            res['id'] = trial_id
            results.append(res)
        except Exception as e:
            print(f"⚠️ Skipping trial {trial_id}: {e}")

    return pd.DataFrame(results)
