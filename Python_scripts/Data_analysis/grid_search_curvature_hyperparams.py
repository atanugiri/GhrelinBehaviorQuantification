import sys
import os
import numpy as np
import pandas as pd

analysis_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Data_analysis")
)
if analysis_path not in sys.path:
    sys.path.append(analysis_path)

from compute_binned_curvature_stats import compute_binned_curvature_stats

def grid_search_curvature_hyperparams(conn, ids_saline, ids_ghrelin,
                                      window_values=[3, 5, 7, 9, 11],
                                      speed_thresh_values=[1e-3, 5e-3, 1e-2, 2e-2, 5e-2],
                                      bin_size=120, time_limit=1200.0):
    """
    Run a 2D grid search over `window` and `speed_thresh` to maximize saline-ghrelin difference.

    Returns:
        DataFrame with ['window', 'speed_thresh', 'score', 'saline', 'ghrelin']
    """
    results = []

    for window in window_values:
        for speed_thresh in speed_thresh_values:
            try:
                df_sal = compute_binned_curvature_stats(
                    conn, ids_saline, 'Saline',
                    window=window, speed_thresh=speed_thresh,
                    bin_size=bin_size, time_limit=time_limit
                )
                df_ghr = compute_binned_curvature_stats(
                    conn, ids_ghrelin, 'Ghrelin',
                    window=window, speed_thresh=speed_thresh,
                    bin_size=bin_size, time_limit=time_limit
                )

                # Use curvature_mean — average across all bins
                saline_mean = df_sal['curvature_mean'].mean()
                ghrelin_mean = df_ghr['curvature_mean'].mean()
                score = saline_mean - ghrelin_mean

                results.append({
                    'window': window,
                    'speed_thresh': speed_thresh,
                    'score': score,
                    'saline': saline_mean,
                    'ghrelin': ghrelin_mean
                })

            except Exception as e:
                print(f"⚠️ window={window}, speed_thresh={speed_thresh} failed: {e}")
                continue

    return pd.DataFrame(results).sort_values(by='score', ascending=False).reset_index(drop=True)
