#!/usr/bin/env python3
"""Plot individual trajectories for a fixed set of Saline and Ghrelin IDs."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scripts.config import load_dlc_table
from scripts.analysis.plot_single_trajectory import plot_single_trajectory

SALINE_IDS = [508, 513, 518, 524, 528]
GHRELIN_IDS = [507, 512, 514, 522, 534]

TRAJECTORY_PARAMS = dict(
    bodypart="Midback",
    normalize=False,
    interpolate=True,
    likelihood_threshold=0.5,
    max_points=500,
    color_by_time=False,
    style="line",
)

outdir = Path("results/trajectories")
outdir.mkdir(parents=True, exist_ok=True)

dlc_table = load_dlc_table()

for label, id_list in [("Saline", SALINE_IDS), ("Ghrelin", GHRELIN_IDS)]:
    fig, ax = plt.subplots(figsize=(6, 6))
    for trial_id in id_list:
        plot_single_trajectory(dlc_table, trial_id, label=f"ID {trial_id}", **TRAJECTORY_PARAMS, ax=ax)
    ax.set_title(label)
    plt.tight_layout()
    out_path = outdir / f"{label.lower()}_trajectories.pdf"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[✓] Saved {out_path}")
