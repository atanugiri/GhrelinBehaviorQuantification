import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

# --- pull normalized coordinates directly ---
from Python_scripts.Data_analysis.normalized_bodypart import get_normalized_bodypart

# --- DB helper (short form, same style as accel_outliers) ---
def _get_trial_meta(conn, trial_id: int, table: str = "dlc_table") -> Tuple[Optional[float], Optional[float]]:
    """
    Returns (trial_length_seconds, frame_rate_fps) from the DB (or (None, None) if missing).
    Uses psycopg2 '%s' style with sqlite fallback to '?'.
    """
    # Use a DB cursor rather than pandas.read_sql_query to avoid pandas' SQLAlchemy
    # warning when given a DBAPI connection (psycopg2, sqlite3, etc.). This also
    # keeps the function dependency-light and works for both drivers.
    q_psycopg = f"SELECT trial_length, frame_rate FROM {table} WHERE id = %s;"
    q_sqlite = f"SELECT trial_length, frame_rate FROM {table} WHERE id = ?;"

    cur = None
    try:
        cur = conn.cursor()
        # Try psycopg2 style first
        try:
            cur.execute(q_psycopg, (trial_id,))
        except Exception:
            # Fallback to sqlite-style parameter marker
            cur.execute(q_sqlite, (trial_id,))

        rows = cur.fetchall()
        if not rows:
            return None, None

        # Build a dict from the first row using cursor.description
        cols = [d[0] for d in cur.description] if cur.description else []
        row = rows[0]
        rowd = dict(zip(cols, row))

        length = float(rowd.get("trial_length")) if rowd.get("trial_length") is not None else None
        fps = float(rowd.get("frame_rate")) if rowd.get("frame_rate") is not None else None
        return length, fps
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass

def _runs_from_bbox(x: np.ndarray, y: np.ndarray,
                    dx_thresh: float, dy_thresh: float,
                    min_frames: int) -> List[Tuple[int,int]]:
    """
    One-pass scan: grow a candidate segment while the axis-aligned bounding
    box of points stays within dx_thresh × dy_thresh; otherwise close and restart.
    Returns inclusive (start, end) frame indices for segments meeting min_frames.
    """
    n = min(len(x), len(y))
    if n == 0:
        return []

    segs: List[Tuple[int,int]] = []
    s = None
    minx = maxx = miny = maxy = None

    def close_candidate(end_idx):
        nonlocal s
        if s is not None:
            L = end_idx - s + 1
            if L >= min_frames:
                segs.append((s, end_idx))
            s = None

    for i in range(n):
        xi, yi = x[i], y[i]

        # break on NaN
        if not (np.isfinite(xi) and np.isfinite(yi)):
            close_candidate(i - 1)
            minx = maxx = miny = maxy = None
            continue

        if s is None:
            # start new candidate
            s = i
            minx = maxx = xi
            miny = maxy = yi
            continue

        # update bbox
        if xi < minx: minx = xi
        if xi > maxx: maxx = xi
        if yi < miny: miny = yi
        if yi > maxy: maxy = yi

        # if box exceeds threshold, close previous at i-1 and start new at i
        if (maxx - minx) > dx_thresh or (maxy - miny) > dy_thresh:
            close_candidate(i - 1)
            s = i
            minx = maxx = xi
            miny = maxy = yi

    # finalize last
    if s is not None:
        close_candidate(n - 1)

    return segs

# -----------------------------
# Single-trial (position-based)
# -----------------------------
def stopping_points_bbox_for_trial(
    trial_id: int,
    conn,
    table: str = "dlc_table",
    bodypart: str = "Midback",
    time_limit: Optional[float] = None,
    dx_thresh: float = 0.1,
    dy_thresh: float = 0.1,
    min_stop_duration_s: float = 1.5,
    normalize: bool = True,
    interpolate: bool = True,
) -> Dict[str, Any]:
    """
    Count stops from unit-normalized positions: a stop occurs if (x,y) remains
    within an axis-aligned box of size dx_thresh × dy_thresh for ≥ min_stop_duration_s.
    Bins by stop onset minute.
    """
    duration_s_db, fps_db = _get_trial_meta(conn, trial_id, table=table)
    if fps_db is None or not np.isfinite(fps_db) or fps_db <= 0:
        raise ValueError(f"Missing/invalid frame_rate for trial {trial_id} in '{table}'.")
    fps = float(fps_db)

    # fetch normalized coordinates (your function)
    x, y = get_normalized_bodypart(
        trial_id=trial_id, conn=conn, bodypart=bodypart,
        normalize=normalize, interpolate=interpolate
    )
    x = np.asarray(x, float)
    y = np.asarray(y, float)

    # optional truncation
    if time_limit is not None and time_limit > 0:
        n_keep = int(np.floor(time_limit * fps))
        x = x[:n_keep]
        y = y[:n_keep]

    n = min(len(x), len(y))
    if n == 0:
        return dict(
            trial_id=trial_id, frame_rate=fps, duration_s=0.0,
            num_stops=0, stops_per_min=np.nan, counts_per_min=[],
            stop_segments=[], dx_thresh=dx_thresh, dy_thresh=dy_thresh,
            min_stop_duration_s=min_stop_duration_s
        )

    min_frames = int(round(min_stop_duration_s * fps))
    segments = _runs_from_bbox(x, y, dx_thresh, dy_thresh, min_frames)

    # choose duration: prefer DB length; fallback to analyzed length
    duration_s = float(duration_s_db) if (duration_s_db is not None and np.isfinite(duration_s_db) and duration_s_db > 0) else n / fps

    # per-minute binning (onset)
    num_stops = len(segments)
    n_minutes = int(np.ceil(duration_s / 60.0)) if duration_s > 0 else 0
    counts_per_min = [0] * n_minutes
    for (start, _end) in segments:
        onset_sec = start / fps
        bin_idx = int(onset_sec // 60.0)
        if 0 <= bin_idx < n_minutes:
            counts_per_min[bin_idx] += 1

    stops_per_min = (num_stops / (duration_s / 60.0)) if duration_s > 0 else np.nan

    # Total stop time & fraction
    stop_frames = sum((e - s + 1) for s, e in segments)
    stop_time_s = stop_frames / fps
    stop_time_fraction = (stop_time_s / duration_s) if duration_s > 0 else np.nan

    return dict(
        trial_id=trial_id,
        frame_rate=fps,
        duration_s=float(duration_s),
        num_stops=int(num_stops),
        stops_per_min=float(stops_per_min) if np.isfinite(stops_per_min) else np.nan,
        counts_per_min=counts_per_min,
        stop_segments=segments,
        dx_thresh=float(dx_thresh),
        dy_thresh=float(dy_thresh),
        min_stop_duration_s=float(min_stop_duration_s),
        stop_time_s=float(stop_time_s),
        stop_time_fraction=float(stop_time_fraction) if np.isfinite(stop_time_fraction) else np.nan,
    )


# -----------------------------
# Batch wrapper
# -----------------------------
def batch_stopping_points_bbox(
    conn, id_list: List[int],
    table: str = "dlc_table",
    bodypart: str = "Head",
    time_limit: Optional[float] = None,
    dx_thresh: float = 0.1,
    dy_thresh: float = 0.1,
    min_stop_duration_s: float = 5.0,
    normalize: bool = True,
    interpolate: bool = True,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for tid in id_list:
        try:
            rows.append(stopping_points_bbox_for_trial(
                tid, conn, table=table, bodypart=bodypart,
                time_limit=time_limit, dx_thresh=dx_thresh, dy_thresh=dy_thresh,
                min_stop_duration_s=min_stop_duration_s,
                normalize=normalize, interpolate=interpolate
            ))
        except Exception as e:
            rows.append(dict(
                trial_id=tid, frame_rate=np.nan, duration_s=np.nan,
                num_stops=np.nan, stops_per_min=np.nan, counts_per_min=None,
                stop_segments=None, dx_thresh=dx_thresh, dy_thresh=dy_thresh,
                min_stop_duration_s=min_stop_duration_s, error=str(e)
            ))
    df = pd.DataFrame(rows)
    df["n_minutes"] = df["duration_s"].apply(lambda s: int(np.ceil(s / 60.0)) if pd.notna(s) and s > 0 else np.nan)
    return df
