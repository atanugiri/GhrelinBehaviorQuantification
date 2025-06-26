def compute_time_in_maze_regions_FA(conn, trial_id, radius=0.1, bodypart_x='head_x_norm', bodypart_y='head_y_norm',
                                    use_circle=False, return_fraction=True, plot_maze=False):
    """
    Compute fraction of time spent inside and outside a central region (square or circle).

    Args:
        conn: psycopg2 or SQLAlchemy connection to database
        trial_id: int
        radius: float, radius of the region (for circle) or half side (for square)
        bodypart_x, bodypart_y: columns for coordinates
        use_circle: if True, use a circular region; else use square
        return_fraction: if True, return fraction of total time instead of seconds
        plot_maze: if True, plot trajectory and region

    Returns:
        dict: {'inside': frac_inside, 'outside': frac_outside} or in seconds if return_fraction=False
    """
    import numpy as np
    import pandas as pd

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
    n_frames = len(x)

    if use_circle:
        inside = ((x - 0.5)**2 + (y - 0.5)**2) <= radius**2
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
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.scatter(x, y, s=2, alpha=0.6, label='Trajectory')

        if use_circle:
            from matplotlib.patches import Circle
            shape = Circle((0.5, 0.5), radius, edgecolor='blue', fill=False, linestyle='--', label='Center Circle')
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
