import numpy as np
import pandas as pd
from typing import List, Tuple, Optional


def _get_fps(dlc_table: pd.DataFrame, trial_id: int) -> float:
    """Fetch per-trial frame rate from dlc_table DataFrame."""
    row = dlc_table[dlc_table['id'] == trial_id]
    if row.empty or 'frame_rate' not in row.columns:
        raise ValueError(f"Missing frame_rate for ID {trial_id}")
    
    fps = row['frame_rate'].iloc[0]
    if pd.isna(fps):
        raise ValueError(f"Invalid frame_rate for ID {trial_id}")
    
    return float(fps)


def compute_motion_features(dlc_table: pd.DataFrame, trial_id: int, 
                            bodypart='Midback',
                            time_limit: Optional[float] = None, 
                            smooth: bool = False, 
                            window: int = 5) -> Tuple[List[float], List[float], List[float]]:
    """
    Compute framewise motion features: distance, velocity, and acceleration
    using normalized bodypart coordinates from get_normalized_bodypart().
    """
    from Python_scripts.Data_analysis.normalized_bodypart import get_normalized_bodypart

    x_vals, y_vals = get_normalized_bodypart(
        trial_id=trial_id, 
        dlc_table=dlc_table, 
        bodypart=bodypart, 
        normalize=True,
        interpolate=True
    )

    if x_vals is None or y_vals is None:
        raise ValueError(f"Could not load normalized data for ID {trial_id}")

    # Get frame rate from dlc_table
    frame_rate = _get_fps(dlc_table, trial_id)
    t_vals = np.arange(len(x_vals)) / frame_rate

    if time_limit is not None:
        mask = (t_vals >= 0) & (t_vals <= time_limit)
        if not np.any(mask):
            raise ValueError(f"No frames in time range for ID {trial_id}")
        x_vals = x_vals[mask]
        y_vals = y_vals[mask]
        t_vals = t_vals[mask]

    if len(t_vals) < 3:
        raise ValueError(f"Not enough valid frames for ID {trial_id}")

    if smooth:
        from scipy.ndimage import uniform_filter1d
        x_vals = uniform_filter1d(x_vals, size=window)
        y_vals = uniform_filter1d(y_vals, size=window)

    dx = np.diff(x_vals)
    dy = np.diff(y_vals)
    dt = np.diff(t_vals)

    distance = np.sqrt(dx**2 + dy**2)
    velocity = np.divide(distance, dt, out=np.zeros_like(distance), where=dt != 0)

    acc = np.diff(velocity)
    dt2 = dt[1:]
    acceleration = np.divide(acc, dt2, out=np.zeros_like(acc), where=dt2 != 0)

    return (
        np.round(distance, 4).tolist(),
        np.round(velocity, 4).tolist(),
        np.round(acceleration, 4).tolist()
    )


def batch_compute_motion_feature(
    dlc_table: pd.DataFrame, 
    trial_ids: List[int], 
    bodypart='Midback',
    feature: str = 'distance',
    time_limit: Optional[float] = None, 
    smooth: bool = False, 
    window: int = 5
) -> List[np.ndarray]:
    """
    Compute a specified motion feature ('distance', 'velocity', 'acceleration') for a batch of trials.
    Uses normalized (x, y) from get_normalized_bodypart().
    """
    assert feature in ['distance', 'velocity', 'acceleration'], "Invalid feature name"

    results = []
    for trial_id in trial_ids:
        try:
            dis, vel, acc = compute_motion_features(
                dlc_table, trial_id, bodypart, time_limit, smooth, window
            )
            feature_map = {'distance': dis, 'velocity': vel, 'acceleration': acc}
            results.append(np.array(feature_map[feature]))
        except Exception as e:
            print(f"Skipping ID {trial_id}: {e}")
            continue
    return results


def compute_motion_features_per_minute(
    dlc_table: pd.DataFrame,
    trial_id: int,
    bodypart: str = 'Midback',
    time_limit: Optional[float] = None,
    smooth: bool = False,
    window: int = 5,
    min_duration_s: float = 5.0,
    return_diagnostics: bool = False,
) -> float | tuple[float, dict]:
    """
    Return a single scalar: average speed in arena-units per minute for one trial.
    Uses compute_motion_features(...) under the hood.

    If return_diagnostics=True, returns (velocity_per_min, info_dict).
    """
    # Get per-frame arrays via your existing function
    distance, velocity, _ = compute_motion_features(
        dlc_table=dlc_table, trial_id=trial_id, bodypart=bodypart,
        time_limit=time_limit, smooth=smooth, window=window
    )

    fps = _get_fps(dlc_table, trial_id)

    # distance has length N-1 for N frames; duration (s) ~ len(distance)/fps
    frames_of_motion = len(distance)
    duration_s = frames_of_motion / fps if frames_of_motion else 0.0

    if duration_s < min_duration_s or not np.isfinite(duration_s):
        vpm = float('nan')
        if return_diagnostics:
            return vpm, {
                "trial_id": trial_id,
                "fps": fps,
                "frames_used": int(frames_of_motion + 1) if frames_of_motion else 0,
                "duration_s": float(duration_s),
                "total_distance": 0.0,
                "reason": "duration_too_short"
            }
        return vpm

    total_distance = float(np.sum(distance))
    vpm = (total_distance / duration_s) * 60.0

    if return_diagnostics:
        return vpm, {
            "trial_id": trial_id,
            "fps": fps,
            "frames_used": int(frames_of_motion + 1),
            "duration_s": float(duration_s),
            "total_distance": total_distance
        }
    return vpm


def batch_compute_motion_features_per_minute(
    dlc_table: pd.DataFrame,
    trial_ids: List[int],
    bodypart: str = 'Midback',
    time_limit: Optional[float] = None,
    smooth: bool = False,
    window: int = 5,
    min_duration_s: float = 5.0
) -> pd.DataFrame:
    """
    Vectorized convenience: one row per trial with velocity_per_min (units/min) and diagnostics.
    """
    rows = []
    for tid in trial_ids:
        try:
            vpm, diag = compute_motion_features_per_minute(
                dlc_table, tid, bodypart=bodypart,
                time_limit=time_limit, smooth=smooth, window=window,
                min_duration_s=min_duration_s, return_diagnostics=True
            )
            rows.append({**diag, "velocity_per_min": float(vpm)})
        except Exception as e:
            # Keep going; you can log/print if desired
            print(f"Skipping ID {tid}: {e}")
            continue

    return pd.DataFrame(rows)


# --- Main Test Block ----------------------------------------------------------
if __name__ == "__main__":
    import sys
    from pathlib import Path
    # Ensure project root is importable for Python_scripts package
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from Python_scripts.config import load_dlc_table

    try:
        dlc_table = load_dlc_table()
    except Exception as e:
        print(f"Error loading dlc_table.csv: {e}")
        sys.exit(1)

    # Pick a sample trial id
    sample_id = int(dlc_table['id'].iloc[0])
    print(f"Running motion feature tests for trial ID {sample_id}")
    try:
        dis, vel, acc = compute_motion_features(dlc_table, sample_id)
        print(f"distance len: {len(dis)}, velocity len: {len(vel)}, acceleration len: {len(acc)}")
        vpm, diag = compute_motion_features_per_minute(dlc_table, sample_id, return_diagnostics=True)
        print(f"velocity per min: {vpm}")
        print(f"diagnostics: {diag}")
    except Exception as e:
        print(f"Test failed: {e}")
