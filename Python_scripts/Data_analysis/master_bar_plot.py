import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def master_bar_plot(task_name, feature_name, ylabel=None):
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname="deeplabcut_db",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )

    # Query to fetch 'health', 'name', and the desired feature
    query = f"""
        SELECT health, name, {feature_name}
        FROM dlc_files
        WHERE task = %s AND {feature_name} IS NOT NULL;
    """

    try:
        df = pd.read_sql_query(query, conn, params=(task_name,))
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        conn.close()
        return

    conn.close()

    if df.empty:
        print(f"⚠️ No data found for task '{task_name}' and feature '{feature_name}'.")
        return

    df = df[~((df[feature_name] == 0) & (df['name'].str.startswith('None')))]

    if df.empty:
        print(f"⚠️ No valid data left after filtering for task '{task_name}' and feature '{feature_name}'.")
        return

    # Group by 'health' and calculate mean and SEM (standard error of the mean)
    summary_mean = df.groupby('health')[feature_name].mean()
    summary_sem = df.groupby('health')[feature_name].sem()  # sem() = std / sqrt(n)

    # Ensure all 4 health groups are shown in order
    health_order = ['Saline', 'Ghrelin', 'Inhibitory', 'Excitatory']
    summary_mean = summary_mean.reindex(health_order)
    summary_sem = summary_sem.reindex(health_order)

    # Set colors for bars
    colors = {
        'Saline': '#4CAF50',       # green
        'Ghrelin': '#2196F3',      # blue
        'Inhibitory': '#FFC107',   # amber
        'Excitatory': '#F44336'    # red
    }
    bar_colors = [colors.get(h, 'gray') for h in health_order]

    # Plot
    plt.figure(figsize=(8, 6))
    bars = plt.bar(summary_mean.index, summary_mean.values, 
                   yerr=summary_sem.values, 
                   capsize=5, 
                   color=bar_colors, 
                   edgecolor='black')

    plt.ylabel(ylabel if ylabel else f"Mean {feature_name.capitalize()}")
    plt.title(f"{feature_name.capitalize()} by Health for {task_name}")
    plt.xticks(rotation=45)

    if not summary_mean.isnull().all():
        plt.ylim(0, max((summary_mean + summary_sem).dropna()) * 1.2)  # account for error bars

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()
