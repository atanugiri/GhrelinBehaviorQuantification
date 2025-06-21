def plot_feature_histogram_and_boxplot(conn, column_name, bins=50):
    """
    Plots a histogram and a box plot for a scalar feature column in the 'dlc_table'.

    Parameters:
        conn: psycopg2 connection object
        column_name (str): The name of the scalar column (e.g., 'mean_curv')
        bins (int): Number of histogram bins (default: 50)

    Returns:
        fig: Matplotlib Figure object
    """
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    # Query non-null values
    query = f"""
    SELECT {column_name}
    FROM dlc_table
    WHERE {column_name} IS NOT NULL;
    """
    df = pd.read_sql_query(query, conn)

    if df.empty:
        raise ValueError(f"No non-null data found for column '{column_name}'.")

    # Convert to float array
    values = np.array([float(v) for v in df[column_name]])

    # Plotting
    fig, axes = plt.subplots(nrows=2, figsize=(6, 6), gridspec_kw={'height_ratios': [3, 1]})
    
    # Histogram
    axes[0].hist(values, bins=bins, color='steelblue', edgecolor='black')
    axes[0].set_title(f'Histogram of {column_name}')
    axes[0].set_ylabel('Count')
    
    # Box plot
    axes[1].boxplot(values, vert=False, patch_artist=True,
                    boxprops=dict(facecolor='skyblue'))
    axes[1].set_xlabel(column_name)
    axes[1].set_yticks([])

    plt.tight_layout()
    plt.show()
    # return fig
