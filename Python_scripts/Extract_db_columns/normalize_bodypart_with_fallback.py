def normalize_bodypart_with_fallback(df, bodypart='Head', likelihood_threshold=0.5):
    import numpy as np
    import pandas as pd
    import cv2

    try:
        # ---------------------------
        # STEP 0: Setup
        # ---------------------------
        n_frames = len(df)
        n90 = int(n_frames * 0.9)
        df_train = df.iloc[:n90]  # only first 90% for estimation

        # ---------------------------
        # STEP 1: Interpolate bodypart coordinates
        # ---------------------------
        if (bodypart, 'likelihood') in df.columns:
            valid = df[(bodypart, 'likelihood')] >= likelihood_threshold
            x = df[(bodypart, 'x')].where(valid, np.nan)
            y = df[(bodypart, 'y')].where(valid, np.nan)
        else:
            x = df[(bodypart, 'x')]
            y = df[(bodypart, 'y')]

        x_vals = pd.Series(x).interpolate(limit_direction='both').to_numpy()
        y_vals = pd.Series(y).interpolate(limit_direction='both').to_numpy()

        # ---------------------------
        # STEP 2: Try homography from corner medians
        # ---------------------------
        src_pts = []
        dst_pts = []
        dst_mapping = {
            1: [1, 0],  # top-right
            2: [0, 0],  # top-left
            3: [0, 1],  # bottom-left
            4: [1, 1],  # bottom-right
        }

        for i in [1, 2, 3, 4]:
            bp = f'Corner{i}'
            if (bp, 'likelihood') not in df.columns:
                continue
            lx = df_train[(bp, 'likelihood')]
            mask = lx >= likelihood_threshold
            cx = df_train[(bp, 'x')].where(mask, np.nan)
            cy = df_train[(bp, 'y')].where(mask, np.nan)

            if cx.isna().all() or cy.isna().all():
                continue

            src_pts.append([np.nanmedian(cx), np.nanmedian(cy)])
            dst_pts.append(dst_mapping[i])

        if len(src_pts) >= 4:
            H, _ = cv2.findHomography(np.array(src_pts, np.float32),
                                      np.array(dst_pts, np.float32))
            if H is not None:
                pts = np.vstack([x_vals, y_vals]).T.astype(np.float32)
                norm_pts = cv2.perspectiveTransform(pts[:, None, :], H).squeeze()
                print("✅ Homography normalization applied.")
                return norm_pts[:, 0], norm_pts[:, 1]

        # ---------------------------
        # STEP 3: Fallback min-max normalization
        # ---------------------------
        print("⚠️ Falling back to min-max normalization")

        # Define good range, only using first 90%
        x_train = pd.Series(x_vals[:n90])
        y_train = pd.Series(y_vals[:n90])

        x_good = x_train[(x_train >= 100) & (x_train <= 270)]
        y_good = y_train[(y_train >= 100) & (y_train <= 270)]

        if len(x_good) < 10 or len(y_good) < 10:
            raise ValueError("Too few valid points for min-max fallback.")

        x_min = np.percentile(x_good, 1)
        x_max = np.percentile(x_good, 99)
        y_min = np.percentile(y_good, 1)
        y_max = np.percentile(y_good, 99)

        # Normalize full series using bounds
        x_norm_all = (x_vals - x_min) / (x_max - x_min)
        y_norm_all = (y_vals - y_min) / (y_max - y_min)

        # Mask and fill outliers to preserve length
        good_mask = (x_vals >= 100) & (x_vals <= 270) & \
                    (y_vals >= 100) & (y_vals <= 270)

        x_norm = pd.Series(np.where(good_mask, x_norm_all, np.nan)).fillna(method='ffill').fillna(method='bfill').to_numpy()
        y_norm = pd.Series(np.where(good_mask, y_norm_all, np.nan)).fillna(method='ffill').fillna(method='bfill').to_numpy()

        return x_norm, y_norm

    except Exception as e:
        print(f"❌ Error during normalization: {e}")
        return None, None
