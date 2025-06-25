def plot_binned_feature_with_sem_from_raw(df, feature, title=None, ylabel=None):
    """
    Plots group-wise mean ± SEM of a binned feature from raw (trial-level) data.

    Args:
        df (pd.DataFrame): Must contain columns ['group', 'bin_index', <feature>]
        feature (str): Feature column to plot (e.g., 'distance_sum', 'velocity_mean')
        title (str): Plot title (optional)
        ylabel (str): Y-axis label (optional)
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd

    if feature not in df.columns or 'group' not in df.columns or 'bin_index' not in df.columns:
        raise ValueError("DataFrame must have columns: 'group', 'bin_index', and the feature column.")

    # Compute mean and SEM
    summary = df.groupby(['group', 'bin_index']).agg(
        mean_val=(feature, 'mean'),
        sem_val=(feature, 'sem')
    ).reset_index()

    # Plot mean values using seaborn pointplot
    plt.figure(figsize=(8, 5))
    sns.pointplot(
        data=summary, x='bin_index', y='mean_val', hue='group',
        errorbar=None, markers='o', capsize=0.1, errwidth=1.2
    )

    # Add manual error bars
    for _, row in summary.iterrows():
        plt.errorbar(
            x=row['bin_index'], y=row['mean_val'],
            yerr=row['sem_val'], fmt='none', color='black', capsize=3, alpha=0.5
        )

    # Labels and layout
    plt.xlabel("Time Bin Index")
    plt.ylabel(ylabel if ylabel else f"{feature.replace('_', ' ').capitalize()} (± SEM)")
    plt.title(title if title else f"{feature.replace('_', ' ').capitalize()} by Time Bin")
    plt.grid(True)
    plt.tight_layout()
    plt.legend(title='Group')
    plt.show()
