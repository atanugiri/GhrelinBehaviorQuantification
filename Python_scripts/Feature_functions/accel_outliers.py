import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

# -----------------------------
# Robust spread + outliers
# -----------------------------
def _mad(x: np.ndarray) -> float:
    """
    Median Absolute Deviation (robust spread). NaNs ignored.
    """
    x = np.asarray(x, dtype=float)
    # print(f"[INFO] Analyzing x: type = {type(x)}, x = {x[:5]}")
    x = x[np.isfinite(x)]
    # print(f"[INFO] Analyzing x: size = {x.size}")    
    if x.size == 0:
        return np.nan
    med = np.median(x)
    # print(f"[INFO] Analyzing med: med = {med}")   
    # print(f"[INFO] Analyzing _mad return: mad = {np.median(np.abs(x - med))}")    
    return np.median(np.abs(x - med))

def accel_outlier_mask(accel: np.ndarray, mad_thresh: float = 3.5) -> np.ndarray:
    """
    Boolean mask of acceleration outliers using MAD-based z-scores.
    """
    accel = np.asarray(accel, dtype=float)
    # print(f"[INFO] Analyzing accel: type = {type(accel)}, accel = {accel[:5]}")
    med = np.median(accel)
    # print(f"[INFO] Analyzing med: type = {type(med)}, med = {med}")
    mad = _mad(accel)
    # print(f"[INFO] Analyzing mad: type = {type(mad)}, mad = {mad}")
    if not np.isfinite(mad) or mad == 0:
        return np.zeros_like(accel, dtype=bool)
    z = 0.6745 * (accel - med) / mad  # scale MAD toward std under Normal
    return np.abs(z) >= mad_thresh

# -----------------------------
# DB metadata (trial_length, frame_rate)
# -----------------------------
def _get_trial_meta(conn, trial_id: int, table: str = "dlc_table") -> Tuple[Optional[float], Optional[float]]:
    """
    Returns (trial_length_seconds, frame_rate_fps) from the DB (or (None, None) if missing).
    """
    q = f"SELECT trial_length, frame_rate FROM {table} WHERE id = %s;"
    df = pd.read_sql_query(q, conn, params=(trial_id,))
    if df.empty:
        return None, None
    length = float(df.loc[0, "trial_length"]) if pd.notna(df.loc[0, "trial_length"]) else None
    fps    = float(df.loc[0, "frame_rate"])  if "frame_rate" in df and pd.notna(df.loc[0, "frame_rate"]) else None
    return length, fps

# -----------------------------
# Single-trial summary
# -----------------------------
def accel_outliers_for_trial(
    trial_id: int,
    conn,
    table: str = "dlc_table",
    bodypart: str = "Head",
    # Parameters forwarded to your compute_motion_features:
    time_limit: Optional[float] = None,
    smooth: bool = False,
    window: int = 5,
    # Outlier logic:
    mad_thresh: float = 3.5,
    # Per-minute binning:
    bin_seconds: int = 60,
) -> Dict[str, Any]:
    """
    Summarize acceleration outliers for one trial.
    Uses your compute_motion_features(...) to get per-frame acceleration,
    and DB to get (trial_length, frame_rate) for normalization and binning.
    """
    from Python_scripts.Feature_functions.motion_features import compute_motion_features

    # Your function returns (distance, velocity, acceleration) as lists
    _dis, _vel, acc = compute_motion_features(
        conn, trial_id, table, bodypart, time_limit, smooth, window
    )
    acc = np.asarray(acc, dtype=float)

    # DB metadata
    duration_s, fps = _get_trial_meta(conn, trial_id, table=table)

    # Robust outlier mask
    mask = accel_outlier_mask(acc, mad_thresh=mad_thresh)
    total_outliers = int(mask.sum())

    # Duration fallback if DB length missing but fps available
    if (duration_s is None) and (fps is not None) and fps > 0:
        duration_s = len(acc) / float(fps)

    # Normalized rate per minute
    rate_per_min = (total_outliers / duration_s) * 60.0 if (duration_s and duration_s > 0) else np.nan

    # Per-minute counts if fps is known
    counts_per_min = None
    if fps is not None and fps > 0:
        bin_frames = max(1, int(round(bin_seconds * float(fps))))
        n = len(acc)
        counts_per_min = [int(mask[i:i+bin_frames].sum()) for i in range(0, n, bin_frames)]

    return dict(
        trial_id=trial_id,
        duration_s=duration_s,
        frame_rate=fps,
        total_outliers=total_outliers,
        rate_per_min=rate_per_min,
        counts_per_min=counts_per_min,  # list if fps known; else None
    )

# -----------------------------
# Batch over many trials
# -----------------------------
def batch_accel_outliers(
    conn,
    trial_ids: List[int],
    table: str = "dlc_table",
    bodypart: str = "Head",
    time_limit: Optional[float] = None,
    smooth: bool = False,
    window: int = 5,
    mad_thresh: float = 3.5,
    bin_seconds: int = 60,
) -> pd.DataFrame:
    """
    Run accel_outliers_for_trial on many trials (mixed FPS supported).
    """
    rows = []
    for tid in trial_ids:
        try:
            rows.append(accel_outliers_for_trial(
                tid, conn, table=table, bodypart=bodypart,
                time_limit=time_limit, smooth=smooth, window=window,
                mad_thresh=mad_thresh, bin_seconds=bin_seconds
            ))
        except Exception as e:
            rows.append(dict(
                trial_id=tid, duration_s=np.nan, frame_rate=np.nan,
                total_outliers=np.nan, rate_per_min=np.nan,
                counts_per_min=None, error=str(e)
            ))
    df = pd.DataFrame(rows)
    df["n_minutes"] = df["counts_per_min"].apply(lambda v: len(v) if isinstance(v, list) else np.nan)
    return df
