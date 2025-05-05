import psycopg2
import pandas as pd

def extract_treatment_ids(task, health):
    valid_tasks = {'food_light', 'food_only', 'light_only', 'toy_light', 'toy_only'}
    valid_health = {'Excitatory', 'Ghrelin', 'Inhibitory', 'Saline'}
    
    if task not in valid_tasks:
        raise ValueError(f"Invalid task: {task}")
    if health not in valid_health:
        raise ValueError(f"Invalid health: {health}")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname="deeplabcut_db",
            user="postgres",
            password="1234",
            host="localhost",
            port="5432"
        )

        query = """
            SELECT id
            FROM dlc_files
            WHERE task = %s AND health = %s;
        """
        df = pd.read_sql_query(query, conn, params=(task, health))
        conn.close()
        return df['id'].tolist()

    except Exception as e:
        print(f"❌ Error during query: {e}")
        return []
