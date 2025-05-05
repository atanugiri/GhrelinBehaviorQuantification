import psycopg2
import pandas as pd
from calculate_acc_jerk_outliers import calculate_acc_jerk_outliers
from psycopg2.extras import execute_values

def update_outliers_to_db():
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname="deeplabcut_db",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    # Make sure the columns exist
    cur.execute("ALTER TABLE dlc_files ADD COLUMN IF NOT EXISTS acc_outliers INT;")
    cur.execute("ALTER TABLE dlc_files ADD COLUMN IF NOT EXISTS jerk_outliers INT;")
    conn.commit()

    # Fetch IDs and paths
    df = pd.read_sql_query("SELECT id, normalized_path FROM dlc_files WHERE normalized_path IS NOT NULL", conn)

    updates = []

    for _, row in df.iterrows():
        id_ = row['id']
        path = row['normalized_path']
        try:
            acc, jerk = calculate_acc_jerk_outliers(path)
            if pd.notna(acc) and pd.notna(jerk):
                updates.append((int(acc), int(jerk), id_))
                print(f"ID {id_}: acc={acc}, jerk={jerk}")
        except Exception as e:
            print(f"ID {id_}: error — {e}")

    # Update all rows efficiently in one step
    if updates:
        execute_values(
            cur,
            """
            UPDATE dlc_files AS d SET
                acc_outliers = u.acc,
                jerk_outliers = u.jerk
            FROM (VALUES %s) AS u(acc, jerk, id)
            WHERE d.id = u.id;
            """,
            updates
        )
        conn.commit()
        print(f"Updated {len(updates)} rows.")

    else:
        print("No updates to apply.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    update_outliers_to_db()
