def compute_time_in_maze_regions(
    conn, trial_id, table='dlc_table', bodypart='Head',
    shape = 'square',  # 'square' or 'circle'
    size = 0.5, return_fraction = True, plot_maze = False
) -> Dict[str, float]:
    
    """
    Compute time spent in 4 corner regions + center + task-specific corner (from get_center_for_trial).
    Each region can be square (side=size) or circle (diameter=size), centered at corners or center.

    Returns:
        Dict with: 'corner_total', 'center', 'task_specific_corner'
    """
    from Python_scripts.Data_analysis.normalized_bodypart import get_normalized_bodypart
    from Python_scripts.Feature_functions.get_center_for_trial import get_center_for_trial
    import numpy as np
    import pandas as pd

    # 1. Get normalized trajectory
    x, y = get_normalized_bodypart(trial_id, conn, bodypart, normalize=True, interpolate=True)
    if x is None or y is None:
        raise ValueError(f"Missing normalized data for trial {trial_id}")

    # 2. Frame rate
    df = pd.read_sql_query(f"SELECT frame_rate FROM {table} WHERE id = %s", conn, params=(trial_id,))
    if df.empty or pd.isna(df['frame_rate'][0]):
        raise ValueError(f"Missing frame rate for trial {trial_id}")
    fps = df['frame_rate'][0]
    dt = 1.0 / fps
    n_frames = len(x)
    xy = np.stack((x, y), axis=1)
    half = size / 2

    # 3. Define centers of 5 regions
    region_centers = {
        'corner_UL': (0.0, 0.0),
        'corner_UR': (1.0, 0.0),
        'corner_LL': (0.0, 1.0),
        'corner_LR': (1.0, 1.0),
        'center':    (0.5, 0.5)
    }

    # 4. Compute time/fraction in each region
    region_values = {}
    masks = {}
    for name, (cx, cy) in region_centers.items():
        if shape == 'square':
            x0, x1 = cx - half, cx + half
            y0, y1 = cy - half, cy + half
            mask = (x >= x0) & (x <= x1) & (y >= y0) & (y <= y1)
        elif shape == 'circle':
            d = np.linalg.norm(xy - [cx, cy], axis=1)
            mask = d <= half
        else:
            raise ValueError("shape must be 'square' or 'circle'")
        masks[name] = mask
        val = np.sum(mask) / n_frames if return_fraction else np.sum(mask) * dt
        region_values[name] = val

    # 5. Get task-specific corner region
    task_center = get_center_for_trial(trial_id, conn, table)
    if task_center == (0, 0):
        task_region = 'corner_UL'
    elif task_center == (1, 0):
        task_region = 'corner_UR'
    elif task_center == (0, 1):
        task_region = 'corner_LL'
    elif task_center == (1, 1):
        task_region = 'corner_LR'
    else:
        print(f"[WARNING] Unknown task center: {task_center}, returning NaN for task-specific corner")
        task_region = None

    result = {
        'corner_total': sum(region_values[r] for r in ['corner_UL', 'corner_UR', 'corner_LL', 'corner_LR']),
        'center': region_values['center']
    }

    if task_region:
        result['task_specific_corner'] = region_values[task_region]
    else:
        result['task_specific_corner'] = np.nan

    # 6. Optional plot
    if plot_maze:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle, Circle

        fig, ax = plt.subplots(figsize=(5, 5))
        ax.scatter(x, y, s=2, alpha=0.6, label='Trajectory')

        for name, (cx, cy) in region_centers.items():
            if shape == 'square':
                patch = Rectangle((cx - half, cy - half), size, size,
                                  edgecolor='blue' if name == task_region else 'gray',
                                  linestyle='--', fill=False)
            else:
                patch = Circle((cx, cy), half,
                               edgecolor='blue' if name == task_region else 'gray',
                               linestyle='--', fill=False)
            ax.add_patch(patch)
            ax.text(cx, cy, name, fontsize=8, ha='center', va='center')

        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(1.1, -0.1)
        ax.set_aspect('equal')
        ax.set_title(f'Trial {trial_id}: Regions ({shape})')
        plt.tight_layout()
        plt.show()

    return result


def batch_time_in_maze_regions(
    conn, trial_ids, table = 'dlc_table', bodypart = 'Head',
    shape = 'square', size = 0.5, return_fraction = True, plot_maze = False
) -> pd.DataFrame:
    """
    Compute center/corner/task-specific region occupancy for a batch of trials.

    Returns:
        DataFrame with columns:
        ['trial_id', 'corner_total', 'center', 'task_specific_corner']
    """
    import pandas as pd
    from typing import List, Dict
    results = []

    for trial_id in trial_ids:
        try:
            region_times = compute_time_in_maze_regions(
                conn=conn,
                trial_id=trial_id,
                table=table,
                bodypart=bodypart,
                shape=shape,
                size=size,
                return_fraction=return_fraction,
                plot_maze=plot_maze  # You might want to turn this off unless debugging
            )
            region_times['trial_id'] = trial_id
            results.append(region_times)
        except Exception as e:
            print(f"Skipping trial {trial_id}: {e}")
            continue

    return pd.DataFrame(results)
