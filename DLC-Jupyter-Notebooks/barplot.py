import numpy as np
import matplotlib.pyplot as plt

def barplot(n1=30, n2=30, mu1=0, mu2=1):
    """
    Simulate two arrays of normally distributed values, then plot their means with standard error bars.
    
    Parameters:
    - n1, n2: Lengths of the two arrays (int)
    - mu1, mu2: Means of the two distributions (float)
    
    Returns:
    - fig, ax: Matplotlib figure and axes handle for further customization
    """
    # Simulate data
    data1 = np.random.normal(loc=mu1, scale=1.0, size=n1)
    data2 = np.random.normal(loc=mu2, scale=1.0, size=n2)

    means = [np.mean(data1), np.mean(data2)]
    sems = [np.std(data1, ddof=1) / np.sqrt(n1),
            np.std(data2, ddof=1) / np.sqrt(n2)]

    # Plot
    fig, ax = plt.subplots()
    ax.bar([0, 1], means, yerr=sems, capsize=5, color=['skyblue', 'salmon'])    
    return fig, ax
