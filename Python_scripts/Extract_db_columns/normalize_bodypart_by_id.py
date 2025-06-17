import numpy as np
import pandas as pd

def normalize_bodypart_by_id(conn, id, bodypart='head'):
    """
    Normalize the (x, y) coordinates of a body part using min-max normalization
    bounded by the 4 maze corner coordinates (Corner1–Corner4).

    Args:
        conn: psycopg2 or SQLAlchemy connection
        id: trial ID
        bodypart: body part name (e.g., 'head')

    Returns:
        x_norm, y_norm: normalized numpy arrays of the same length as original trace
    """
    def safe_array(val):
        if isinstance(val, (list, np.ndarray)):
            return np.array(val)
        try:
            return np.array(eval(val))
        except Exception:
            raise ValueError(f"Cannot convert: {val}")

    query = f"""
    SELECT 
        {bodypart}_x, {bodypart}_y,
        corner1_x, corner1_y,
        corner2_x, corner2_y,
        corner3_x, corner3_y,
        corner4_x, corner4_y
    FROM dlc_table
    WHERE id = {id}
    """
    df = pd.read_sql_query(query, conn)

    if df.empty:
        print(f"❌ No data found for ID {id}")
        return None, None

    try:
        row = df.iloc[0]

        # Interpolate body part trace
        x_vals = pd.Series(safe_array(row[f"{bodypart}_x"])).interpolate(limit_direction='both').to_numpy()
        y_vals = pd.Series(safe_array(row[f"{bodypart}_y"])).interpolate(limit_direction='both').to_numpy()

        # Corner arrays
        c1x = safe_array(row['corner1_x'])
        c1y = safe_array(row['corner1_y'])
        c2x = safe_array(row['corner2_x'])
        c2y = safe_array(row['corner2_y'])
        c3x = safe_array(row['corner3_x'])
        c3y = safe_array(row['corner3_y'])
        c4x = safe_array(row['corner4_x'])
        c4y = safe_array(row['corner4_y'])

        # Define min/max bounds from corners
        x_min = np.nanmin([np.nanmin(c1x), np.nanmin(c2x), np.nanmin(c3x), np.nanmin(c4x)])
        x_max = np.nanmax([np.nanmax(c1x), np.nanmax(c2x), np.nanmax(c3x), np.nanmax(c4x)])
        y_min = np.nanmin([np.nanmin(c1y), np.nanmin(c2y), np.nanmin(c3y), np.nanmin(c4y)])
        y_max = np.nanmax([np.nanmax(c1y), np.nanmax(c2y), np.nanmax(c3y), np.nanmax(c4y)])

        x_range = x_max - x_min
        y_range = y_max - y_min

        if x_range == 0 or y_range == 0:
            print(f"❌ Invalid normalization range for ID {id}")
            return None, None

        x_norm = (x_vals - x_min) / x_range
        y_norm = (y_vals - y_min) / y_range

        return x_norm, y_norm

    except Exception as e:
        print(f"❌ Error processing ID {id}: {e}")
        return None, None
