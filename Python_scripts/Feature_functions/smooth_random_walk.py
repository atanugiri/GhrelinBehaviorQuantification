import numpy as np
import matplotlib.pyplot as plt

def smooth_walk_sparse_band_only(trial_id, conn,
                                 inertia=0.9, step_noise=0.3,
                                 center=(0, 1), r_min=0.42, r_max=0.57,
                                 avoid_strength=0.003, skip_prob=0.2,
                                 margin=0.05, seed=0, plot=False):
    """
    Smooth random walk with sparsity in radial band (r_min < r < r_max),
    using frame_rate and trial_length from database trial.
    Allows soft boundary margin and optional plotting.

    Parameters:
        trial_id: Trial ID in dlc_table_temp (must have frame_rate & trial_length).
        conn: psycopg2 or SQLAlchemy connection object.
        Other params as before.
        margin: Extra margin allowed beyond unit square (default: 0.05).
        plot: If True, plot the trajectory.

    Returns:
        traj: (n_steps, 2) numpy array of x,y trajectory.
    """
    import pandas as pd

    # Query DB
    df = pd.read_sql_query("""
        SELECT frame_rate, trial_length FROM dlc_table_temp WHERE id = %s
        """, conn, params=(trial_id,))
    if df.empty:
        raise ValueError(f"No trial found with id {trial_id}")
    frame_rate = df.loc[0, 'frame_rate']
    trial_length = df.loc[0, 'trial_length']
    n_steps = int(frame_rate * trial_length)
    dt = 1 / frame_rate

    # Init
    np.random.seed(seed)
    traj = np.zeros((n_steps, 2))
    velocity = np.zeros((n_steps, 2))
    traj[0] = np.random.rand(2)

    for t in range(1, n_steps):
        pos = traj[t - 1]
        v_prev = velocity[t - 1]

        # Smooth noise movement
        noise = step_noise * np.random.randn(2)
        velocity[t] = inertia * v_prev + (1 - inertia) * noise

        # Radial band detection
        r_vec = pos - center
        r = np.linalg.norm(r_vec)

        if r_min < r < r_max:
            if np.random.rand() < skip_prob:
                traj[t] = pos
                continue
            velocity[t] += avoid_strength * (r_vec / r)

        # Update position
        next_pos = pos + dt * velocity[t]

        # Soft boundary reflection with margin
        for i in [0, 1]:
            if next_pos[i] < -margin:
                next_pos[i] = -margin
                velocity[t][i] *= -1
            elif next_pos[i] > 1 + margin:
                next_pos[i] = 1 + margin
                velocity[t][i] *= -1

        traj[t] = next_pos

    # Optional plot
    if plot:
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.plot(traj[:, 0], traj[:, 1], linewidth=0.5)
        ax.plot(*center, 'ko', label='Light source')
        circle1 = plt.Circle(center, r_min, color='green', fill=False, linestyle='--')
        circle2 = plt.Circle(center, r_max, color='red', fill=False, linestyle='--')
        ax.add_artist(circle1)
        ax.add_artist(circle2)
        ax.set_xlim(-margin, 1 + margin)
        ax.set_ylim(1 + margin, -margin)  # DLC-style flip
        ax.set_xlabel("x")
        ax.set_ylabel("y (DLC-style: 0 at top, 1 at bottom)")
        ax.set_title(f"Smooth Trajectory with Sparse Band ({r_min}–{r_max})")
        ax.legend()
        ax.set_aspect('equal')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    return traj
