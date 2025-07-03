import numpy as np
import matplotlib.pyplot as plt

def sparse_radial_band(center=(0, 1), n=3000, r_min=0.2, r_max=0.4, band_accept_prob=0.25):
    points = []
    while len(points) < n:
        x, y = np.random.rand(2)
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)

        if r_min < r < r_max:
            if np.random.rand() < band_accept_prob:
                points.append((x, y))
        else:
            points.append((x, y))
    return np.array(points)

# Generate points
pts = sparse_radial_band()

# Plot with y-axis flipped for DLC-style view
fig, ax = plt.subplots(figsize=(5, 5))
ax.scatter(pts[:, 0], pts[:, 1], s=2, alpha=0.5)  # No flip
ax.plot(0, 1, 'ko', label='Light source')  # Light source at (0,1)

# Radial band visualization
theta = np.linspace(0, np.pi/2, 300)
for r in [0.2, 0.4]:
    x = r * np.cos(theta)
    y = r * np.sin(theta) + 1  # offset center to (0,1)
    ax.plot(x, y, 'r--', label='Radial band' if r == 0.2 else None)

ax.set_aspect('equal')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.invert_yaxis()  # Flip y-axis: 0 at top, 1 at bottom
ax.set_xlabel("x")
ax.set_ylabel("y (DLC-style: 0 at top, 1 at bottom)")
ax.set_title("Sparse Occupancy in Radial Band Near Light Source")
ax.legend()
ax.grid(True)
plt.show()
