import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

def plot_cumulative_distance(ids_to_plot):
    conn = psycopg2.connect(dbname="deeplabcut_db", user="postgres", password="1234")
    cursor = conn.cursor()

    for id_ in ids_to_plot:
        cursor.execute("""
            SELECT cumulative_distance
            FROM dlc_files
            WHERE id = %s AND cumulative_distance IS NOT NULL;
        """, (id_,))
        result = cursor.fetchone()

        if result and result[0]:
            cumulative = result[0]  # This will be a list of floats (FLOAT[])
            plt.plot(cumulative, label=f"ID {id_}")
        else:
            print(f"No cumulative_distance found for ID {id_}")

    conn.close()

    plt.xlabel("Frame index")
    plt.ylabel("Cumulative Distance (pixels)")
    plt.title("Cumulative Distance over Time")
    plt.legend()
    plt.tight_layout()
    plt.show()
    