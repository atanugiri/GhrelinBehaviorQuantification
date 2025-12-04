import numpy as np
import pandas as pd
from scipy.ndimage import uniform_filter1d
from typing import Tuple, List

from Python_scripts.Data_analysis.normalized_bodypart import get_normalized_bodypart


def _get_frame_rate(dlc_table: pd.DataFrame, trial_id: int) -> float:
    """Fetch frame_rate metadata for a trial."""
    row = dlc_table[dlc_table['id'] == trial_id]
    if row.empty or 'frame_rate' not in row.columns:
        raise ValueError(f"frame_rate not found for id={trial_id}")
    
    fps = row['frame_rate'].iloc[0]
    if pd.isna(fps):
        raise ValueError(f"Invalid frame_rate for id={trial_id}")
    
    return float(fps)


def compute_trajectory_curvature(dlc_table: pd.DataFrame,
                                 trial_id: int,
                                 bodypart: str = 'Midback',
                                 time_limit: float = None,   # <-- default None
                                 smooth: bool = True,
                                 window: int = 19,
                                 speed_thresh: float = 1e-2) -> Tuple[List[float], float]:
    """
    Compute trajectory curvature for a given trial using normalized/interpolated coordinates.

    Args:
        dlc_table: DataFrame containing trial metadata.
        trial_id: Trial ID.
        bodypart: Name of the bodypart, e.g., 'Head'.
        time_limit: Use data up to this time in seconds (None = full trajectory).
        smooth: If True, smooth coordinates before computing curvature.
        window: Smoothing window size in samples (ignored if smooth=False).
        speed_thresh: Set curvature to 0 where speed < threshold (units/sec in normalized space).

    Returns:
        Tuple:
            curvature: list of per-frame curvature values (float, NaN where undefined).
            mean_curv: Mean of valid curvature values (float).
    """
    # 1) Load trajectory
    x_vals, y_vals = get_normalized_bodypart(trial_id, dlc_table, bodypart, normalize=True, interpolate=True)
    x_vals = np.asarray(x_vals, dtype=float)
    y_vals = np.asarray(y_vals, dtype=float)

    # 2) Metadata
    frame_rate = _get_frame_rate(dlc_table, trial_id)
    if frame_rate <= 0:
        raise ValueError(f"Invalid frame_rate={frame_rate} for id={trial_id}")

    # 3) Respect time_limit if given
    if time_limit is not None and np.isfinite(time_limit):
        n_keep = int(min(len(x_vals), max(0, np.floor(time_limit * frame_rate))))
        x_vals = x_vals[:n_keep]
        y_vals = y_vals[:n_keep]

    if x_vals.size < 5:
        raise ValueError(f"Not enough data points for ID {trial_id} after time_limit.")

    # 4) Optional smoothing
    if smooth and window and window > 1:
        w = int(window)
        if w % 2 == 0:
            w += 1
        w = max(3, w)
        x_vals = uniform_filter1d(x_vals, size=w, mode='nearest')
        y_vals = uniform_filter1d(y_vals, size=w, mode='nearest')

    # 5) Derivatives
    dt = 1.0 / frame_rate
    dx = np.gradient(x_vals, dt)
    dy = np.gradient(y_vals, dt)
    ddx = np.gradient(dx, dt)
    ddy = np.gradient(dy, dt)

    # 6) Curvature
    speed = np.hypot(dx, dy)
    numerator = np.abs(dx * ddy - dy * ddx)
    denom = np.power(dx*dx + dy*dy, 1.5)

    with np.errstate(divide='ignore', invalid='ignore'):
        curvature = np.where(denom != 0, numerator / denom, np.nan)

    if speed_thresh is not None and speed_thresh > 0:
        curvature = np.where(speed < speed_thresh, 0.0, curvature)

    valid = np.isfinite(curvature)
    mean_curv = float(np.mean(curvature[valid])) if np.any(valid) else float('nan')

    return curvature.astype(float).tolist(), mean_curv


def batch_trajectory_curvature(dlc_table: pd.DataFrame,
                               trial_ids: List[int],
                               bodypart: str = 'Midback',
                               time_limit: float = None,   # <-- default None
                               smooth: bool = True,
                               window: int = 5,
                               speed_thresh: float = 1e-2) -> pd.DataFrame:
    """
    Compute mean curvature for a list of trial IDs.

    Args:
        dlc_table: DataFrame containing trial metadata.
        trial_ids: List of trial IDs to process.
        bodypart: e.g., 'Head'
        time_limit: Time cap (seconds), None = full trajectory.
        smooth: Whether to smooth trajectory.
        window: Smoothing window size in samples.
        speed_thresh: Speed threshold to suppress curvature (units/sec).

    Returns:
        DataFrame with columns ['id', 'mean_curvature']
    """
    rows = []
    for tid in trial_ids:
        try:
            _, mean_curv = compute_trajectory_curvature(
                dlc_table, tid,
                bodypart=bodypart,
                time_limit=time_limit,
                smooth=smooth,
                window=window,
                speed_thresh=speed_thresh
            )
            rows.append({'id': tid, 'mean_curvature': mean_curv})
        except Exception as e:
            print(f"Skipping ID {tid}: {e}")
    return pd.DataFrame(rows)
    x_vals = np.asarray(x_vals, dtype=float)
    y_vals = np.asarray(y_vals, dtype=float)

    # 2) Metadata
    frame_rate = _get_frame_rate(conn, trial_id)
    if frame_rate <= 0:
        raise ValueError(f"Invalid frame_rate={frame_rate} for id={trial_id}")

    # 3) Respect time_limit if given
    if time_limit is not None and np.isfinite(time_limit):
        n_keep = int(min(len(x_vals), max(0, np.floor(time_limit * frame_rate))))
        x_vals = x_vals[:n_keep]
        y_vals = y_vals[:n_keep]

    if x_vals.size < 5:
        raise ValueError(f"Not enough data points for ID {trial_id} after time_limit.")

    # 4) Optional smoothing
    if smooth and window and window > 1:
        w = int(window)
        if w % 2 == 0:
            w += 1
        w = max(3, w)
        x_vals = uniform_filter1d(x_vals, size=w, mode='nearest')
        y_vals = uniform_filter1d(y_vals, size=w, mode='nearest')

    # 5) Derivatives
    dt = 1.0 / frame_rate
    dx = np.gradient(x_vals, dt)
    dy = np.gradient(y_vals, dt)
    ddx = np.gradient(dx, dt)
    ddy = np.gradient(dy, dt)

    # 6) Curvature
    speed = np.hypot(dx, dy)
    numerator = np.abs(dx * ddy - dy * ddx)
    denom = np.power(dx*dx + dy*dy, 1.5)

    with np.errstate(divide='ignore', invalid='ignore'):
        curvature = np.where(denom != 0, numerator / denom, np.nan)

    if speed_thresh is not None and speed_thresh > 0:
        curvature = np.where(speed < speed_thresh, 0.0, curvature)

    valid = np.isfinite(curvature)
    mean_curv = float(np.mean(curvature[valid])) if np.any(valid) else float('nan')

    return curvature.astype(float).tolist(), mean_curv


def batch_trajectory_curvature(conn: PGConnection,
                               trial_ids: List[int],
                               bodypart: str = 'Midback',
                               time_limit: float = None,   # <-- default None
                               smooth: bool = True,
                               window: int = 5,
                               speed_thresh: float = 1e-2) -> pd.DataFrame:
    """
    Compute mean curvature for a list of trial IDs.

    Args:
        conn: Active PostgreSQL connection.
        trial_ids: List of trial IDs to process.
        bodypart: e.g., 'Head'
        time_limit: Time cap (seconds), None = full trajectory.
        smooth: Whether to smooth trajectory.
        window: Smoothing window size in samples.
        speed_thresh: Speed threshold to suppress curvature (units/sec).

    Returns:
        DataFrame with columns ['id', 'mean_curvature']
    """
    rows = []
    for tid in trial_ids:
        try:
            _, mean_curv = compute_trajectory_curvature(
                conn, tid,
                bodypart=bodypart,
                time_limit=time_limit,
                smooth=smooth,
                window=window,
                speed_thresh=speed_thresh
            )
            rows.append({'id': tid, 'mean_curvature': mean_curv})
        except Exception as e:
            print(f"Skipping ID {tid}: {e}")
    return pd.DataFrame(rows)
