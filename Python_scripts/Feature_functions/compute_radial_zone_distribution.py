import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def compute_radial_zone_distribution(conn, trial_id,
                                     bodypart_x='head_x_norm', bodypart_y='head_y_norm',
                                     center=(0.0, 1.0), max_radius=1.0, n_bins=10,
                                     return_fraction=True, plot=False):
    """
    Compute time spent in concentric radial bins from a center point (e.g., corner_LL).
    """

    # Step 1: Get x, y coordinates, frame rate, and video name from the database
    query = f"""
        SELECT {bodypart_x}, {bodypart_y}, frame_rate, video_name
        FROM dlc_table
        WHERE id = {trial_id}
    """
    df = pd.read_sql_query(query, conn)

    # Step 2: Convert columns to arrays
    x = np.array(df[bodypart_x][0])
    y = np.array(df[bodypart_y][0])
    fps = df['frame_rate'].iloc[0]
    video_name = df['video_name'].iloc[0]
    dt = 1.0 / fps
    n_frames = len(x)
    total_time = n_frames * dt

    # Step 3: Calculate Euclidean distance from the center point for each frame
    cx, cy = center
    distance = np.sqrt((x - cx)**2 + (y - cy)**2)

    # Step 4: Create bin edges for radial zones
    bin_edges = np.linspace(0, max_radius, n_bins + 1)

    # Step 5: Create string labels for each bin
    bin_labels = [f"{round(bin_edges[i], 2)}–{round(bin_edges[i+1], 2)}" for i in range(n_bins)]

    # Step 6: Assign each distance value to a bin
    bin_indices = np.digitize(distance, bin_edges, right=False) - 1
    bin_indices[bin_indices == -1] = 0
    bin_indices[bin_indices >= n_bins] = n_bins - 1

    # Step 7: Count frames per bin
    bin_counts = np.bincount(bin_indices, minlength=n_bins)

    # Step 8: Convert to time or fraction
    bin_values = bin_counts / n_frames if return_fraction else bin_counts * dt

    # Step 9: Create Series with labels
    series = pd.Series(bin_values, index=bin_labels)

    # Step 10: Optional plot
    if plot:
        ax = series.plot(kind='bar', figsize=(8, 4), color='skyblue', edgecolor='k')
        ax.set_title(f'Trial {trial_id}: {video_name}', fontsize=12)
        ax.set_ylabel('Fraction of Time' if return_fraction else 'Time (s)')
        ax.set_xlabel('Radial Bin (Distance from Center)')
        plt.tight_layout()
        plt.show()

    return series
