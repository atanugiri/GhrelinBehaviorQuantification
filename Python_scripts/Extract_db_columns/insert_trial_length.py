import psycopg2
from tqdm import tqdm

def insert_trial_length(id_list, conn, table='dlc_table'):
    """
    Compute trial length as num_frames / frame_rate and update the trial_length column.
    
    Parameters:
        id_list (list): List of trial IDs to update.
        conn: psycopg2 or SQLAlchemy connection.
        table (str): Name of the table to update.
    """
    cursor = conn.cursor()
    updated_count = 0

    for trial_id in tqdm(id_list, desc='Updating trial_length'):
        # Fetch num_frames and frame_rate
        cursor.execute(f"""
            SELECT num_frames, frame_rate FROM {table}
            WHERE id = %s;
        """, (trial_id,))
        row = cursor.fetchone()

        if row is None:
            print(f"[WARNING] Trial ID {trial_id} not found.")
            continue

        num_frames, frame_rate = row

        # Check for None or zero values
        if num_frames is None or frame_rate in (None, 0):
            print(f"[SKIP] ID {trial_id}: num_frames or frame_rate missing/invalid.")
            continue

        trial_length = num_frames / frame_rate

        # Update trial_length
        cursor.execute(f"""
            UPDATE {table}
            SET trial_length = %s
            WHERE id = %s;
        """, (trial_length, trial_id))

        updated_count += 1

    conn.commit()
    print(f"[INFO] Updated trial_length for {updated_count} rows.")
