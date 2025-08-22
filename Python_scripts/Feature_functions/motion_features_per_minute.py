# Python_scripts/Feature_functions/motion_features_per_minute.py

from typing import List, Optional
import numpy as np
import pandas as pd
from psycopg2.extensions import connection as PGConnection

from Python_scripts.Feature_functions.motion_features import compute_motion_features


def _get_fps(conn: PGConnection, table: str, trial_id: int) -> float:
    """Fetch per-trial frame rate."""
    df = pd.read_sql_query(
        f"SELECT frame_rate FROM {table} WHERE id=%s;",
        conn, params=(trial_id,)
    )
    if df.empty or pd.isna(df.iloc[0, 0]):
        raise ValueError(f"Missing or invalid frame_rate for ID {trial_id}")
    return float(df.iloc[0, 0])


def compute_motion_features_per_minute(
    conn: PGConnection,
    trial_id: int,
    table: str = 'dlc_table',
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
        conn=conn, trial_id=trial_id, table=table, bodypart=bodypart,
        time_limit=time_limit, smooth=smooth, window=window
    )

    fps = _get_fps(conn, table, trial_id)

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
    conn: PGConnection,
    trial_ids: List[int],
    table: str = 'dlc_table',
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
                conn, tid, table=table, bodypart=bodypart,
                time_limit=time_limit, smooth=smooth, window=window,
                min_duration_s=min_duration_s, return_diagnostics=True
            )
            rows.append({**diag, "velocity_per_min": float(vpm)})
        except Exception as e:
            # Keep going; you can log/print if desired
            print(f"Skipping ID {tid}: {e}")
            continue

    return pd.DataFrame(rows)
