import sys
import os
import numpy as np

# Setup: import once
motion_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Feature_functions")
)
if motion_path not in sys.path:
    sys.path.append(motion_path)

from compute_motion_features import compute_motion_features

def insert_motion_features(ids, conn, bodypart_x='head_x_norm', bodypart_y='head_y_norm', time_limit=1200.0):
    cursor = conn.cursor()

    # Ensure columns exist
    cursor.execute("ALTER TABLE dlc_table ADD COLUMN IF NOT EXISTS distance FLOAT;")
    cursor.execute("ALTER TABLE dlc_table ADD COLUMN IF NOT EXISTS velocity FLOAT;")
    cursor.execute("ALTER TABLE dlc_table ADD COLUMN IF NOT EXISTS cumulative_distance FLOAT[];")

    for id_ in ids:
        try:
            total_dist, avg_vel, cum_dist = compute_motion_features(
                conn, id_, bodypart_x=bodypart_x, bodypart_y=bodypart_y, time_limit=time_limit)
        except Exception as e:
            print(f"⚠️ Skipping ID {id_}: {e}")
            continue

        try:
            cursor.execute(
                """
                UPDATE dlc_table
                SET distance = %s,
                    velocity = %s,
                    cumulative_distance = %s
                WHERE id = %s;
                """,
                (total_dist, avg_vel, cum_dist, id_)
            )
            print(f"✅ Inserted motion summary for ID {id_}")
        except Exception as e:
            print(f"❌ DB update failed for ID {id_}: {e}")

    conn.commit()
    cursor.close()
