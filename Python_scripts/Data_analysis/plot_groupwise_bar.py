import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from scipy.stats import ranksums

def plot_groupwise_bar(df, y='total_distance', title=None, ylabel=None, figsize=(6, 4)):
    """
    Plots a barplot of groupwise mean ± SEM with individual data points and performs RS test.

    Args:
        df (pd.DataFrame): Must have columns ['group', y]
        y (str): Column name to plot (e.g., 'total_distance')
        title (str): Plot title
        ylabel (str): Y-axis label
        figsize (tuple): Figure size
    """
    if y not in df.columns or 'group' not in df.columns:
        raise ValueError("DataFrame must have columns: 'group' and the feature column.")

    plt.figure(figsize=figsize)
    sns.barplot(data=df, x='group', y=y, errorbar='se', capsize=0.15, errwidth=1.2)
    sns.stripplot(data=df, x='group', y=y, color='black', size=4, jitter=True)

    # Add statistical test
    groups = df['group'].unique()
    if len(groups) == 2:
        vals1 = df[df['group'] == groups[0]][y]
        vals2 = df[df['group'] == groups[1]][y]
        stat, pval = ranksums(vals1, vals2)
        plt.text(0.5, df[y].max() * 1.05, f'p = {pval:.4f}', ha='center')

    plt.ylabel(ylabel if ylabel else y.replace('_', ' ').capitalize())
    plt.xlabel('')
    plt.title(title if title else f'{y.replace("_", " ").capitalize()} by Group')
    plt.tight_layout()
    plt.show()
