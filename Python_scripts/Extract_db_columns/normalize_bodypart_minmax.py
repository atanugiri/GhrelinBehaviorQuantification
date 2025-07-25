def normalize_bodypart_minmax(df, bodypart='head', likelihood_threshold=0.0):
    import numpy as np
    import pandas as pd

    try:
        # Check if multi-index format exists
        if (bodypart, 'likelihood') in df.columns:
            valid = df[(bodypart, 'likelihood')] >= likelihood_threshold
            x = df[(bodypart, 'x')].where(valid, np.nan)
            y = df[(bodypart, 'y')].where(valid, np.nan)
        else:
            x = df[(bodypart, 'x')]
            y = df[(bodypart, 'y')]

        x_vals = pd.Series(x).interpolate(limit_direction='both').to_numpy()
        y_vals = pd.Series(y).interpolate(limit_direction='both').to_numpy()

        # x_min = np.percentile(x_vals, 0.1)
        # x_max = np.percentile(x_vals, 99.9)
        # y_min = np.percentile(y_vals, 0.1)
        # y_max = np.percentile(y_vals, 99.9)

        # Apply min-max normalization
        x_min, x_max = np.nanmin(x), np.nanmax(x)
        y_min, y_max = np.nanmin(y), np.nanmax(y)

        x_norm = (x_vals - x_min) / (x_max - x_min)
        y_norm = (y_vals - y_min) / (y_max - y_min)

        return x_norm, y_norm

    except Exception as e:
        print(f"❌ Error during min-max normalization: {e}")
        return None, None
