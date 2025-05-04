import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def calculate_time_in_roi_20min(filename, maze, body_part='Head', r=0.25, likelihood_threshold=0.9, plot=False):
    """
    Calculates time spent inside a circular ROI for the first 20 minutes.
    Optionally plots trajectory with ROI shaded.

    Parameters:
        filename (str): Path to normalized CSV file.
        maze (int or float): Maze number (should be 1,2,3,4).
        body_part (str): Body part to track (default 'Head').
        r (float): Radius of ROI (default 0.25).
        likelihood_threshold (float): Minimum likelihood threshold (default 0.9).
        plot (bool): Whether to generate a scatter plot with ROI overlay (default False).

    Returns:
        time_in_roi (float): Time spent in ROI (seconds).
    """
    try:
        maze = int(maze)  # Ensure maze is integer

        # Load CSV
        df = pd.read_csv(filename, header=[0,1])

        # Filter first 20 minutes
        df_20min = df[df[('Unnamed: 1_level_0', 's')] <= 1200].copy()

        # Extract time, x, y, likelihood
        t = df_20min[('Unnamed: 1_level_0', 's')].to_numpy()
        x = df_20min[(body_part, 'x')].to_numpy()
        y = df_20min[(body_part, 'y')].to_numpy()
        likelihood = df_20min[(body_part, 'likelihood')].to_numpy()

        # Mask low likelihood
        x[likelihood < likelihood_threshold] = np.nan
        y[likelihood < likelihood_threshold] = np.nan

        # Valid frames only
        valid = ~np.isnan(x) & ~np.isnan(y)
        t = t[valid]
        x = x[valid]
        y = y[valid]

        if len(x) == 0:
            return 0.0

        # ROI center definition
        if maze in [1,2,3]:
            cx, cy = 0.0, 0.0
        elif maze == 4:
            cx, cy = 1.0, 1.0
        else:
            raise ValueError(f"Unknown maze: {maze}")

        # Compute distance from center
        dx = x - cx
        dy = y - cy
        radius = np.sqrt(dx**2 + dy**2)

        # Check if inside circular ROI
        in_roi = radius <= r

        # Calculate time spent inside ROI
        time_diffs = np.diff(t)  # Time between consecutive frames
        time_in_roi = np.sum(time_diffs[in_roi[:-1]])  # Adjusted length

        # Optional plotting
        if plot:
            fig, ax = plt.subplots(figsize=(6,6))
            ax.scatter(x, y, s=5, alpha=0.5, label='Tracked Points')
            ax.set_aspect('equal')

            # Draw full circle ROI
            circle = plt.Circle((cx, cy), r, color='red', alpha=0.2, label='ROI')
            ax.add_patch(circle)

            ax.set_xlim(-0.2, 1.2)
            ax.set_ylim(-0.2, 1.2)
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.set_title(f'Maze {maze} - Time in ROI: {time_in_roi:.2f}s')
            ax.legend()
            plt.show()

        return time_in_roi

    except Exception as e:
        print(f"⚠️ Error processing {filename}: {e}")
        return None
