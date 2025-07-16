def normalize_bodypart_from_csv(df, bodypart='head', likelihood_threshold=0.3):
    import numpy as np
    import pandas as pd
    import cv2

    try:
        # If likelihood column exists
        if f"{bodypart}_likelihood" in df.columns:
            likelihood = df[f"{bodypart}_likelihood"]
            x = df[f"{bodypart}_x"].where(likelihood >= likelihood_threshold, np.nan)
            y = df[f"{bodypart}_y"].where(likelihood >= likelihood_threshold, np.nan)
        else:
            x = df[f"{bodypart}_x"]
            y = df[f"{bodypart}_y"]

        x_vals = pd.Series(x).interpolate(limit_direction='both').to_numpy()
        y_vals = pd.Series(y).interpolate(limit_direction='both').to_numpy()

        # Corner medians
        corners = []
        for i in range(1, 5):
            cx = pd.Series(df[f"corner{i}_x"]).to_numpy()
            cy = pd.Series(df[f"corner{i}_y"]).to_numpy()
            corners.append([np.nanmedian(cx), np.nanmedian(cy)])

        src_pts = np.array(corners, dtype=np.float32)

        if np.isnan(src_pts).any():
            print("❌ Invalid corner values in CSV")
            return None, None

        # Your standard unit square mapping
        dst_pts = np.array([
            [1, 0],  # corner1
            [0, 0],  # corner2
            [0, 1],  # corner3
            [1, 1],  # corner4
        ], dtype=np.float32)

        H, _ = cv2.findHomography(src_pts, dst_pts)
        if H is None:
            print("❌ Homography computation failed")
            return None, None

        points = np.vstack([x_vals, y_vals]).T.astype(np.float32)
        norm_pts = cv2.perspectiveTransform(points[:, None, :], H).squeeze()

        return norm_pts[:, 0], norm_pts[:, 1]

    except Exception as e:
        print(f"❌ Error during normalization: {e}")
        return None, None
