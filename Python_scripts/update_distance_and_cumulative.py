import psycopg2
from calculate_total_distance_custom import calculate_total_distance_custom
import os

def is_valid_csv(path, id_):
    if path is None or not str(path).endswith('.csv'):
        print(f"Skipping ID {id_} — missing or non-CSV path.")
        return False
    if not os.path.exists(path):
        print(f"File not found for ID {id_}: {path}")
        return False
    return True

def update_distance_and_cumulative():
    conn = psycopg2.connect(dbname="deeplabcut_db", user="postgres", password="1234")
    cursor = conn.cursor()

    # Ensure column exists
    cursor.execute("""
        ALTER TABLE dlc_files
        ADD COLUMN IF NOT EXISTS distance FLOAT,
        ADD COLUMN IF NOT EXISTS cumulative_distance FLOAT[];
    """)
    conn.commit()
    
    cursor.execute("SELECT id, normalized_path FROM dlc_files")
    rows = cursor.fetchall()

    for id_, path in rows:
        print(f"Processing ID {id_}, path: {path}")
        if not is_valid_csv(path, id_):
            continue

        try:
            total_distance, cumulative = calculate_total_distance_custom(path)
        except Exception as e:
            print(f"Error for ID {id_}: {e}")
            continue

        if total_distance is not None and cumulative is not None:
            cursor.execute("""
                UPDATE dlc_files
                SET distance = %s,
                    cumulative_distance = %s
                WHERE id = %s;
            """, (total_distance, list(cumulative), id_))
            print(f"ID {id_} updated: total={total_distance:.2f}, length={len(cumulative)}")
        else:
            print(f"Skipping ID {id_} — calculation failed.")

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    update_distance_and_cumulative()
