import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def plot_column_distribution_by_id(conn, id, column_name, bins=50):
    """
    Plot histogram and boxplot for a specified column (e.g., 'corner1_x') of a given trial ID.

    Args:
        conn: psycopg2 or SQLAlchemy connection object
        id: trial ID to query
        column_name: string, name of the column (e.g., 'corner1_x')
        bins: number of bins for the histogram
    """
    query = f"SELECT {column_name} FROM dlc_table WHERE id = {id};"
    df = pd.read_sql_query(query, conn)

    if df.empty or df.iloc[0][column_name] is None:
        print(f"No data found for ID {id}, column '{column_name}'")
        return

    try:
        # Handle stringified lists
        val = df.iloc[0][column_name]
        if isinstance(val, (list, np.ndarray)):
            data = np.array(val)
        else:
            data = np.array(eval(val))

        if len(data) == 0:
            print(f"Column '{column_name}' is empty for ID {id}")
            return

        # Plot
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        axes[0].hist(data[~np.isnan(data)], bins=bins, color='skyblue', edgecolor='black')
        axes[0].set_title(f'Histogram of {column_name} (ID {id})')

        axes[1].boxplot(data[~np.isnan(data)], vert=False)
        axes[1].set_title(f'Boxplot of {column_name} (ID {id})')

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Failed to process column '{column_name}' for ID {id}: {e}")
