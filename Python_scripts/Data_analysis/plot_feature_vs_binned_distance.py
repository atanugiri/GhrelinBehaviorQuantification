import matplotlib.pyplot as plt
import numpy as np

def plot_feature_vs_binned_distance(df, feature_col='entropy',
                                    ylabel=None, title=None,
                                    figsize=(8, 5), save_path=None):
    """
    Compute group-wise mean ± SEM across distance bins and plot them.

    Args:
        df (pd.DataFrame): Must contain ['group', 'bin_start', 'bin_end', feature_col].
        feature_col (str): Feature name to analyze and plot.
        ylabel (str): Y-axis label.
        title (str): Plot title.
        figsize (tuple): Figure size.
        save_path (str): Optional path to save the figure.

    Returns:
        stats_df (pd.DataFrame): Bin-level group stats (mean, sem, count).
        fig (matplotlib.figure.Figure): Figure object.
        ax (matplotlib.axes.Axes): Axes object.
    """
    grouped = df.groupby(['group', 'bin_start', 'bin_end'])[feature_col]
    stats_df = grouped.agg(
        mean='mean',
        sem=lambda x: x.std(ddof=1) / x.notna().sum()**0.5,
        n='count'
    ).reset_index()

    stats_df = stats_df.rename(columns={
        'mean': f'{feature_col}_mean',
        'sem': f'{feature_col}_sem',
        'n': f'{feature_col}_n'
    })

    fig, ax = plt.subplots(figsize=figsize)

    for group in stats_df['group'].unique():
        df_group = stats_df[stats_df['group'] == group]
        x = df_group['bin_end']
        y = df_group[f'{feature_col}_mean']
        yerr = df_group[f'{feature_col}_sem']

        ax.errorbar(x, y, yerr=yerr, label=group, marker='o', capsize=3)

    ax.set_xlabel("Distance from Center")
    ax.set_ylabel(ylabel if ylabel else feature_col.replace('_', ' ').capitalize())
    ax.set_title(title if title else f"{feature_col.replace('_', ' ').capitalize()} vs Distance from Center")
    # ax.grid(True)
    ax.legend()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)
        print(f"[INFO] Saved plot to: {save_path}")

    return stats_df, fig, ax
