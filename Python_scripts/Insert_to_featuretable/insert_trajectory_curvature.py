import sys
import os
import numpy as np

# Setup: import once
motion_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Feature_functions")
)
if motion_path not in sys.path:
    sys.path.append(motion_path)

from compute_trajectory_curvature import compute_trajectory_curvature

def insert_trajectory_curvature(ids, conn):
    cursor = conn.cursor()

    # Ensure columns exist
    cursor.execute("ALTER TABLE dlc_table ADD COLUMN IF NOT EXISTS curvature FLOAT[];")
    cursor.execute("ALTER TABLE dlc_table ADD COLUMN IF NOT EXISTS mean_curv FLOAT;")

    for id_ in ids:
        try:
            curvature, mean_curv = compute_trajectory_curvature(
                conn, id_, bodypart_x='head_x_norm', bodypart_y='head_y_norm', 
                time_limit=1200.0, smooth=True, window=5)
            
        except Exception as e:
            print(f"⚠️ Skipping ID {id_}: {e}")
            continue

        try:
            cursor.execute(
                """
                UPDATE dlc_table
                SET curvature = %s,
                    mean_curv = %s
                WHERE id = %s;
                """,
                (curvature, mean_curv, id_)
            )
            print(f"✅ Inserted motion summary for ID {id_}")
        except Exception as e:
            print(f"❌ DB update failed for ID {id_}: {e}")

    conn.commit()
    cursor.close()
