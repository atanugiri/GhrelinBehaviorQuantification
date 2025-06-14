import numpy as np
import matplotlib.pyplot as plt

def barplot(n1=30, n2=30, mu1=0, mu2=1, std1=1.0, std2=1.0):
    """
    Simulate two arrays of normally distributed values, then plot their means with standard error bars.
    
    Parameters:
    - n1, n2: Number of samples
    - mu1, mu2: Means of the distributions
    - std1, std2: Standard deviations of the distributions (optional)
    
    Returns:
    - fig, ax: Matplotlib figure and axes handle
    """
    # Simulate data
    data1 = np.random.normal(loc=mu1, scale=std1, size=n1)
    data2 = np.random.normal(loc=mu2, scale=std2, size=n2)

    # Compute mean and standard error
    means = [np.mean(data1), np.mean(data2)]
    sems = [np.std(data1, ddof=1) / np.sqrt(n1),
            np.std(data2, ddof=1) / np.sqrt(n2)]

    # Plot
    fig, ax = plt.subplots()
    ax.bar([0, 1], means, yerr=sems, capsize=5, color=['skyblue', 'salmon'])    
    return fig, ax
