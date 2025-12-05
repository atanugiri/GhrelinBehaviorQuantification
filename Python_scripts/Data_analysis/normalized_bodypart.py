import numpy as np
import pandas as pd
import cv2
from pathlib import Path

def get_normalized_bodypart(trial_id, dlc_table, bodypart='Midback', 
                                    likelihood_threshold=0.5, 
                                    normalize=True,
                                    interpolate=True,
                                    use_homography=False):
    """
    Load and normalize bodypart (x, y) trajectory from DLC CSV.

    Args:
        trial_id: int
        dlc_table: pd.DataFrame containing trial metadata with csv_file_path
        bodypart: str
        likelihood_threshold: float
        normalize: bool, whether to normalize (min-max or homography)
        interpolate: bool, interpolate low-confidence points
        use_homography: bool, use homography normalization instead of min-max

    Returns:
        x_vals, y_vals: numpy arrays
    """
    row = dlc_table[dlc_table['id'] == trial_id]
    if row.empty:
        print(f"[WARNING] Trial {trial_id} not found in dlc_table.")
        return None, None

    csv_path = row['csv_file_path'].iloc[0]
    
    if pd.isna(csv_path):
        print(f"[WARNING] Trial {trial_id} has no csv_file_path.")
        return None, None
    
    # If path is relative, resolve it from project root
    if not Path(csv_path).is_absolute():
        # Get project root (2 levels up: normalized_bodypart.py -> Data_analysis -> Python_scripts -> root)
        project_root = Path(__file__).resolve().parents[2]
        csv_path = str(project_root / csv_path)

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

# --- Main Test Block ----------------------------------------------------------
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from Python_scripts.config import load_dlc_table

    # Load dlc_table.csv
    try:
        dlc_table = load_dlc_table()
    except Exception as e:
        print(f"Error loading dlc_table.csv: {e}")
        sys.exit(1)

    # Use first available trial ID for demonstration
    trial_id = int(dlc_table['id'].iloc[0])
    x, y = get_normalized_bodypart(trial_id, dlc_table)
    print(f"Trial ID: {trial_id}")
    print(f"x shape: {None if x is None else x.shape}, y shape: {None if y is None else y.shape}")
    if x is not None and y is not None:
        print(f"x preview: {x[:5]}")
        print(f"y preview: {y[:5]}")

