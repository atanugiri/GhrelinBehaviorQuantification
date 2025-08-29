# feature_summary_vector.py
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from typing import List, Optional, Tuple

def plot_feature_grid(
    n_tasks: int = 7,
    n_features: int = 5,
    task_labels: Optional[List[str]] = None,
    feature_labels: Optional[List[str]] = None,
    facecolor: str = "lightgrey",
    show: bool = True,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Draw a blank grid with tasks as rows and features as columns.
    Each cell is a Rectangle patch (editable individually in Illustrator).
    """
    if task_labels is None:
        task_labels = [f"Task{i+1}" for i in range(n_tasks)]
    if feature_labels is None:
        feature_labels = [f"Feature{j+1}" for j in range(n_features)]

    fig, ax = plt.subplots(figsize=(8, 6))

    # Draw rectangles manually
    for i in range(n_tasks):
        for j in range(n_features):
            rect = Rectangle((j - 0.5, i - 0.5), 1, 1,
                             facecolor=facecolor, edgecolor="black", lw=0.5)
            ax.add_patch(rect)

    # Set limits
    ax.set_xlim(-0.5, n_features - 0.5)
    ax.set_ylim(n_tasks - 0.5, -0.5)  # invert y so rows are top-to-bottom

    # Labels
    ax.set_xticks(range(n_features))
    ax.set_yticks(range(n_tasks))
    ax.set_xticklabels(feature_labels, rotation=45, ha="right")
    ax.set_yticklabels(task_labels)

    plt.tight_layout()
    if show:
        plt.show()
    return fig, ax


if __name__ == "__main__":
    fig, ax = plot_feature_grid()
    fig.savefig("feature_grid_vector.pdf", dpi=300, bbox_inches="tight")
