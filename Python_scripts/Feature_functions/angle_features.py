# angle_features.py

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List

from Python_scripts.Feature_functions.stopping_points import _get_trial_meta

# ---------- math utils (unchanged) ----------
def _angle_of(v: np.ndarray) -> np.ndarray:
    return np.arctan2(v[:, 1], v[:, 0])

def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=1, keepdims=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(n > 0, v / n, np.nan)

def _angle_between(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    uu, vv = _unit(u), _unit(v)
    dot = np.sum(uu * vv, axis=1)
    cross_z = uu[:, 0]*vv[:, 1] - uu[:, 1]*vv[:, 0]
    return np.arctan2(cross_z, dot)

def _unwrap(a: np.ndarray) -> np.ndarray:
    return np.unwrap(a)

# ---------- I/O helpers (unchanged) ----------
def _read_csv_path(conn, trial_id: int, table: str = "dlc_table") -> str:
    q = f"SELECT csv_file_path FROM {table} WHERE id = %s;"
    df = pd.read_sql_query(q, conn, params=(trial_id,))
    if df.empty or pd.isna(df.loc[0, "csv_file_path"]):
        raise ValueError(f"csv_file_path not found for id={trial_id} in '{table}'")
    return str(df.loc[0, "csv_file_path"])

def _load_bodyparts_raw(csv_path: str, bodyparts: List[str], likelihood_threshold: float = 0.5) -> Dict[str, np.ndarray]:
    df = pd.read_csv(csv_path, header=[1, 2], index_col=0)
    out: Dict[str, np.ndarray] = {}
    for bp in bodyparts:
        x = df[(bp, 'x')].astype(float).copy()
        y = df[(bp, 'y')].astype(float).copy()
        if (bp, 'likelihood') in df.columns:
            p = df[(bp, 'likelihood')].astype(float).copy()
            x[p < likelihood_threshold] = np.nan
            y[p < likelihood_threshold] = np.nan
        xs = pd.Series(x).interpolate(limit_direction='both')
        ys = pd.Series(y).interpolate(limit_direction='both')
        out[bp] = np.column_stack([xs.to_numpy(dtype=float), ys.to_numpy(dtype=float)])
    return out

# ---------- core per-trial ----------
def angle_features_for_trial(
    conn,
    trial_id: int,
    table: str = "dlc_table",
    likelihood_threshold: float = 0.5,
    smooth_window: Optional[int] = None,
) -> Tuple[Dict[str, np.ndarray], Dict[str, Dict[str, float]], np.ndarray]:
    trial_length_s, frame_rate = _get_trial_meta(conn, trial_id, table=table)
    if frame_rate is None or not np.isfinite(frame_rate) or frame_rate <= 0:
        raise ValueError(f"Missing/invalid frame_rate for trial {trial_id} in '{table}'.")
    csv_path = _read_csv_path(conn, trial_id, table=table)
    
    print(f"[INFO] csv path: {csv_path}") #TBD

    parts = ["Head", "Neck", "Midback", "Lowerback", "Tailbase"]
    B = _load_bodyparts_raw(csv_path, parts, likelihood_threshold=likelihood_threshold)
    head, neck = B["Head"], B["Neck"]
    mid, low  = B["Midback"], B["Lowerback"]
    tail      = B["Tailbase"]

    v_tail_head = head - tail
    v_head_neck = head - neck
    v_neck_mid  = neck - mid
    v_mid_low   = mid - low
    v_low_tail  = low - tail


    theta_body = _angle_of(v_tail_head)
    theta_head = _angle_of(v_head_neck)
    theta_seg_head_neck = _angle_of(v_head_neck)
    theta_seg_neck_mid  = _angle_of(v_neck_mid)
    theta_seg_mid_low   = _angle_of(v_mid_low)
    theta_seg_low_tail  = _angle_of(v_low_tail)

    head_body_misalignment = _angle_between(v_tail_head, v_head_neck)
    bend_neck = _angle_between(-v_head_neck, -v_neck_mid)
    bend_mid  = _angle_between(-v_neck_mid,  -v_mid_low)
    bend_low  = _angle_between(-v_mid_low,   -v_low_tail)
    tail_bend_index = np.abs(bend_neck) + np.abs(bend_mid) + np.abs(bend_low)

    theta_body_u = _unwrap(theta_body.copy())
    if smooth_window and smooth_window >= 3:
        if smooth_window % 2 == 0:
            smooth_window += 1
        k = smooth_window // 2
        pad = np.pad(theta_body_u, (k, k), mode='edge')
        kern = np.ones(smooth_window) / smooth_window
        theta_body_u = np.convolve(pad, kern, mode='valid')

    dt = 1.0 / float(frame_rate)
    ang_vel_body = np.gradient(theta_body_u, dt)   # rad/s

    timeseries = dict(
        theta_body=theta_body,
        theta_head=theta_head,
        theta_seg_head_neck=theta_seg_head_neck,
        theta_seg_neck_mid=theta_seg_neck_mid,
        theta_seg_mid_low=theta_seg_mid_low,
        theta_seg_low_tail=theta_seg_low_tail,
        head_body_misalignment=head_body_misalignment,
        bend_neck=bend_neck,
        bend_mid=bend_mid,
        bend_low=bend_low,
        ang_vel_body=ang_vel_body,                 # rad/s
        tail_bend_index=tail_bend_index,
    )

    def _stats(x: np.ndarray) -> Dict[str, float]:
        x = x[np.isfinite(x)]
        if x.size == 0:
            return dict(mean=np.nan, std=np.nan, max=np.nan, p95=np.nan)
        return dict(
            mean=float(np.nanmean(x)),
            std=float(np.nanstd(x)),
            max=float(np.nanmax(x)),
            p95=float(np.nanpercentile(x, 95)),
        )

    summary = {
        "head_body_misalignment": _stats(head_body_misalignment),  # radians
        "tail_bend_index":        _stats(tail_bend_index),         # radians
        "ang_vel_body":           _stats(ang_vel_body),            # rad/s
        "abs_bend_neck":          _stats(np.abs(bend_neck)),       # radians
        "abs_bend_mid":           _stats(np.abs(bend_mid)),        # radians
        "abs_bend_low":           _stats(np.abs(bend_low)),        # radians
        # Include meta so the batch can compute per-minute views consistently
        "_meta": {"trial_length_s": float(trial_length_s), "frame_rate": float(frame_rate)},
    }

    valid = np.ones(len(theta_body), dtype=bool)
    return timeseries, summary, valid

# ---------- batch (short, no try/except) ----------
def batch_angle_features(
    conn,
    id_list: List[int],
    table: str = "dlc_table",
    likelihood_threshold: float = 0.5,
    smooth_window: Optional[int] = None,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for tid in id_list:
        ts, sm, _ = angle_features_for_trial(
            conn, tid, table=table,
            likelihood_threshold=likelihood_threshold,
            smooth_window=smooth_window,
        )

        # meta
        trial_len_s = sm["_meta"]["trial_length_s"]
        minutes = trial_len_s / 60.0 if np.isfinite(trial_len_s) and trial_len_s > 0 else np.nan

        # Per-minute scaling: only for *rates* (ang_vel_body is in rad/s → rad/min by *60).
        ang_mean_per_min = sm["ang_vel_body"]["mean"] * 60.0 if np.isfinite(sm["ang_vel_body"]["mean"]) else np.nan
        ang_p95_per_min  = sm["ang_vel_body"]["p95"]  * 60.0 if np.isfinite(sm["ang_vel_body"]["p95"])  else np.nan

        rows.append(dict(
            trial_id=tid,
            trial_length_s=trial_len_s,
            minutes=minutes,

            # orientation/bend magnitudes (unitless radians): keep as-is
            head_body_misalignment_mean=sm["head_body_misalignment"]["mean"],
            head_body_misalignment_p95 =sm["head_body_misalignment"]["p95"],
            tail_bend_index_mean       =sm["tail_bend_index"]["mean"],
            tail_bend_index_p95        =sm["tail_bend_index"]["p95"],
            abs_bend_neck_mean         =sm["abs_bend_neck"]["mean"],
            abs_bend_mid_mean          =sm["abs_bend_mid"]["mean"],
            abs_bend_low_mean          =sm["abs_bend_low"]["mean"],

            # angular velocity (rate) in rad/s
            ang_vel_body_mean_s        =sm["ang_vel_body"]["mean"],
            ang_vel_body_p95_s         =sm["ang_vel_body"]["p95"],

            # per-minute view (rad/min)
            ang_vel_body_mean_min      =ang_mean_per_min,
            ang_vel_body_p95_min       =ang_p95_per_min,
        ))
    return pd.DataFrame(rows)
