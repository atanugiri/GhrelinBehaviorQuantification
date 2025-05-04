
import os
import psycopg2
from extract_animal_name import extract_animal_name
from extract_maze_number import extract_maze_number
from extract_task_name import extract_task_name
from extract_health_name import extract_health_name
from calculate_total_distance_20min import calculate_total_distance_20min
from calculate_time_in_roi_20min import calculate_time_in_roi_20min
from count_stopping_points import count_stopping_points


def is_valid_csv(path, id_):
    if path is None or not str(path).endswith('.csv'):
        print(f"Skipping ID {id_} — missing or non-CSV path.")
        return False
    if not os.path.exists(path):
        print(f"File not found for ID {id_}: {path}")
        return False
    return True

def update_column(column_name):
    conn = psycopg2.connect(dbname="deeplabcut_db", user="postgres", password=1234)
    cursor = conn.cursor()

    if column_name == "distance":
        updates = []
        cursor.execute("""
            ALTER TABLE dlc_files ADD COLUMN IF NOT EXISTS distance FLOAT;
        """)
        cursor.execute("SELECT id, normalized_path FROM dlc_files")
        rows = cursor.fetchall()

        for row in rows:
            id_, path = row
            if not is_valid_csv(path, id_):
                continue
            try:
                total_distance = calculate_total_distance_20min(path)
            except Exception as e:
                print(f"Error for ID {id_}: {e}")
                continue

            if total_distance is not None:
                updates.append((total_distance, id_))
                print(f"Updated distance for ID {id_}: {total_distance:.2f}")
            else:
                print(f"Skipping ID {id_} — calculation failed.")

        if updates:
            cursor.executemany("UPDATE dlc_files SET distance = %s WHERE id = %s", updates)

    elif column_name == "stop_count":
        updates = []
        cursor.execute("""
            ALTER TABLE dlc_files ADD COLUMN IF NOT EXISTS stop_count INT;
        """)
        cursor.execute("SELECT id, normalized_path FROM dlc_files")
        rows = cursor.fetchall()

        for row in rows:
            id_, path = row
            if not is_valid_csv(path, id_):
                continue
            try:
                stop_count = count_stopping_points(path)
            except Exception as e:
                print(f"Error for ID {id_}: {e}")
                continue

            if stop_count is not None:
                updates.append((stop_count, id_))
                print(f"Updated stop_count for ID {id_}: {stop_count}")
            else:
                print(f"Skipping ID {id_} — calculation failed.")

        if updates:
            cursor.executemany("UPDATE dlc_files SET stop_count = %s WHERE id = %s", updates)
            
    elif column_name == "time_in_roi":
        updates = []
        cursor.execute("""
            ALTER TABLE dlc_files ADD COLUMN IF NOT EXISTS time_in_roi FLOAT;
        """)
        cursor.execute("SELECT id, normalized_path, maze FROM dlc_files")
        rows = cursor.fetchall()

        for row in rows:
            id_, path, maze = row
            if not is_valid_csv(path, id_):
                continue
            try:
                time_in_roi = calculate_time_in_roi_20min(path, maze=int(maze), plot=False)
            except Exception as e:
                print(f"Error for ID {id_}: {e}")
                continue

            if time_in_roi is not None:
                updates.append((time_in_roi, id_))
                print(f"Updated time_in_roi for ID {id_}: {time_in_roi:.2f}")
            else:
                print(f"Skipping ID {id_} — calculation failed.")

        if updates:
            cursor.executemany("UPDATE dlc_files SET time_in_roi = %s WHERE id = %s", updates)

    elif column_name == "health":
        cursor.execute("SELECT id, name FROM dlc_files")
        rows = cursor.fetchall()
        for row in rows:
            id_, name_from_db = row
            value = extract_health_name(name_from_db) if name_from_db else None
            if value is not None:
                cursor.execute(
                    "UPDATE dlc_files SET health = %s WHERE id = %s",
                    (value, id_)
                )
                print(f"Updated health for ID {id_}: {value}")
            else:
                print(f"Could not extract health for ID {id_}")

    else:
        cursor.execute("SELECT id, coord_path FROM dlc_files")
        rows = cursor.fetchall()
        for row in rows:
            id_, coord_path = row
            filename = os.path.basename(coord_path)

            if column_name == "name":
                value = extract_animal_name(filename)
            elif column_name == "maze":
                value = extract_maze_number(filename)
            elif column_name == "gender":
                value = None
            elif column_name == "genotype":
                value = None
            elif column_name == "task":
                value = extract_task_name(filename)
            elif column_name == "date":
                value = None
            else:
                print(f"Unknown column: {column_name}")
                continue

            if value is not None:
                cursor.execute(
                    f"UPDATE dlc_files SET {column_name} = %s WHERE id = %s",
                    (value, id_)
                )
                print(f"Updated {column_name} for ID {id_}: {value}")
            else:
                print(f"Could not extract {column_name} for ID {id_}")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"All values for '{column_name}' updated.")
