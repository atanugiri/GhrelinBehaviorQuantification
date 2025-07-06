def plot_radial_density_per_trial(ids, conn, center=(0, 1), r_band=(0.43, 0.57), n_cols=4):
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np

    n_rows = int(np.ceil(len(ids) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 3 * n_rows), sharex=True, sharey=True)

    for ax, trial_id in zip(axes.flat, ids):
        df = pd.read_sql_query("SELECT head_x_norm, head_y_norm FROM dlc_table_temp WHERE id = %s", conn, params=(trial_id,))
        if df.empty:
            continue
        x = np.array(df['head_x_norm'][0])
        y = np.array(df['head_y_norm'][0])
        r = np.linalg.norm(np.stack((x, y), axis=1) - center, axis=1)

        ax.hist(r, bins=50, density=True, alpha=0.7, color='steelblue')
        ax.axvspan(*r_band, color='orange', alpha=0.3)
        ax.set_title(f"ID {trial_id}")
        ax.set_xlim(0, 1)

    plt.tight_layout()
    plt.suptitle("Radial Distance Density per Saline Trial", y=1.02)
    plt.show()
