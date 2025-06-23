import sys
import os
import pandas as pd

analysis_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Data_analysis")
)
if analysis_path not in sys.path:
    sys.path.append(analysis_path)

from compute_binned_curvature_stats import compute_binned_curvature_stats


def optimize_window_for_group_separation(
    conn, saline_ids, ghrelin_ids,
    task_label='LightOnly',
    window_values=[3, 5, 7, 9, 11],
    bin_size=120,
    speed_thresh=1e-2,
    smooth=True
):
    """
    Grid search over 'window' values to find the one that maximizes
    Saline - Ghrelin curvature_mean or curvature_z_mean_abs.
    """

    results = []

    for window in window_values:
        print(f"\n🧪 Testing window={window}")

        df_sal = compute_binned_curvature_stats(
            conn, saline_ids, 'Saline',
            bin_size=bin_size, window=window,
            speed_thresh=speed_thresh, smooth=smooth
        )

        df_ghr = compute_binned_curvature_stats(
            conn, ghrelin_ids, 'Ghrelin',
            bin_size=bin_size, window=window,
            speed_thresh=speed_thresh, smooth=smooth
        )

        # Combine
        df_all = pd.concat([df_sal, df_ghr], ignore_index=True)

        # Objective: difference in mean curvature_z_mean_abs
        mean_sal = df_sal['curvature_z_mean_abs'].mean()
        mean_ghr = df_ghr['curvature_z_mean_abs'].mean()
        score = mean_sal - mean_ghr

        results.append({'window': window, 'score': score, 'saline': mean_sal, 'ghrelin': mean_ghr})

    df_result = pd.DataFrame(results).sort_values(by='score', ascending=False)

    print("\n📊 Window optimization results (best on top):")
    print(df_result)
    return df_result
