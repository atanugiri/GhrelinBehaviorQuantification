import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_cumulative_distance(ids_to_plot):
    conn = psycopg2.connect(dbname="deeplabcut_db", user="postgres", password="1234")
    cursor = conn.cursor()

    all_curves = []

    for id_ in ids_to_plot:
        cursor.execute("""
            SELECT cumulative_distance
            FROM dlc_files
            WHERE id = %s AND cumulative_distance IS NOT NULL;
        """, (id_,))
        result = cursor.fetchone()

        if result and result[0]:
            cumulative = result[0]  # FLOAT[] column returns a list
            plt.plot(cumulative, alpha=0.4, label=f"ID {id_}")
            all_curves.append(cumulative)
        else:
            print(f"⚠️ No cumulative_distance found for ID {id_}")

    conn.close()

    # Compute and plot average + standard error
    if all_curves:
        max_len = max(len(c) for c in all_curves)
        padded = np.array([
            np.pad(c, (0, max_len - len(c)), constant_values=np.nan) for c in all_curves
        ])
        
        mean_curve = np.nanmean(padded, axis=0)
        sem_curve = np.nanstd(padded, axis=0) / np.sqrt(np.sum(~np.isnan(padded), axis=0))

        plt.plot(mean_curve, color='black', linewidth=2.5, label='Average', zorder=10)
        plt.fill_between(np.arange(len(mean_curve)),
                         mean_curve - sem_curve,
                         mean_curve + sem_curve,
                         color='black', alpha=0.2, label='±1 SEM')

    plt.xlabel("Frame index")
    plt.ylabel("Cumulative Distance (pixels)")
    plt.title("Cumulative Distance over Time")
    plt.legend()
    plt.tight_layout()
    plt.show()
