"""
Angle Features Module

This module computes angle-based behavioral features from DeepLabCut pose data,
including head-body misalignment, tail bend indices, and angular velocities.

The main functions are:
- angle_features_for_trial(): Compute angle features for a single trial
- batch_angle_features(): Compute angle features for multiple trials

Author: DeepLabCut Analysis Pipeline
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Import utilities from the new db_utils module
from .db_utils import get_trial_meta, get_csv_path

# ---------- math utils ----------
def _angle_of(v: np.ndarray) -> np.ndarray:
    """Compute the angle of 2D vectors."""
    return np.arctan2(v[:, 1], v[:, 0])

def _unit(v: np.ndarray) -> np.ndarray:
    """Convert vectors to unit vectors, handling zero-length vectors."""
    n = np.linalg.norm(v, axis=1, keepdims=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(n > 0, v / n, np.nan)

def _angle_between(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Compute the signed angle between two sets of 2D vectors."""
    uu, vv = _unit(u), _unit(v)
    dot = np.sum(uu * vv, axis=1)
    cross_z = uu[:, 0]*vv[:, 1] - uu[:, 1]*vv[:, 0]
    return np.arctan2(cross_z, dot)

def _unwrap(a: np.ndarray) -> np.ndarray:
    """Unwrap angles to remove discontinuities."""
    return np.unwrap(a)

# ---------- I/O helpers ----------
def _load_bodyparts_raw(csv_path: str, bodyparts: List[str], likelihood_threshold: float = 0.5) -> Dict[str, np.ndarray]:
    """Load and interpolate bodypart coordinates from DeepLabCut CSV file."""
    # If path is relative, resolve it from project root
    csv_path_obj = Path(csv_path)
    if not csv_path_obj.is_absolute():
        # Get project root (2 levels up from this file: angle_features.py -> Feature_functions -> Python_scripts -> root)
        project_root = Path(__file__).resolve().parents[2]
        csv_path = str(project_root / csv_path)
    
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
    dlc_table: pd.DataFrame,
    trial_id: int,
    likelihood_threshold: float = 0.5,
    smooth_window: Optional[int] = None,
) -> Tuple[Dict[str, np.ndarray], Dict[str, Dict[str, float]], np.ndarray]:
    """
    Compute angle-based features for a single trial.
    
    Args:
        dlc_table: DataFrame containing trial metadata
        trial_id: Trial identifier
        likelihood_threshold: Minimum likelihood for pose data
        smooth_window: Window size for smoothing (optional)
    
    Returns:
        Tuple of (timeseries_dict, summary_dict, valid_frames)
    """
    trial_length_s, frame_rate = get_trial_meta(dlc_table, trial_id)
    if frame_rate is None or not np.isfinite(frame_rate) or frame_rate <= 0:
        raise ValueError(f"Missing/invalid frame_rate for trial {trial_id}.")
    csv_path = get_csv_path(dlc_table, trial_id)
    
    # Optional debug output - remove in production
    # print(f"[INFO] csv path: {csv_path}")

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

# ---------- batch processing ----------
def batch_angle_features(
    dlc_table: pd.DataFrame,
    id_list: List[int],
    likelihood_threshold: float = 0.5,
    smooth_window: Optional[int] = None,
) -> pd.DataFrame:
    """
    Compute angle features for multiple trials.
    
    Args:
        dlc_table: DataFrame containing trial metadata
        id_list: List of trial IDs to process
        likelihood_threshold: Minimum likelihood for pose data
        smooth_window: Window size for smoothing (optional)
    
    Returns:
        DataFrame with angle features for all trials
    """
    rows: List[Dict[str, Any]] = []
    for tid in id_list:
        ts, sm, _ = angle_features_for_trial(
            dlc_table, tid,
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


def main(conn, trial_id):
    """
    Simple demo of angle_features_for_trial().
    
    Args:
        conn: Database connection (required)
        trial_id: Trial ID to analyze (required)
    """
    print("Angle Features Demo")
    print("=" * 30)
    print(f"📊 Trial ID: {trial_id}")
    
    try:
        print(f"🧮 Computing angle features for trial {trial_id}...")
        timeseries, summary, valid = angle_features_for_trial(conn, trial_id)
        
        print(f"✅ Success! Processed {len(timeseries['theta_body'])} frames")
        print(f"📈 Head-body misalignment (mean): {summary['head_body_misalignment']['mean']:.3f} rad")
        print(f"📈 Tail bend index (mean): {summary['tail_bend_index']['mean']:.3f} rad")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check trial ID, CSV file, and database connection")


if __name__ == '__main__':
    import argparse
    import sys
    from pathlib import Path
    
    # Add project root to path for config import
    project_root = Path(__file__).parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    from Python_scripts.config import get_conn
    
    parser = argparse.ArgumentParser(description='Run angle features analysis on a trial')
    parser.add_argument('trial_id', type=int, help='Trial ID to analyze')
    
    args = parser.parse_args()
    
    try:
        print("🔗 Connecting to database...")
        conn = get_conn()
        print(f"✅ Connected! Running analysis for trial {args.trial_id}")
        
        main(conn, args.trial_id)
        
        conn.close()
        print("🔗 Database connection closed")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        print("Make sure your database credentials are set in .env file")
        sys.exit(1)
