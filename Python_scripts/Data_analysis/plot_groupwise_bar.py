import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from scipy.stats import ranksums

def plot_groupwise_bar(df, y='total_distance', title=None, ylabel=None,
                       figsize=(6, 4), plot_type='bar', order=None, show_stats=True):
    """
    Plot groupwise comparison with optional bar or box plot and RS test.

    Args:
        df (pd.DataFrame): Must have columns ['group', y]
        y (str): Column to plot (e.g., 'total_distance')
        title (str): Plot title
        ylabel (str): Y-axis label
        figsize (tuple): Figure size
        plot_type (str): 'bar' or 'box'
        order (list): Optional list of group order (e.g., ['Saline', 'Ghrelin'])
        show_stats (bool): If True, adds RS test and asterisk(s)

    Returns:
        fig, ax: matplotlib Figure and Axes objects
    """
    if y not in df.columns or 'group' not in df.columns:
        raise ValueError("DataFrame must contain columns: 'group' and the feature column.")

    if order is None:
        order = df['group'].drop_duplicates().tolist()

    fig, ax = plt.subplots(figsize=figsize)

    palette = sns.color_palette("Set2", n_colors=len(order))

    if plot_type == 'bar':
        sns.barplot(data=df, x='group', y=y, order=order,
                    errorbar='se', capsize=0.15, errwidth=1.2,
                    palette=palette, ax=ax)
    elif plot_type == 'box':
        sns.boxplot(data=df, x='group', y=y, order=order,
                    palette=palette, ax=ax, showcaps=True,
                    boxprops=dict(alpha=0.7), medianprops=dict(color='black'))
    else:
        raise ValueError("plot_type must be either 'bar' or 'box'.")

    sns.stripplot(data=df, x='group', y=y, order=order,
                  color='black', size=4, jitter=True, ax=ax)

    if show_stats and len(order) == 2:
        vals1 = df[df['group'] == order[0]][y]
        vals2 = df[df['group'] == order[1]][y]
        stat, pval = ranksums(vals1, vals2)

        # Choose annotation text
        if pval < 0.0001:
            p_str = '****'
        elif pval < 0.001:
            p_str = '***'
        elif pval < 0.01:
            p_str = '**'
        elif pval < 0.05:
            p_str = '*'
        else:
            p_str = 'n.s.'

        # Draw a line + asterisk above bars
        y_max = df[y].max()
        y_line = y_max * 1.1
        y_text = y_max * 1.15
        ax.plot([0, 1], [y_line, y_line], color='black', linewidth=1.2)
        ax.text(0.5, y_text, p_str, ha='center', fontsize=12)

    ax.set_ylabel(ylabel if ylabel else y.replace('_', ' ').capitalize())
    ax.set_xlabel('')
    ax.set_title(title if title else f'{y.replace("_", " ").capitalize()} by Group')

    fig.tight_layout()
    return fig, ax
