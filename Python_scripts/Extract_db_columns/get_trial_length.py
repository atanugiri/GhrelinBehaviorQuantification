import pandas as pd

def get_trial_length(conn, trial_id):
    """
    Returns the last timestamp from 't' for a given trial ID in dlc_table.
    """
    query = f"SELECT t FROM dlc_table WHERE id = {trial_id};"
    df = pd.read_sql_query(query, conn)

    if df.empty or df['t'][0] is None:
        return None  # Avoids crash if t is missing or NULL

    time = df['t'][0]
    if not isinstance(time, list) or len(time) == 0:
        return None

    return time[-1]
