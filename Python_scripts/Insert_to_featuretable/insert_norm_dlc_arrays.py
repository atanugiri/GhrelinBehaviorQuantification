import sys
import os
import numpy as np

# Setup: import once
extract_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Extract_db_columns")
)
if extract_path not in sys.path:
    sys.path.append(extract_path)

from normalize_bodypart_by_id import normalize_bodypart_by_id

def insert_norm_dlc_arrays(ids, conn, bodypart="head"):
    cursor = conn.cursor()

    # Ensure columns exist
    cursor.execute(f"ALTER TABLE dlc_table ADD COLUMN IF NOT EXISTS {bodypart.lower()}_x_norm FLOAT[];")
    cursor.execute(f"ALTER TABLE dlc_table ADD COLUMN IF NOT EXISTS {bodypart.lower()}_y_norm FLOAT[];")

    for id_ in ids:
        x_vals, y_vals = normalize_bodypart_by_id(conn, id_, bodypart=bodypart)

        if x_vals is None or y_vals is None:
            print(f"Skipping ID {id_} — normalization failed.")
            continue

        x_vals = np.round(x_vals, 3).tolist()
        y_vals = np.round(y_vals, 3).tolist()

        try:
            cursor.execute(f"""
                UPDATE dlc_table
                SET {bodypart.lower()}_x_norm = %s,
                    {bodypart.lower()}_y_norm = %s
                WHERE id = %s;
            """, (x_vals, y_vals, id_))
            print(f"✅ Inserted normalized {bodypart} for ID {id_}")
        except Exception as e:
            print(f"❌ DB update failed for ID {id_}: {e}")

    conn.commit()
    cursor.close()
