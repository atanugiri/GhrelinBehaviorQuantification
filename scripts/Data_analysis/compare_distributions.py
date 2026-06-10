import numpy as np
import matplotlib.pyplot as plt

def compare_distributions(*arrays, labels=None, bins=100, kind='pdf', return_data=False):
    """
    Compare multiple 1D distributions using PDF or CDF plots.

    Parameters
    ----------
    *arrays : array-like
        Variable number of 1D arrays to compare.
    labels : list of str, optional
        Labels corresponding to each array (default: generic labels).
    bins : int, optional
        Number of histogram bins (default: 100).
    kind : str, optional
        'pdf' or 'cdf' (default: 'pdf').
    return_data : bool, optional
        If True, return computed histogram data (default: False).

    Returns
    -------
    fig, ax : matplotlib Figure and Axes objects
    data (optional) : list of dicts containing 'x' and 'y' for each array if return_data=True
    """
    if len(arrays) < 2:
        raise ValueError("At least two arrays are required for comparison.")

    if labels is None:
        labels = [f'Distribution {i+1}' for i in range(len(arrays))]
    if len(labels) != len(arrays):
        raise ValueError("Number of labels must match number of arrays.")

    hist_range = (min(arr.min() for arr in arrays), max(arr.max() for arr in arrays))
    fig, ax = plt.subplots(figsize=(8, 5))
    data = []

    if kind == 'pdf':
        for arr, label in zip(arrays, labels):
            ax.hist(arr, bins=bins, range=hist_range, density=True, alpha=0.5, label=label)
        ylabel = 'Density'
        title = 'Distribution Comparison (PDF)'

    elif kind == 'cdf':
        for arr, label in zip(arrays, labels):
            counts, bin_edges = np.histogram(arr, bins=bins, range=hist_range, density=True)
            dx = np.diff(bin_edges)[0]
            x = bin_edges[:-1] + dx / 2
            y = np.cumsum(counts) * dx
            ax.plot(x, y, label=label)
            data.append({'x': x, 'y': y})
        ylabel = 'Cumulative Probability'
        title = 'Distribution Comparison (CDF)'

    else:
        raise ValueError("`kind` must be 'pdf' or 'cdf'")

    ax.set_xlabel('Value')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()

    if return_data and kind == 'cdf':
        return fig, ax, data
    else:
        return fig, ax
