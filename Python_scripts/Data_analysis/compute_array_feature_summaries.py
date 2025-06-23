import numpy as np
import pandas as pd
from scipy.stats import entropy

def compute_array_feature_summaries(conn, ids, feature):
    """
    Compute summary stats (mean, max, std, entropy, area, z-mean-abs)
    for a FLOAT[] feature in dlc_table, without modifying the database.

    Parameters:
        conn: psycopg2 or SQLAlchemy connection
        ids: List of trial IDs to process
        feature: Name of the FLOAT[] column (e.g., 'curvature')

    Returns:
        A pandas DataFrame with columns:
            id, <feature>_mean, ..., <feature>_z_mean_abs
    """
    results = []

    for id_ in ids:
        try:
            query = f"""
                SELECT {feature}
                FROM dlc_table
                WHERE id = %s AND {feature} IS NOT NULL;
            """
            df = pd.read_sql_query(query, conn, params=(id_,))
            if df.empty or df[feature][0] is None:
                continue

            arr = np.array(df[feature][0])
            arr = arr[~np.isnan(arr)]

            if len(arr) < 2:
                summary = [np.nan] * 6
            else:
                hist, _ = np.histogram(arr, bins=30, density=True)
                hist = hist[hist > 0]
                z_arr = (arr - np.mean(arr)) / np.std(arr)

                summary = [
                    float(np.mean(arr)),
                    float(np.max(arr)),
                    float(np.std(arr)),
                    float(entropy(hist)) if len(hist) > 0 else np.nan,
                    float(np.sum(arr)),
                    float(np.mean(np.abs(z_arr)))
                ]

            results.append({
                'id': id_,
                f'{feature}_mean': summary[0],
                f'{feature}_max': summary[1],
                f'{feature}_std': summary[2],
                f'{feature}_entropy': summary[3],
                f'{feature}_area': summary[4],
                f'{feature}_z_mean_abs': summary[5]
            })

        except Exception as e:
            print(f"⚠️ Error for ID {id_}: {e}")
            continue

    return pd.DataFrame(results)
