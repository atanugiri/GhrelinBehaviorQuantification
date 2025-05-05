import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_grouped_cumulative_distance(group_dict):
    conn = psycopg2.connect(dbname="deeplabcut_db", user="postgres", password="1234")
    cursor = conn.cursor()

    plt.figure(figsize=(10, 6))
    colors = ['blue', 'green', 'orange', 'red']
    
    for (label, ids), color in zip(group_dict.items(), colors):
        all_curves = []

        for id_ in ids:
            cursor.execute("""
                SELECT cumulative_distance
                FROM dlc_files
                WHERE id = %s AND cumulative_distance IS NOT NULL;
            """, (id_,))
            result = cursor.fetchone()

            if result and result[0]:
                cumulative = result[0]
                all_curves.append(cumulative)
            else:
                print(f"⚠️ No cumulative_distance found for ID {id_} ({label})")

        # Compute and plot average + SEM
        if all_curves:
            max_len = max(len(c) for c in all_curves)
            padded = np.array([
                np.pad(c, (0, max_len - len(c)), constant_values=np.nan) for c in all_curves
            ])
            mean_curve = np.nanmean(padded, axis=0)
            sem_curve = np.nanstd(padded, axis=0) / np.sqrt(np.sum(~np.isnan(padded), axis=0))

            plt.plot(mean_curve, label=label, color=color, linewidth=2.5)
            plt.fill_between(np.arange(len(mean_curve)),
                             mean_curve - sem_curve,
                             mean_curve + sem_curve,
                             color=color, alpha=0.2)

    conn.close()

    plt.xlabel("Frame index")
    plt.ylabel("Cumulative Distance (pixels)")
    plt.title("Cumulative Distance over Time by Health Group")
    plt.legend()
    plt.tight_layout()
    plt.show()
