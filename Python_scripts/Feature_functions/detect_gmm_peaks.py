from sklearn.mixture import GaussianMixture
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

def detect_gmm_peaks(r_all, n_components=2, plot=True):
    r_all = r_all.reshape(-1, 1)
    gmm = GaussianMixture(n_components=n_components, random_state=0).fit(r_all)

    means = np.sort(gmm.means_.flatten())
    sparse_band_width = means[1] - means[0]

    if plot:
        sns.histplot(r_all.flatten(), bins=100, stat='density', kde=False, color='lightgray')
        x = np.linspace(0, 1, 500).reshape(-1, 1)
        y = np.exp(gmm.score_samples(x))
        plt.plot(x, y, label='GMM Fit')
        for m in means:
            plt.axvline(m, linestyle='--', label=f'Mean = {m:.2f}')
        plt.fill_betweenx(np.linspace(0, max(y), 500), means[0], means[1], color='orange', alpha=0.3, label='Sparse Band')
        plt.xlabel('Radial Distance')
        plt.title('GMM-Based Sparse Band Detection')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    return (means[0], means[1], sparse_band_width)
