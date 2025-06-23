def plot_binned_total_distance(df, title=None):
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.figure(figsize=(8, 5))
    sns.pointplot(data=df, x='bin_index', y='mean_total_distance', hue='group',
                  errorbar=None, markers='o', capsize=0.1, errwidth=1.2)

    # Add error bars manually
    for _, row in df.iterrows():
        plt.errorbar(x=row['bin_index'], y=row['mean_total_distance'],
                     yerr=row['sem_total_distance'], fmt='none', color='black', capsize=3, alpha=0.5)

    plt.xlabel("Time Bin Index")
    plt.ylabel("Mean Total Distance (± SEM)")
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    plt.legend(title='Group')
    plt.show()
