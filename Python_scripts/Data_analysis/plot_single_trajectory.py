import matplotlib.pyplot as plt
import numpy as np

from Python_scripts.Data_analysis.normalized_bodypart import get_normalized_bodypart

def plot_single_trajectory(conn, trial_id, bodypart='Midback', table='dlc_table',
                           normalize=True, interpolate=True, likelihood_threshold=0.5,
                           use_homography=False,
                           label=None, color=None, style='line',
                           max_points=None, color_by_time=True, ax=None
                           ):
    """
    Plot trajectory from DLC CSV for a given bodypart (interpolated + normalized).
    """
    # Load and optionally normalize/interpolate bodypart coordinates
    x, y = get_normalized_bodypart(
        trial_id, conn, bodypart=bodypart, table=table,
        likelihood_threshold=likelihood_threshold,
        normalize=normalize, interpolate=interpolate, 
        use_homography=use_homography,
    )

    if x is None or y is None or len(x) == 0:
        print(f"No valid trajectory for Trial ID {trial_id}")
        return ax

    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 5))

    # Optional downsampling
    if max_points is not None and len(x) > max_points:
        x = x[:max_points]
        y = y[:max_points]

    # Plot title (optional)
    ax.set_title(f"Trial {trial_id} | {bodypart}")
    ax.invert_yaxis()
    ax.set_aspect('equal')

    # Plotting
    if style == 'scatter':
        if color is not None or not color_by_time:
            ax.scatter(x, y, s=2, label=label or f"ID {trial_id}", color=color)
        else:
            c = np.linspace(0, 1, len(x))
            sc = ax.scatter(x, y, c=c, cmap='viridis', s=2)
            plt.colorbar(sc, ax=ax, label='Progression')
    else:
        ax.plot(x, y, label=label or f"ID {trial_id}", color=color)

    if label:
        ax.legend()

    return ax
