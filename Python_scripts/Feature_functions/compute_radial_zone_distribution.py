import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def compute_radial_zone_distribution(conn, trial_id,
                                     bodypart_x='head_x_norm', bodypart_y='head_y_norm',
                                     center=(0.0, 1.0), max_radius=1.0, n_bins=10,
                                     return_fraction=True, plot=False):
    """
    Compute time spent in concentric radial bins from a center point (e.g., corner_LL).

    Args:
        conn: psycopg2 or SQLAlchemy database connection
        trial_id: int, trial ID to query from dlc_table
        bodypart_x, bodypart_y: str, column names for (x, y) coordinates
        center: tuple (x, y), center point for radial bins (e.g., corner_LL = (0.0, 1.0))
        max_radius: float, farthest radial distance to consider
        n_bins: int, number of equal-width radial bins
        return_fraction: bool, if True returns fraction of time per bin; else time in seconds
        plot: bool, whether to show barplot of result

    Returns:
        pd.Series: bin label → fraction of time (or seconds)
    """

    # Step 1: Get x, y coordinates and frame rate from the database
    query = f"""
        SELECT {bodypart_x}, {bodypart_y}, frame_rate
        FROM dlc_table
        WHERE id = {trial_id}
    """
    df = pd.read_sql_query(query, conn)

    # Step 2: Convert columns to arrays
    x = np.array(df[bodypart_x][0])
    y = np.array(df[bodypart_y][0])
    fps = df['frame_rate'].iloc[0]
    dt = 1.0 / fps
    n_frames = len(x)
    total_time = n_frames * dt

    # Step 3: Calculate Euclidean distance from the center point for each frame
    cx, cy = center
    distance = np.sqrt((x - cx)**2 + (y - cy)**2)

    # Step 4: Create bin edges for radial zones, e.g., [0.0, 0.1, ..., 1.0]
    bin_edges = np.linspace(0, max_radius, n_bins + 1)

    # Step 5: Create string labels like "0.0–0.1", "0.1–0.2", ..., for each bin
    bin_labels = [f"{round(bin_edges[i], 2)}–{round(bin_edges[i+1], 2)}" for i in range(n_bins)]

    # Step 6: Assign each distance value to a bin
    bin_indices = np.digitize(distance, bin_edges, right=False) - 1

    # Fix edge cases: frame distances exactly 0 or > max_radius
    bin_indices[bin_indices == -1] = 0
    bin_indices[bin_indices >= n_bins] = n_bins - 1

    # Step 7: Count how many frames fell into each bin
    bin_counts = np.bincount(bin_indices, minlength=n_bins)

    # Step 8: Convert frame counts into desired unit
    if return_fraction:
        bin_values = bin_counts / n_frames
    else:
        bin_values = bin_counts * dt

    # Step 9: Create a labeled Series
    series = pd.Series(bin_values, index=bin_labels)

    # Step 10 (Optional): Plot the distribution as a bar chart
    if plot:
        ax = series.plot(kind='bar', figsize=(8, 4), color='skyblue', edgecolor='k')
        ax.set_title(f'Trial {trial_id}: Radial Zone Distribution')
        ax.set_ylabel('Fraction of Time' if return_fraction else 'Time (s)')
        ax.set_xlabel('Radial Bin (Distance from Center)')
        plt.tight_layout()
        plt.show()

    return series
