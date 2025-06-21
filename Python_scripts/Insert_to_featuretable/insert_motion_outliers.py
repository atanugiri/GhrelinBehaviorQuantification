import sys
import os
import numpy as np

# Setup: import once
motion_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Feature_functions")
)
if motion_path not in sys.path:
    sys.path.append(motion_path)

from compute_motion_outliers import compute_motion_outliers

def insert_motion_outliers(ids, conn, bodypart_x='head_x_norm', bodypart_y='head_y_norm', time_limit=1200.0):
    cursor = conn.cursor()

    # Ensure columns exist
    cursor.execute("ALTER TABLE dlc_table ADD COLUMN IF NOT EXISTS acc_outlier FLOAT;")
    cursor.execute("ALTER TABLE dlc_table ADD COLUMN IF NOT EXISTS jerk_outlier FLOAT;")

    for id_ in ids:
        try:
            acc_outliers, jerk_outliers = compute_motion_outliers(
                conn, id_, bodypart_x=bodypart_x, bodypart_y=bodypart_y, time_limit=time_limit)
        except Exception as e:
            print(f"⚠️ Skipping ID {id_}: {e}")
            continue

        try:
            cursor.execute(
                """
                UPDATE dlc_table
                SET acc_outlier = %s,
                    jerk_outlier = %s
                WHERE id = %s;
                """,
                (acc_outliers, jerk_outliers, id_)
            )
            print(f"✅ Inserted motion summary for ID {id_}")
        except Exception as e:
            print(f"❌ DB update failed for ID {id_}: {e}")

    conn.commit()
    cursor.close()
