import numpy as np
import pandas as pd

# ---- small utilities ----
def _angle_of(v):
    """Angle of a 2D vector in radians, in (-pi, pi]."""
    return np.arctan2(v[..., 1], v[..., 0])

def _unit(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        u = np.where(n > 0, v / n, np.nan)
    return u

def _angle_between(u, v):
    """Signed smallest angle from u to v (radians) using atan2 of cross/dot."""
    u = _unit(u); v = _unit(v)
    dot = np.sum(u * v, axis=-1)
    cross_z = u[..., 0]*v[..., 1] - u[..., 1]*v[..., 0]
    return np.arctan2(cross_z, dot)

def _unwrap(a):
    """Unwrap angle time series (radians)."""
    return np.unwrap(a)

def _nan_drop_mask(*arrs):
    """Frames where all provided arrays are finite."""
    masks = [np.isfinite(a).all(axis=-1) if a.ndim==2 else np.isfinite(a) for a in arrs]
    m = np.logical_and.reduce(masks)
    return m

# ---- core feature extractor ----
def angle_features_from_spine(
    head, neck, midback, lowerback, tailbase, fps, smooth_window=None
):
    """
    Parameters
    ----------
    head, neck, midback, lowerback, tailbase : np.ndarray of shape (T, 2)
        DLC (x,y) per frame for each bodypart.
    fps : float
        Frames per second.
    smooth_window : int or None
        Optional odd window length for boxcar smoothing of angle time series (after unwrapping).

    Returns
    -------
    timeseries : dict of np.ndarray
        Keys: 'theta_body', 'theta_head', 'theta_seg_head_neck', 'theta_seg_neck_mid',
              'theta_seg_mid_low', 'theta_seg_low_tail', 'head_body_misalignment',
              'bend_neck', 'bend_mid', 'bend_low', 'ang_vel_body', 'tail_bend_index'
    summary : dict
        Aggregate statistics (mean, std, max, p95) for selected features.
    valid_index : np.ndarray (bool)
        Mask of frames kept after NaN filtering.
    """
    # Build segment vectors per frame
    v_tail_head = head - tailbase
    v_head_neck = head - neck
    v_neck_mid  = neck - midback
    v_mid_low   = midback - lowerback
    v_low_tail  = lowerback - tailbase

    # Need these bodyparts for different computations
    mask_axis = _nan_drop_mask(v_tail_head)
    mask_head = _nan_drop_mask(v_head_neck)
    mask_neck = _nan_drop_mask(v_neck_mid)
    mask_mid  = _nan_drop_mask(v_mid_low)
    mask_low  = _nan_drop_mask(v_low_tail)

    # Global valid frames = need everything for a clean pass
    valid = mask_axis & mask_head & mask_neck & mask_mid & mask_low

    # Drop invalid frames
    v_tail_head = v_tail_head[valid]
    v_head_neck = v_head_neck[valid]
    v_neck_mid  = v_neck_mid[valid]
    v_mid_low   = v_mid_low[valid]
    v_low_tail  = v_low_tail[valid]

    # Absolute segment angles (against arena x-axis)
    theta_body = _angle_of(v_tail_head)
    theta_head = _angle_of(v_head_neck)
    theta_seg_head_neck = _angle_of(v_head_neck)
    theta_seg_neck_mid  = _angle_of(v_neck_mid)
    theta_seg_mid_low   = _angle_of(v_mid_low)
    theta_seg_low_tail  = _angle_of(v_low_tail)

    # Head-body misalignment (signed, radians)
    head_body_misalignment = _angle_between(v_tail_head, v_head_neck)

    # Local bend angles at joints (signed turn at the middle point)
    # bend at Neck: (Neck←Head) to (Neck→Midback)
    bend_neck = _angle_between(-v_head_neck, -v_neck_mid)  # vectors pointing away from neck
    # bend at Midback: (Mid←Neck) to (Mid→Lower)
    bend_mid  = _angle_between(-v_neck_mid, -v_mid_low)
    # bend at Lowerback: (Low←Mid) to (Low→Tail)
    bend_low  = _angle_between(-v_mid_low, -v_low_tail)

    # Tail bend index (overall curvature): sum of absolute local bends
    tail_bend_index = np.abs(bend_neck) + np.abs(bend_mid) + np.abs(bend_low)

    # Unwrap continuous angles for derivatives
    theta_body_u = _unwrap(theta_body.copy())

    # Optional smoothing of the unwrapped angles (simple moving average)
    if smooth_window and smooth_window >= 3 and smooth_window % 2 == 0:
        smooth_window += 1  # enforce odd
    if smooth_window and smooth_window >= 3:
        def _movavg(x, w):
            k = w // 2
            pad = np.pad(x, (k, k), mode='edge')
            kern = np.ones(w) / w
            return np.convolve(pad, kern, mode='valid')
        theta_body_u = _movavg(theta_body_u, smooth_window)

    # Angular velocity (turn rate) in rad/s from unwrapped body axis
    dt = 1.0 / float(fps)
    ang_vel_body = np.gradient(theta_body_u, dt)

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
        ang_vel_body=ang_vel_body,
        tail_bend_index=tail_bend_index,
    )

    # Summary stats helper
    def _stats(x):
        x = x[np.isfinite(x)]
        if x.size == 0:
            return dict(mean=np.nan, std=np.nan, max=np.nan, p95=np.nan)
        return dict(mean=float(np.nanmean(x)),
                    std=float(np.nanstd(x)),
                    max=float(np.nanmax(x)),
                    p95=float(np.nanpercentile(x, 95)))

    summary = {
        'head_body_misalignment': _stats(head_body_misalignment),
        'tail_bend_index': _stats(tail_bend_index),
        'ang_vel_body': _stats(ang_vel_body),
        'abs_bend_neck': _stats(np.abs(bend_neck)),
        'abs_bend_mid':  _stats(np.abs(bend_mid)),
        'abs_bend_low':  _stats(np.abs(bend_low)),
    }

    return timeseries, summary, valid

# ---- convenience: from a DLC dataframe with columns like Head_x, Head_y, etc. ----
def angle_features_from_df(df, fps, prefix_map=None, smooth_window=None):
    """
    df: pandas DataFrame with columns for each bodypart x/y.
        Default expected names: Head_x, Head_y, Neck_x, ..., Tailbase_y
    prefix_map: optional dict to remap names, e.g. {'Head':'nose', 'Neck':'neck1', ...}
    """
    def _col(p, ax):  # ax in {'x','y'}
        name = prefix_map.get(p, p) if prefix_map else p
        return df[f"{name}_{ax}"].to_numpy()

    head = np.column_stack([_col('Head','x'), _col('Head','y')])
    neck = np.column_stack([_col('Neck','x'), _col('Neck','y')])
    mid  = np.column_stack([_col('Midback','x'), _col('Midback','y')])
    low  = np.column_stack([_col('Lowerback','x'), _col('Lowerback','y')])
    tail = np.column_stack([_col('Tailbase','x'), _col('Tailbase','y')])

    return angle_features_from_spine(head, neck, mid, low, tail, fps=fps, smooth_window=smooth_window)
