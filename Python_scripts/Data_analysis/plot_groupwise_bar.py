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

    # Use consistent color palette
    group_order = df['group'].unique()
    palette = sns.color_palette("Set2", n_colors=len(group_order))

    sns.barplot(data=df, x='group', y=y, order=group_order,
                errorbar='se', capsize=0.15, errwidth=1.2,
                palette=palette)

    sns.stripplot(data=df, x='group', y=y, order=group_order,
                  color='black', size=4, jitter=True)

    # Add statistical test if exactly two groups
    if len(group_order) == 2:
        vals1 = df[df['group'] == group_order[0]][y]
        vals2 = df[df['group'] == group_order[1]][y]
        stat, pval = ranksums(vals1, vals2)
        p_str = f'p = {pval:.4f}' if pval >= 0.0001 else 'p < 0.0001'

        # Set x and y for text placement (just above second bar)
        y_pos = df[y].max() * 1.05
        plt.text(0.75, y_pos, p_str, ha='left', fontsize=10)

    plt.ylabel(ylabel if ylabel else y.replace('_', ' ').capitalize())
    plt.xlabel('')
    plt.title(title if title else f'{y.replace("_", " ").capitalize()} by Group')
    plt.tight_layout()
    plt.show()
