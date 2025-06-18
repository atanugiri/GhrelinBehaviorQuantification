import numpy as np
import pandas as pd
import cv2

def normalize_bodypart_by_id(conn, id, bodypart='head'):
    """
    Normalize (x, y) trajectory of a bodypart using homography transform
    based on the median positions of Corner1–Corner4.
    """

    def safe_array(val):
        if isinstance(val, (list, np.ndarray)):
            return np.array(val)
        try:
            return np.array(eval(val))
        except Exception:
            raise ValueError(f"Cannot convert: {val}")

    # Query bodypart + corners
    query = f"""
    SELECT 
        {bodypart}_x, {bodypart}_y,
        corner1_x, corner1_y,
        corner2_x, corner2_y,
        corner3_x, corner3_y,
        corner4_x, corner4_y
    FROM dlc_table
    WHERE id = {id};
    """
    df = pd.read_sql_query(query, conn)
    if df.empty:
        print(f"❌ No data found for ID {id}")
        return None, None

    try:
        row = df.iloc[0]

        # Bodypart trajectory
        x_vals = pd.Series(safe_array(row[f"{bodypart}_x"])).interpolate(limit_direction='both').to_numpy()
        y_vals = pd.Series(safe_array(row[f"{bodypart}_y"])).interpolate(limit_direction='both').to_numpy()

        # Corner medians
        corners = []
        for i in range(1, 5):
            cx = safe_array(row[f"corner{i}_x"])
            cy = safe_array(row[f"corner{i}_y"])
            corners.append([np.nanmedian(cx), np.nanmedian(cy)])

        src_pts = np.array(corners, dtype=np.float32)

        if np.isnan(src_pts).any():
            print(f"❌ Invalid corner values for ID {id}")
            return None, None

        # Match your annotation order: top-right → top-left → bottom-left → bottom-right
        dst_pts = np.array([
            [1, 0],  # corner1 (top-right)
            [0, 0],  # corner2 (top-left)
            [0, 1],  # corner3 (bottom-left)
            [1, 1],  # corner4 (bottom-right)
        ], dtype=np.float32)

        # Compute homography
        H, _ = cv2.findHomography(src_pts, dst_pts)
        if H is None:
            print(f"❌ Homography computation failed for ID {id}")
            return None, None

        # Transform trajectory
        points = np.vstack([x_vals, y_vals]).T.astype(np.float32)  # shape (N, 2)
        norm_pts = cv2.perspectiveTransform(points[:, None, :], H).squeeze()

        x_norm, y_norm = norm_pts[:, 0], norm_pts[:, 1]
        return x_norm, y_norm

    except Exception as e:
        print(f"❌ Error processing ID {id}: {e}")
        return None, None
