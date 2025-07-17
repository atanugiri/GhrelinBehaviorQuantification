def normalize_bodypart_minmax(df, bodypart='head', likelihood_threshold=0.3):
    import numpy as np
    import pandas as pd

    try:
        if f"{bodypart}_likelihood" in df.columns:
            valid = df[f"{bodypart}_likelihood"] >= likelihood_threshold
            x = df[f"{bodypart}_x"].where(valid, np.nan)
            y = df[f"{bodypart}_y"].where(valid, np.nan)
        else:
            x = df[f"{bodypart}_x"]
            y = df[f"{bodypart}_y"]

        x_vals = pd.Series(x).interpolate(limit_direction='both').to_numpy()
        y_vals = pd.Series(y).interpolate(limit_direction='both').to_numpy()

        x_min = np.percentile(x_vals, 1)
        x_max = np.percentile(x_vals, 99)
        y_min = np.percentile(y_vals, 1)
        y_max = np.percentile(y_vals, 99)

        x_norm = (x_vals - x_min) / (x_max - x_min)
        y_norm = (y_vals - y_min) / (y_max - y_min)

        return x_norm, y_norm

    except Exception as e:
        print(f"❌ Error during min-max normalization: {e}")
        return None, None
