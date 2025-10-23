import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

def plot_misalignment_frame(
    head, neck, midback, lowerback, tailbase,
    line_colors=("tab:orange","tab:blue"),  # (Head→Neck, Head→Tailbase)
    dot_size=70,
    wedge_radius=20.0,
    invert_y=True,
    figsize=(4,4),
    linewidth=3.0,
):
    """
    Draws 5 bodypart dots, connects ONLY Head→Neck and Head→Tailbase,
    and shades the angle at Head between those two lines.

    Parameters
    ----------
    head, neck, midback, lowerback, tailbase : array-like (x,y) in *your* coordinate system
        e.g., np.array([x,y]) for each part (pixels or normalized coords).
    line_colors : tuple
        Colors for (Head→Neck, Head→Tailbase) lines.
    wedge_radius : float
        Radius of the shaded angle wedge (in your coordinate units, e.g., pixels).
    invert_y : bool
        True if your image coordinates have y pointing down (typical video coords).
    """
    head = np.asarray(head, float)
    neck = np.asarray(neck, float)
    mid  = np.asarray(midback, float)
    low  = np.asarray(lowerback, float)
    tail = np.asarray(tailbase, float)

    # vectors for angle
    v_hn = neck - head        # Head→Neck
    v_ht = tail - head        # Head→Tailbase

    def _angle(v):
        return np.degrees(np.arctan2(v[1], v[0]))

    # angles for wedge sweep
    a1 = _angle(v_ht)   # reference: Head→Tailbase
    a2 = _angle(v_hn)   # Head→Neck
    # choose the shorter sweep between a1 and a2
    d = (a2 - a1 + 180) % 360 - 180  # wrap to (-180,180]
    theta1, theta2 = a1, a1 + d

    fig, ax = plt.subplots(figsize=figsize)

    # scatter all five dots
    pts = np.vstack([tail, low, mid, neck, head])
    ax.scatter(pts[:,0], pts[:,1], s=dot_size)

    # draw ONLY the two lines you want
    ax.plot([head[0], neck[0]], [head[1], neck[1]], color=line_colors[0], lw=linewidth)
    ax.plot([head[0], tail[0]], [head[1], tail[1]], color=line_colors[1], lw=linewidth)

    # shade angle wedge at the head
    wedge = Wedge(center=(head[0], head[1]),
                  r=wedge_radius, theta1=theta1, theta2=theta2, alpha=0.25)
    ax.add_patch(wedge)

    # cosmetics
    ax.set_aspect('equal', adjustable='box')
    if invert_y:
        ax.invert_yaxis()
    ax.axis('off')
    plt.tight_layout()
    return fig, ax
