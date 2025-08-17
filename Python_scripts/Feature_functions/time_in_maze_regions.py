from typing import Dict
import pandas as pd
import numpy as np

def _corner_from_center(cx, cy, tol=1e-6):
    """Map DB (center_x, center_y) to a corner name or None if geometric center/missing."""
    if pd.isna(cx) or pd.isna(cy):
        return None
    if abs(cx - 0.5) <= tol and abs(cy - 0.5) <= tol:
        return None  # geometric center -> no task-specific corner
    ix = 0 if cx <= 0.5 + tol else 1
    iy = 0 if cy <= 0.5 + tol else 1
    return { (0,0): 'corner_UL', (1,0): 'corner_UR', (0,1): 'corner_LL', (1,1): 'corner_LR' }[(ix, iy)]

def compute_time_in_maze_regions(
    conn, trial_id, table='dlc_table', bodypart='Head',
    shape='square',  # 'square' or 'circle'; circle uses diameter=size
    size=0.5, return_fraction=True, plot_maze=False
) -> Dict[str, float]:

    """
    Compute time in 4 corner regions + center + task-specific corner (from DB center_x, center_y).
    Returns dict with: 'corner_total', 'center', 'task_specific_corner'
    """

    # 1) Trajectory
    from Python_scripts.Data_analysis.normalized_bodypart import get_normalized_bodypart
    x, y = get_normalized_bodypart(trial_id, conn, bodypart, normalize=True, interpolate=True)
    if x is None or y is None:
        raise ValueError(f"Missing normalized data for trial {trial_id}")
    xy = np.stack((x, y), axis=1)
    n_frames = len(x)

    # 2) One query for meta
    meta = pd.read_sql_query(
        f"SELECT frame_rate, center_x, center_y FROM {table} WHERE id = %s",
        conn, params=(trial_id,)
    )
    if meta.empty or pd.isna(meta.at[0, 'frame_rate']):
        raise ValueError(f"Missing frame rate for trial {trial_id}")
    fps = float(meta.at[0, 'frame_rate'])
    cx_db, cy_db = meta.at[0, 'center_x'], meta.at[0, 'center_y']
    dt = 1.0 / fps

    # 3) Region centers
    region_centers = {
        'corner_UL': (0.0, 0.0),
        'corner_UR': (1.0, 0.0),
        'corner_LL': (0.0, 1.0),
        'corner_LR': (1.0, 1.0),
        'center':    (0.5, 0.5),
    }
    half = size / 2

    # 4) Occupancy
    region_values = {}
    for name, (cx, cy) in region_centers.items():
        if shape == 'square':
            mask = (x >= cx - half) & (x <= cx + half) & (y >= cy - half) & (y <= cy + half)
        elif shape == 'circle':
            mask = np.linalg.norm(xy - [cx, cy], axis=1) <= half
        else:
            raise ValueError("shape must be 'square' or 'circle'")
        count = np.count_nonzero(mask)
        region_values[name] = (count / n_frames) if return_fraction else (count * dt)

    # 5) Task-specific corner from DB
    task_region = _corner_from_center(cx_db, cy_db)
    result = {
        'corner_total': sum(region_values[k] for k in ('corner_UL','corner_UR','corner_LL','corner_LR')),
        'center': region_values['center'],
        'task_specific_corner': region_values[task_region] if task_region else np.nan,
    }

    # 6) Optional plot
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
        ax.set_xlim(-0.1, 1.1); ax.set_ylim(1.1, -0.1); ax.set_aspect('equal')
        ax.set_title(f'Trial {trial_id}: Regions ({shape})')
        plt.tight_layout(); plt.show()

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
