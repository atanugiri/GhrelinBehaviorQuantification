import sys
import os
import numpy as np
import pandas as pd

feature_path = os.path.abspath(
    os.path.join(os.getcwd(), "..", "Python_scripts", "Feature_functions")
)
if feature_path not in sys.path:
    sys.path.append(feature_path)

from batch_time_in_maze_regions_TL import batch_time_in_maze_regions_TL


def find_best_radius_pair_by_difference(conn, saline_ids, ghrelin_ids, 
                                        r1_range=np.arange(0.1, 0.5, 0.05),
                                        r2_offset_range=np.arange(0.05, 0.3, 0.05),
                                        verbose=False):
    """
    Finds (r1, r2) pair that maximizes (saline - ghrelin) zone_middle_frac difference.

    Args:
        conn: psycopg2 or SQLAlchemy connection
        saline_ids: list of trial IDs for Saline group
        ghrelin_ids: list of trial IDs for Ghrelin group
        r1_range: array-like, values to try for r1
        r2_offset_range: array-like, offsets to add to r1 to get r2
        verbose: bool, print progress

    Returns:
        dict with best r1, r2 and full result DataFrame
    """

    records = []

    for r1 in r1_range:
        for offset in r2_offset_range:
            r2 = r1 + offset

            df_sal = batch_time_in_maze_regions_TL(conn, saline_ids, r1=r1, r2=r2)
            df_sal['group'] = 'Saline'

            df_ghr = batch_time_in_maze_regions_TL(conn, ghrelin_ids, r1=r1, r2=r2)
            df_ghr['group'] = 'Ghrelin'

            df_all = pd.concat([df_sal, df_ghr], ignore_index=True)

            mean_sal = df_all[df_all['group'] == 'Saline']['zone_middle_frac'].mean()
            mean_ghr = df_all[df_all['group'] == 'Ghrelin']['zone_middle_frac'].mean()
            difference = mean_sal - mean_ghr

            records.append({
                'r1': r1,
                'r2': r2,
                'mean_saline': mean_sal,
                'mean_ghrelin': mean_ghr,
                'difference': difference
            })

            if verbose:
                print(f"r1={r1:.2f}, r2={r2:.2f} → Δ={difference:.3f} (Sal={mean_sal:.3f}, Ghr={mean_ghr:.3f})")

    df_results = pd.DataFrame(records)
    best_row = df_results[df_results['difference'] == df_results['difference'].max()].iloc[0]

    return {
        'best_pair': best_row.to_dict(),
        'all_results': df_results
    }
