# feature_summary_dual_bold.py
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from typing import List, Optional, Tuple

def plot_dual_comparison_grid(
    n_tasks: int = 7,
    n_features: int = 5,
    task_labels: Optional[List[str]] = None,
    feature_labels: Optional[List[str]] = None,
    left_label: str = "Inh",
    right_label: str = "Exc",
    left_face: str = "#e6e6e6",
    right_face: str = "#f5f5f5",
    edgecolor: str = "black",
    lw: float = 0.5,
    bold_lw: float = 1.5,   # thickness for bold separators
    fontsize_cell: int = 7,
    show: bool = True,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Tasks × Features grid, each cell split into left (Inh) and right (Exc).
    Adds bold vertical separators after each feature for clear distinction.
    """
    if task_labels is None:
        task_labels = [f"Task{i+1}" for i in range(n_tasks)]
    if feature_labels is None:
        feature_labels = [f"Feature{j+1}" for j in range(n_features)]

    fig, ax = plt.subplots(figsize=(10, 6))

    for i in range(n_tasks):
        for j in range(n_features):
            x0, y0 = j - 0.5, i - 0.5

            # left half (Inh)
            ax.add_patch(Rectangle(
                (x0, y0), 0.5, 1.0,
                facecolor=left_face, edgecolor=edgecolor, lw=lw
            ))
            # right half (Exc)
            ax.add_patch(Rectangle(
                (x0 + 0.5, y0), 0.5, 1.0,
                facecolor=right_face, edgecolor=edgecolor, lw=lw
            ))

            # # placeholder labels
            # ax.text(j - 0.25, i, f"{left_label}\np=", ha="center", va="center", fontsize=fontsize_cell)
            # ax.text(j + 0.25, i, f"{right_label}\np=", ha="center", va="center", fontsize=fontsize_cell)

    # Set limits and orientation
    ax.set_xlim(-0.5, n_features - 0.5)
    ax.set_ylim(n_tasks - 0.5, -0.5)

    # Ticks
    ax.set_xticks(range(n_features))
    ax.set_yticks(range(n_tasks))
    ax.set_xticklabels(feature_labels, rotation=45, ha="right")
    ax.set_yticklabels(task_labels)

    # Bold separators between features
    for j in range(n_features + 1):
        ax.axvline(x=j - 0.5, color="black",
                   lw=bold_lw if j > 0 else lw)

    # Outer box
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)

    plt.tight_layout()
    if show:
        plt.show()
    return fig, ax

if __name__ == "__main__":
    fig, ax = plot_dual_comparison_grid(
        n_tasks=7,
        n_features=5,
        task_labels=["Combined", "NoFoodOnly", "FoodOnly", "ToyOnly", "LightOnly", "ToyLight", "FoodLight"],
        feature_labels=["Curvature", "Distance", "Velocity", "Acceleration", "Stops"],
    )
    fig.savefig("dual_grid_bold.pdf", dpi=300, bbox_inches="tight")
