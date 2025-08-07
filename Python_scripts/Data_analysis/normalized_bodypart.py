import numpy as np
import pandas as pd
import cv2

def get_normalized_bodypart(trial_id, conn, bodypart='Midback', 
                                    table='dlc_table', 
                                    likelihood_threshold=0.5, 
                                    normalize=True,
                                    interpolate=True,
                                    use_homography=False):
    """
    Load and normalize bodypart (x, y) trajectory from DLC CSV.

    Args:
        trial_id: int
        conn: DB connection
        bodypart: str
        table: str, database table name
        likelihood_threshold: float
        normalize: bool, whether to normalize (min-max or homography)
        interpolate: bool, interpolate low-confidence points
        use_homography: bool, use homography normalization instead of min-max

    Returns:
        x_vals, y_vals: numpy arrays
    """
    q = f"SELECT csv_file_path FROM {table} WHERE id = %s"
    df_meta = pd.read_sql_query(q, conn, params=(trial_id,))
    if df_meta.empty:
        print(f"[WARNING] Trial {trial_id} not found in table.")
        return None, None

    csv_path = df_meta['csv_file_path'][0]

    try:
        df_dlc = pd.read_csv(csv_path, header=[1, 2], index_col=0)

        x = df_dlc[(bodypart, 'x')].copy()
        y = df_dlc[(bodypart, 'y')].copy()
        p = df_dlc[(bodypart, 'likelihood')]

        # Set low-likelihood to NaN
        x[p < likelihood_threshold] = np.nan
        y[p < likelihood_threshold] = np.nan

        if interpolate:
            x = pd.Series(x).interpolate(limit_direction='both')
            y = pd.Series(y).interpolate(limit_direction='both')

        x_vals = x.to_numpy()
        y_vals = y.to_numpy()

        if normalize:
            if use_homography:
                corners = []
                for i in range(1, 5):
                    cx = df_dlc[('Corner' + str(i), 'x')]
                    cy = df_dlc[('Corner' + str(i), 'y')]
                    cp = df_dlc[('Corner' + str(i), 'likelihood')]

                    cx[cp < likelihood_threshold] = np.nan
                    cy[cp < likelihood_threshold] = np.nan

                    corners.append((np.nanmedian(cx), np.nanmedian(cy)))

                if all(not np.isnan(pt[0]) and not np.isnan(pt[1]) for pt in corners):
                    src_pts = np.array(corners, dtype=np.float32)
                    dst_pts = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
                    H, _ = cv2.findHomography(src_pts, dst_pts)

                    points = np.vstack([x_vals, y_vals]).T
                    ones = np.ones((points.shape[0], 1))
                    homogenous_points = np.hstack([points, ones])
                    normalized = (H @ homogenous_points.T).T
                    normalized /= normalized[:, 2][:, None]

                    x_vals = normalized[:, 0]
                    y_vals = normalized[:, 1]
                else:
                    print(f"[WARNING] Trial {trial_id}: Homography failed due to missing corner medians. Falling back to min-max.")
                    x_vals = (x_vals - np.nanmin(x_vals)) / (np.nanmax(x_vals) - np.nanmin(x_vals) + 1e-8)
                    y_vals = (y_vals - np.nanmin(y_vals)) / (np.nanmax(y_vals) - np.nanmin(y_vals) + 1e-8)

            else:
                x_vals = (x_vals - np.nanmin(x_vals)) / (np.nanmax(x_vals) - np.nanmin(x_vals) + 1e-8)
                y_vals = (y_vals - np.nanmin(y_vals)) / (np.nanmax(y_vals) - np.nanmin(y_vals) + 1e-8)

        return x_vals, y_vals

    except Exception as e:
        print(f"[ERROR] Failed to process {csv_path} for trial {trial_id}: {e}")
        return None, None
