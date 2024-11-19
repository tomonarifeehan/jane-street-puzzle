import itertools
from collections import deque
from multiprocessing import Pool, cpu_count
import sys
import time

# Define the grid with labels
grid_labels = [
    ['A', 'B', 'B', 'C', 'C', 'C'],  # y=5 (a6 to f6)
    ['A', 'B', 'B', 'C', 'C', 'C'],  # y=4
    ['A', 'A', 'B', 'B', 'C', 'C'],  # y=3
    ['A', 'A', 'B', 'B', 'C', 'C'],  # y=2
    ['A', 'A', 'A', 'B', 'B', 'C'],  # y=1
    ['A', 'A', 'A', 'B', 'B', 'C']   # y=0 (a1 to f1)
]

# Define knight moves
knight_moves = [(-2, -1), (-1, -2), (1, -2), (2, -1),
               (2, 1), (1, 2), (-1, 2), (-2, 1)]

# Precompute all possible knight moves for each cell
def precompute_knight_moves():
    moves = {}
    for y in range(6):
        for x in range(6):
            current_moves = []
            for dx, dy in knight_moves:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 6 and 0 <= ny < 6:
                    current_moves.append((nx, ny))
            moves[(x, y)] = current_moves
    return moves

knight_moves_dict = precompute_knight_moves()

# Function to convert coordinates to cell name
def coord_to_cell(x, y):
    return chr(ord('a') + x) + str(y + 1)

# Function to map (x, y) to label
def get_label(x, y):
    return grid_labels[5 - y][x]  # y=0 is bottom row

# Function to assign values to the grid based on A, B, C
def assign_values(A, B, C):
    values = [[0 for _ in range(6)] for _ in range(6)]
    for y in range(6):
        for x in range(6):
            label = get_label(x, y)
            if label == 'A':
                values[y][x] = A
            elif label == 'B':
                values[y][x] = B
            elif label == 'C':
                values[y][x] = C
    # Debug: Print the assigned values grid
    # Uncomment the following lines to see the grid assignments
    # print(f"Assigned Values for A={A}, B={B}, C={C}:")
    # for row in reversed(values):
    #     print(row)
    return values

# Function to calculate the score of a given path
def calculate_score(path, values):
    if not path:
        return 0
    score = values[path[0][1]][path[0][0]]  # Start with the value of the starting cell
    # Debug: Print initial score
    # print(f"Starting at {coord_to_cell(path[0][0], path[0][1])} with initial score {score}")
    for i in range(1, len(path)):
        current = path[i - 1]
        next_move = path[i]
        label_current = get_label(current[0], current[1])
        label_next = get_label(next_move[0], next_move[1])
        value_next = values[next_move[1]][next_move[0]]
        if label_next != label_current:
            score *= value_next
            # Debug: Print multiplication step
            # print(f"Move from {coord_to_cell(current[0], current[1])} ({label_current}={values[current[1]][current[0]]}) to {coord_to_cell(next_move[0], next_move[1])} ({label_next}={value_next}) | Multiply: {score}")
        else:
            score += value_next
            # Debug: Print addition step
            # print(f"Move from {coord_to_cell(current[0], current[1])} ({label_current}={values[current[1]][current[0]]}) to {coord_to_cell(next_move[0], next_move[1])} ({label_next}={value_next}) | Add: {score}")
        if score > 2024:
            # Debug: Score exceeded
            # print(f"Score exceeded 2024 at move {coord_to_cell(next_move[0], next_move[1])}: {score}")
            break  # Early termination if score exceeds target
    return score

# Function to find a path using BFS that exactly reaches the target score
def find_path_bfs(start, end, values, target_score):
    queue = deque()
    initial_score = values[start[1]][start[0]]
    queue.append((
        [start],  # path
        initial_score  # current score
    ))
    
    while queue:
        path, score = queue.popleft()
        current = path[-1]
        if current == end:
            if score == target_score:
                # Debug: Found a valid path
                # print(f"Valid path found: {[coord_to_cell(x, y) for (x, y) in path]}")
                return path
            continue
        for move in knight_moves_dict[current]:
            if move in path:
                continue  # Cannot revisit within the same trip
            label_current = get_label(current[0], current[1])
            label_next = get_label(move[0], move[1])
            value_next = values[move[1]][move[0]]
            if label_next != label_current:
                new_score = score * value_next
            else:
                new_score = score + value_next
            if new_score > target_score:
                continue  # Prune paths that exceed the target
            new_path = path + [move]
            # To prevent exponential growth, limit the path length
            if len(new_path) > 36:
                continue
            queue.append((
                new_path,
                new_score
            ))
    return None  # No path found

# Function to format the path
def format_path(path):
    return ",".join([coord_to_cell(x, y) for (x, y) in path])

# Function to process a single (A, B, C) assignment
def process_assignment(assignment):
    A, B, C = assignment
    values = assign_values(A, B, C)
    # Define start and end points for both trips
    trip1_start = (0, 0)  # a1
    trip1_end = (5, 5)    # f6
    trip2_start = (0, 5)  # a6
    trip2_end = (5, 0)    # f1

    # Find path for Trip 1
    path1 = find_path_bfs(trip1_start, trip1_end, values, 2024)
    if not path1:
        return (A, B, C, False, None)  # No valid path for Trip 1

    # Verify Trip 1 score
    score1 = calculate_score(path1, values)
    if score1 != 2024:
        return (A, B, C, False, None)  # Trip 1 does not meet the target score

    # Find path for Trip 2
    path2 = find_path_bfs(trip2_start, trip2_end, values, 2024)
    if not path2:
        return (A, B, C, False, None)  # No valid path for Trip 2

    # Verify Trip 2 score
    score2 = calculate_score(path2, values)
    if score2 != 2024:
        return (A, B, C, False, None)  # Trip 2 does not meet the target score

    # If both paths are valid, return the solution
    return (A, B, C, True, (path1, path2))

# Function to generate all valid (A, B, C) assignments sorted by A + B + C
def generate_assignments():
    for total in range(6, 50):  # Minimal sum of distinct positive integers A=1, B=2, C=3 is 6
        for A in range(1, total - 1):
            for B in range(1, total - A):
                C = total - A - B
                if C < 1 or C == A or C == B:
                    continue
                # Ensure distinctness
                if len({A, B, C}) != 3:
                    continue
                yield (A, B, C)

# Worker function defined at the top level for multiprocessing
def worker(assignment):
    return process_assignment(assignment)

# Main function with progress tracking and detailed attempt logging
def main():
    print("Starting the search for a valid solution...")
    assignments = list(generate_assignments())
    total = len(assignments)
    print(f"Total assignments to process: {total}")
    processed = 0
    last_print_time = time.time()
    print_interval = 5  # seconds

    pool_size = max(cpu_count() - 1, 1)  # Leave one core free
    with Pool(pool_size) as pool:
        # Using imap_unordered to get results as they are completed
        for result in pool.imap_unordered(worker, assignments, chunksize=100):
            processed += 1
            A, B, C, success, solution = result
            # Print every attempt
            print(f"Attempting A={A}, B={B}, C={C}, Success: {success}")
            if success:
                path1, path2 = solution
                trip1_formatted = format_path(path1)
                trip2_formatted = format_path(path2)
                output = f"{A},{B},{C},{trip1_formatted},{trip2_formatted}"
                print("\nFinal Solution:")
                print(output)
                pool.terminate()  # Stop further processing
                return
            # Periodic progress updates
            current_time = time.time()
            if current_time - last_print_time >= print_interval:
                percent = (processed / total) * 100
                print(f"Processed {processed}/{total} assignments ({percent:.2f}%)")
                last_print_time = current_time
    print("No solution found with A + B + C < 50.")

if __name__ == "__main__":
    main()