import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple, List
from psycopg2.extensions import connection as PGConnection


def compute_radial_zone_distribution(conn: PGConnection,
                                     trial_id: int,
                                     bodypart_x: str = 'head_x_norm',
                                     bodypart_y: str = 'head_y_norm',
                                     center: Tuple[float, float] = (0.0, 1.0),
                                     max_radius: float = 1.0,
                                     n_bins: int = 10,
                                     return_fraction: bool = True,
                                     plot: bool = False) -> pd.Series:
    """
    Compute time or fraction of time spent in concentric radial bins from a center point.

    Args:
        conn: Active PostgreSQL connection.
        trial_id: Trial ID to process.
        bodypart_x: Name of x-coordinate column.
        bodypart_y: Name of y-coordinate column.
        center: (x, y) coordinates of the center point.
        max_radius: Outer boundary for radial bins.
        n_bins: Number of radial bins.
        return_fraction: If True, return fraction of time; else return seconds.
        plot: If True, display a bar plot of the distribution.

    Returns:
        pd.Series: Time or fraction spent in each radial bin.
    """
    query = f"""
        SELECT {bodypart_x}, {bodypart_y}, frame_rate, video_name
        FROM dlc_table
        WHERE id = %s
    """
    df = pd.read_sql_query(query, conn, params=(trial_id,))
    if df.empty:
        raise ValueError(f"No data found for trial ID {trial_id}")

    x = np.array(df[bodypart_x][0])
    y = np.array(df[bodypart_y][0])
    fps = df['frame_rate'].iloc[0]
    video_name = df['video_name'].iloc[0]

    if not isinstance(fps, (int, float)) or fps <= 0:
        raise ValueError(f"Invalid frame rate for ID {trial_id}")

    dt = 1.0 / fps
    n_frames = len(x)
    total_time = n_frames * dt

    cx, cy = center
    distances = np.sqrt((x - cx)**2 + (y - cy)**2)

    bin_edges = np.linspace(0, max_radius, n_bins + 1)
    bin_labels = [f"{round(bin_edges[i], 2)}–{round(bin_edges[i + 1], 2)}" for i in range(n_bins)]

    bin_indices = np.digitize(distances, bin_edges, right=False) - 1
    bin_indices[bin_indices < 0] = 0
    bin_indices[bin_indices >= n_bins] = n_bins - 1

    bin_counts = np.bincount(bin_indices, minlength=n_bins)
    bin_values = bin_counts / n_frames if return_fraction else bin_counts * dt

    series = pd.Series(bin_values, index=bin_labels)

    if plot:
        ax = series.plot(kind='bar', figsize=(8, 4), color='skyblue', edgecolor='k')
        ax.set_title(f'Trial {trial_id}: {video_name}', fontsize=12)
        ax.set_ylabel('Fraction of Time' if return_fraction else 'Time (s)')
        ax.set_xlabel('Radial Bin (Distance from Center)')
        plt.tight_layout()
        plt.show()

    return series


def batch_radial_zone_distribution(conn: PGConnection,
                                   trial_ids: List[int],
                                   bodypart_x: str = 'head_x_norm',
                                   bodypart_y: str = 'head_y_norm',
                                   center: Tuple[float, float] = (0.0, 1.0),
                                   max_radius: float = 1.0,
                                   n_bins: int = 10,
                                   return_fraction: bool = True,
                                   plot: bool = False) -> pd.DataFrame:
    """
    Compute radial zone distribution for multiple trials.

    Args:
        conn: Active PostgreSQL connection.
        trial_ids: List of trial IDs to process.
        bodypart_x: Name of x-coordinate column.
        bodypart_y: Name of y-coordinate column.
        center: Center point (x, y) for radial analysis.
        max_radius: Maximum radius.
        n_bins: Number of radial bins.
        return_fraction: If True, return fraction of time; else return seconds.
        plot: If True, display plot for each trial.

    Returns:
        DataFrame: One row per trial with radial bin columns and 'id'.
    """
    all_results = []

    for trial_id in trial_ids:
        try:
            series = compute_radial_zone_distribution(
                conn=conn,
                trial_id=trial_id,
                bodypart_x=bodypart_x,
                bodypart_y=bodypart_y,
                center=center,
                max_radius=max_radius,
                n_bins=n_bins,
                return_fraction=return_fraction,
                plot=plot
            )
            result = series.to_dict()
            result['id'] = trial_id
            all_results.append(result)
        except Exception as e:
            print(f"⚠️ Skipping trial {trial_id}: {e}")

    return pd.DataFrame(all_results)
