def plot_binned_curvature_comparison(df_bins, feature='curvature_mean', title=None):
    """
    Plots group-wise mean and SEM of a binned curvature feature over time bins.

    Parameters:
        df_bins (pd.DataFrame): Output from compute_binned_curvature_stats.
        feature (str): One of 'curvature_mean' or 'curvature_z_mean_abs'
        title (str, optional): Custom title for the plot. Defaults to auto-generated title.
    """
    if feature not in df_bins.columns:
        raise ValueError(f"'{feature}' not found in DataFrame")

    plt.figure(figsize=(8, 5))
    sns.pointplot(data=df_bins, x='bin_index', y=feature, hue='group',
                  errorbar='se', markers='o', capsize=0.1, errwidth=1.2)

    plt.xlabel('Time Bin (index)')
    plt.ylabel(feature.replace('_', ' ').capitalize())
    
    plot_title = title if title else f'{feature.replace("_", " ").capitalize()} by Time Bin'
    plt.title(plot_title)

    plt.grid(True)
    plt.tight_layout()
    plt.legend(title='Group')
    plt.show()
