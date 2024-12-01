import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from typing import List, Tuple

def check_intersection(A: np.ndarray, B: np.ndarray) -> Tuple[bool, str, np.ndarray]:
    """
    Check intersection and return success status, nearest side, and intersection point
    """
    # Find nearest side to B
    distances = [
        (abs(B[1] - 0), 'bottom'),  # Bottom
        (abs(B[1] - 1), 'top'),     # Top
        (abs(B[0] - 0), 'left'),    # Left
        (abs(B[0] - 1), 'right')    # Right
    ]
    nearest_side = min(distances, key=lambda x: x[0])[1]
    
    # Calculate midpoint and direction vector of perpendicular bisector
    midpoint = (A + B) / 2
    direction = B - A
    perp_vector = np.array([-direction[1], direction[0]])  # Rotate 90 degrees
    
    # Normalize perpendicular vector
    length = np.linalg.norm(perp_vector)
    if length == 0:
        return False, nearest_side, None
    perp_vector = perp_vector / length
    
    # Calculate intersection based on nearest side
    intersection = None
    success = False
    
    if nearest_side == 'bottom':
        if perp_vector[1] != 0:
            t = (0 - midpoint[1]) / perp_vector[1]
            x = midpoint[0] + t * perp_vector[0]
            intersection = np.array([x, 0])
            success = 0 <= x <= 1
            
    elif nearest_side == 'top':
        if perp_vector[1] != 0:
            t = (1 - midpoint[1]) / perp_vector[1]
            x = midpoint[0] + t * perp_vector[0]
            intersection = np.array([x, 1])
            success = 0 <= x <= 1
            
    elif nearest_side == 'left':
        if perp_vector[0] != 0:
            t = (0 - midpoint[0]) / perp_vector[0]
            y = midpoint[1] + t * perp_vector[1]
            intersection = np.array([0, y])
            success = 0 <= y <= 1
            
    else:  # right
        if perp_vector[0] != 0:
            t = (1 - midpoint[0]) / perp_vector[0]
            y = midpoint[1] + t * perp_vector[1]
            intersection = np.array([1, y])
            success = 0 <= y <= 1
            
    return success, nearest_side, intersection

def plot_example(ax, A: np.ndarray, B: np.ndarray, success: bool):
    """Plot a single example"""
    # Plot unit square
    ax.add_patch(Rectangle((0, 0), 1, 1, fill=False, color='black'))
    
    # Get intersection info
    is_success, nearest_side, intersection = check_intersection(A, B)
    
    # Plot nearest side in blue
    if nearest_side == 'bottom':
        ax.plot([0, 1], [0, 0], 'b-', linewidth=2)
    elif nearest_side == 'top':
        ax.plot([0, 1], [1, 1], 'b-', linewidth=2)
    elif nearest_side == 'left':
        ax.plot([0, 0], [0, 1], 'b-', linewidth=2)
    else:  # right
        ax.plot([1, 1], [0, 1], 'b-', linewidth=2)
    
    # Plot perpendicular bisector
    midpoint = (A + B) / 2
    direction = B - A
    perp_vector = np.array([-direction[1], direction[0]])
    if np.linalg.norm(perp_vector) > 0:
        perp_vector = perp_vector / np.linalg.norm(perp_vector)
        t_values = np.linspace(-0.5, 1.5, 100)
        line_points = np.array([(midpoint[0] + t * perp_vector[0],
                               midpoint[1] + t * perp_vector[1]) for t in t_values])
        valid_points = line_points[
            (line_points[:, 0] >= -0.1) & (line_points[:, 0] <= 1.1) &
            (line_points[:, 1] >= -0.1) & (line_points[:, 1] <= 1.1)
        ]
        if len(valid_points) > 0:
            ax.plot(valid_points[:, 0], valid_points[:, 1], 'g--', alpha=0.5)
    
    # Plot points
    ax.plot(A[0], A[1], 'ro', label='Point A')
    ax.plot(B[0], B[1], 'bo', label='Point B')
    
    # Plot intersection point if it exists
    if intersection is not None:
        ax.plot(intersection[0], intersection[1], 'ko', label='Intersection')
    
    # Set title and limits
    ax.set_title(f"{'Success' if success else 'Failure'}")
    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.1, 1.1)
    ax.set_aspect('equal')

# Run simulation and collect examples
np.random.seed(42)
num_trials = 1_000_000
successes = []
failures = []

while len(successes) < 4 or len(failures) < 4:
    A = np.random.random(2)
    B = np.random.random(2)
    success, _, _ = check_intersection(A, B)
    
    if success and len(successes) < 4:
        successes.append((A, B))
    elif not success and len(failures) < 4:
        failures.append((A, B))

# Create visualization grid
fig, axs = plt.subplots(2, 4, figsize=(16, 8))
fig.suptitle('Examples of Successes and Failures', fontsize=16)

# Plot successes on top row
for i, (A, B) in enumerate(successes):
    plot_example(axs[0, i], A, B, True)
axs[0, 0].set_ylabel('Successes')

# Plot failures on bottom row
for i, (A, B) in enumerate(failures):
    plot_example(axs[1, i], A, B, False)
axs[1, 0].set_ylabel('Failures')

# Add legend to first plot only
axs[0, 0].legend()

plt.tight_layout()
plt.show()

# Run full simulation for probability
all_points = np.random.random((2, num_trials, 2))
A_points = all_points[0]
B_points = all_points[1]

total_successes = sum(check_intersection(A_points[i], B_points[i])[0] 
                     for i in range(num_trials))

probability = total_successes / num_trials
print(f"\nFull Simulation Results:")
print(f"Number of trials: {num_trials:,}")
print(f"Number of successes: {total_successes:,}")
print(f"Probability: {probability:.6f}")