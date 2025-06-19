import sys
import os
import numpy as np

# Setup: import once
extract_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Extract_db_columns")
)
if extract_path not in sys.path:
    sys.path.append(extract_path)

from get_trial_length import get_trial_length

def insert_trial_length(ids, conn):
    cursor = conn.cursor()

    # Ensure columns exist
    cursor.execute("ALTER TABLE dlc_table ADD COLUMN IF NOT EXISTS trial_length FLOAT;")

    for id_ in ids:
        trial_length = get_trial_length(conn, id_)

        if trial_length is None:
            print(f"Skipping ID {id_}.")
            continue

        try:
            cursor.execute(f"UPDATE dlc_table SET trial_length = %s WHERE id = %s;", (trial_length, id_))
            print(f"✅ Inserted trial_length for ID {id_}")
        except Exception as e:
            print(f"❌ DB update failed for ID {id_}: {e}")

    conn.commit()
    cursor.close()
                
