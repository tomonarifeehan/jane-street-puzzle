import sys
sys.setrecursionlimit(10_000)

MIN_EDGE = -0.5
MAX_EDGE = 10.5

def steps_before_leaving(ax, ay, vx, vy):
    """
    Determines how many whole steps can be taken from (ax, ay) in the direction (vx, vy) before going out of the valid grid.
    """
    print(f"[DEBUG] steps_before_leaving called with position=({ax},{ay}), direction=({vx},{vy})")
    if vx > 0:
        distance = int(MAX_EDGE - ax)
    elif vx < 0:
        distance = int(ax - MIN_EDGE)
    elif vy > 0:
        distance = int(MAX_EDGE - ay)
    elif vy < 0:
        distance = int(ay - MIN_EDGE)
    else:
        distance = 0
    print(f"[DEBUG] steps_before_leaving returning {distance}")
    return distance

def is_diagonal_placement_possible(arrangement, px, py):
    """
    Confirms whether a diagonal can be placed at (px, py) such that:
      1) That spot is free.
      2) None of the four adjacent spots already hold a diagonal.
    """
    print(f"[DEBUG] Checking diagonal feasibility at ({px},{py})")
    if (px, py) in arrangement:
        print(f"[DEBUG] Spot ({px},{py}) is already occupied.")
        return False
    for vx, vy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        adj_x, adj_y = px + vx, py + vy
        if (adj_x, adj_y) in arrangement:
            print(f"[DEBUG] Adjacent spot ({adj_x},{adj_y}) is occupied. Cannot place diagonal.")
            return False
    return True

def bounce(direction, diag_type):
    """
    Modifies the incoming direction vector (dx, dy) when hitting either a '/' or '\' diagonal, returning the new direction.
    """
    print(f"[DEBUG] bounce called with direction={direction}, diag_type={diag_type}")
    dx, dy = direction
    if diag_type == '/':
        if (dx, dy) == (-1, 0):
            return (0, -1)
        elif (dx, dy) == (0, -1):
            return (-1, 0)
        elif (dx, dy) == (1, 0):
            return (0, 1)
        elif (dx, dy) == (0, 1):
            return (1, 0)
    elif diag_type == '\\':
        if (dx, dy) == (-1, 0):
            return (0, 1)
        elif (dx, dy) == (0, 1):
            return (-1, 0)
        elif (dx, dy) == (1, 0):
            return (0, -1)
        elif (dx, dy) == (0, -1):
            return (1, 0)
    
    # If nothing changes, just return original direction.
    return (dx, dy)

def evaluate_laser_path_product(arrangement, origin, vector):
    """
    Launches a hypothetical laser from a given origin with a specific
    vector on the provided arrangement. Continues until the laser
    goes off the board, multiplying each traveled segment length.
    """
    print(f"[DEBUG] evaluate_laser_path_product: Starting from origin={origin} with vector={vector}")
    x, y = origin
    dx, dy = vector
    product_accumulator = 1

    while True:
        boundary_dist = steps_before_leaving(x, y, dx, dy)
        found_diagonal = False
        actual_travel = boundary_dist

        for step in range(1, boundary_dist):
            test_x = x + step * dx
            test_y = y + step * dy
            if (test_x, test_y) in arrangement:
                found_diagonal = True
                actual_travel = step
                break

        product_accumulator *= actual_travel
        x += actual_travel * dx
        y += actual_travel * dy

        if found_diagonal:
            diag_kind, _ = arrangement[(x, y)]
            dx, dy = bounce((dx, dy), diag_kind)
        else:
            break

    print(f"[DEBUG] evaluate_laser_path_product: Final product is {product_accumulator}")
    return product_accumulator

def explore_laser_configurations(arrangement, lx, ly, vx, vy, current_mult, target_mult):
    """
    Probes every valid placement of diagonals for a laser traveling from
    (lx, ly) in direction (vx, vy). 'current_mult' is the ongoing product
    of traveled distances, and 'target_mult' is the desired final product.
    Yields all possible valid arrangements meeting the target.
    """
    print(f"[DEBUG] explore_laser_configurations called with laser=({lx},{ly}), direction=({vx},{vy}), "
          f"current_mult={current_mult}, target_mult={target_mult}")
    
    to_wall = steps_before_leaving(lx, ly, vx, vy)
    
    if current_mult * to_wall == target_mult:
        print("[DEBUG] Found matching configuration with no additional diagonals needed.")
        yield arrangement
    
    for step in range(1, to_wall):
        new_lx = lx + step * vx
        new_ly = ly + step * vy
        new_mult = current_mult * step

        # If the partial product no longer fits the target, skip
        if target_mult % new_mult != 0:
            continue

        if (new_lx, new_ly) in arrangement:
            d_type, _ = arrangement[(new_lx, new_ly)]
            updated_dir = bounce((vx, vy), d_type)
            
            yield from explore_laser_configurations(
                arrangement,
                new_lx,
                new_ly,
                updated_dir[0],
                updated_dir[1],
                new_mult,
                target_mult
            )
        
        else:
            if not is_diagonal_placement_possible(arrangement, new_lx, new_ly):
                continue

            for diag_option in ['/', '\\']:
                arrangement_copy = arrangement.copy()
                arrangement_copy[(new_lx, new_ly)] = (diag_option, None)
                updated_dir = bounce((vx, vy), diag_option)
                
                yield from explore_laser_configurations(
                    arrangement_copy,
                    new_lx,
                    new_ly,
                    updated_dir[0],
                    updated_dir[1],
                    new_mult,
                    target_mult
                )

def complete_all_challenges(challenges, arrangement, idx=0):
    """
    Recursively attempts to solve each challenge in 'challenges'.
    After placing diagonals for the current challenge, re-check all previously
    solved ones to ensure no prior constraints were disrupted.
    """
    print(f"[DEBUG] complete_all_challenges at index={idx}")
    if idx == len(challenges):
        return arrangement

    challenge = challenges[idx]
    origin = challenge["origin"]
    vector = challenge["vector"]
    target = challenge["target"]

    for candidate_arrangement in explore_laser_configurations(
        arrangement,
        origin[0],
        origin[1],
        vector[0],
        vector[1],
        1,
        target
    ):
        # Verify older challenges remain valid.
        all_ok = True
        for past_idx in range(idx):
            past_challenge = challenges[past_idx]
            result_mult = evaluate_laser_path_product(
                candidate_arrangement,
                past_challenge["origin"],
                past_challenge["vector"]
            )
            if result_mult != past_challenge["target"]:
                all_ok = False
                break

        if not all_ok:
            continue

        outcome = complete_all_challenges(challenges, candidate_arrangement, idx + 1)
        if outcome is not None:
            return outcome

    return None

def display_arrangement(arrangement):
    """
    Shows the 10x10 grid with placed diagonals. Dots ('.') represent empty cells, while '/' or '\' indicate the diagonal orientation in that cell.
    """
    board_matrix = [['.' for _ in range(10)] for _ in range(10)]
    
    for (ax, ay), (diag_char, _) in arrangement.items():
        col = int(ax - 0.5)
        row = int(ay - 0.5)
        board_matrix[row][col] = diag_char
    
    for row_idx in range(9, -1, -1):
        print(" ".join(board_matrix[row_idx]))
    
    print()

def main():
    # Each challenge has:
    #   "origin": starting coordinate
    #   "vector": direction
    #   "target": expected product
    challenges = [
        { "origin": (10.5, 8.5),  "vector": (-1, 0),  "target": 4 },
        { "origin": (10.5, 7.5),  "vector": (-1, 0),  "target": 27 },
        { "origin": (10.5, 3.5),  "vector": (-1, 0),  "target": 16 },
        { "origin": (7.5, -0.5),  "vector": (0, 1),   "target": 405 },
        { "origin": (5.5, -0.5),  "vector": (0, 1),   "target": 5 },
        { "origin": (4.5, -0.5),  "vector": (0, 1),   "target": 64 },
        { "origin": (3.5, -0.5),  "vector": (0, 1),   "target": 12 },
        { "origin": (0.5, -0.5),  "vector": (0, 1),   "target": 2025 },
        { "origin": (-0.5, 1.5),  "vector": (1, 0),   "target": 225 },
        { "origin": (-0.5, 2.5),  "vector": (1, 0),   "target": 12 },
        { "origin": (-0.5, 6.5),  "vector": (1, 0),   "target": 27 },
        { "origin": (2.5, 10.5),  "vector": (0, -1),  "target": 112 },
        { "origin": (4.5, 10.5),  "vector": (0, -1),  "target": 48 },
        { "origin": (5.5, 10.5),  "vector": (0, -1),  "target": 3087 },
        { "origin": (6.5, 10.5),  "vector": (0, -1),  "target": 9 },
    ]

    # Sort by target for incremental constraint application.
    challenges.sort(key=lambda c: c["target"])

    initial_arrangement = {}
    final_layout = complete_all_challenges(challenges, initial_arrangement, 0)

    if final_layout is None:
        print("\n\n[DEBUG] No final solution could be found :(")
    
    else:
        print("\n\n[DEBUG] Cheeky solution found hehe :)")
        display_arrangement(final_layout)

if __name__ == "__main__":
    main()