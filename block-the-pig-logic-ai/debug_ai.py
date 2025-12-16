"""
Interactive test to debug specific game scenarios.
Pass pig position and walls to see what the AI suggests and why.
"""
from collections import deque

# Grid constants
COL_MIN, COL_MAX = 0, 4
ROW_MIN, ROW_MAX = 0, 10

def get_neighbors(q, r):
    if r % 2 == 0:
        return [(q+1, r), (q, r-1), (q-1, r-1), (q-1, r), (q-1, r+1), (q, r+1)]
    else:
        return [(q+1, r), (q+1, r-1), (q, r-1), (q-1, r), (q, r+1), (q+1, r+1)]

def is_valid(q, r):
    return COL_MIN <= q <= COL_MAX and ROW_MIN <= r <= ROW_MAX

def is_escape(q, r):
    if not is_valid(q, r): return False
    return q == COL_MIN or q == COL_MAX or r == ROW_MIN or r == ROW_MAX

def bfs_escape_distance(pq, pr, blocked_cells):
    if is_escape(pq, pr):
        return 0
    queue = deque([(pq, pr, 0)])
    visited = {(pq, pr)}
    while queue:
        q, r, dist = queue.popleft()
        for nq, nr in get_neighbors(q, r):
            if is_valid(nq, nr) and (nq, nr) not in visited and (nq, nr) not in blocked_cells:
                if is_escape(nq, nr):
                    return dist + 1
                visited.add((nq, nr))
                queue.append((nq, nr, dist + 1))
    return float('inf')

def visualize_grid(pq, pr, wall_set, suggested=None, candidates=None):
    """Print a visualization of the hex grid."""
    print("\n  Grid (q: 0-4, r: 0-10):")
    for r in range(ROW_MIN, ROW_MAX + 1):
        indent = "  " if r % 2 == 1 else ""
        row = indent
        for q in range(COL_MIN, COL_MAX + 1):
            if (q, r) == (pq, pr):
                row += " P "
            elif suggested and (q, r) == suggested:
                row += " X "
            elif (q, r) in wall_set:
                row += " # "
            elif candidates and (q, r) in candidates:
                row += " * "
            elif is_escape(q, r):
                row += " . "
            else:
                row += " o "
        print(f"  r={r:2d}: {row}")
    print("  Legend: P=pig, #=wall, X=suggested, *=candidate, .=escape, o=interior")

def analyze_position(pq, pr, walls_list):
    """Analyze a game position and show detailed AI reasoning."""
    wall_set = set((w['q'], w['r']) for w in walls_list)
    
    current_distance = bfs_escape_distance(pq, pr, wall_set)
    print(f"\n{'='*60}")
    print(f"ANALYSIS: Pig at ({pq}, {pr})")
    print(f"{'='*60}")
    print(f"Current escape distance: {current_distance}")
    
    if current_distance == float('inf'):
        print("Pig is TRAPPED - no moves needed!")
        return
    
    if current_distance == 0:
        print("Pig is AT an escape - game over!")
        return
    
    # Get candidate cells
    candidates = set()
    for nq, nr in get_neighbors(pq, pr):
        if is_valid(nq, nr) and (nq, nr) not in wall_set:
            candidates.add((nq, nr))
    
    for nq, nr in list(candidates):
        for nnq, nnr in get_neighbors(nq, nr):
            if is_valid(nnq, nnr) and (nnq, nnr) not in wall_set and (nnq, nnr) != (pq, pr):
                candidates.add((nnq, nnr))
    
    print(f"Evaluating {len(candidates)} candidate cells...")
    
    # Evaluate each candidate
    results = []
    for cell in sorted(candidates):
        test_walls = wall_set | {cell}
        new_distance = bfs_escape_distance(pq, pr, test_walls)
        improvement = new_distance - current_distance
        results.append((cell, new_distance, improvement))
    
    # Sort by new_distance (higher is better)
    results.sort(key=lambda x: (-x[1], x[0]))
    
    print("\nTop 10 blocking options (sorted by new distance):")
    for i, (cell, dist, imp) in enumerate(results[:10]):
        dist_str = "TRAP" if dist == float('inf') else str(dist)
        imp_str = f"+{imp}" if imp > 0 else str(imp)
        marker = " <-- BEST" if i == 0 else ""
        print(f"  {cell}: new_dist={dist_str}, improvement={imp_str}{marker}")
    
    # Show the suggested move
    best_cell = None
    best_new_distance = current_distance
    for cell, dist, _ in results:
        if dist > best_new_distance:
            best_new_distance = dist
            best_cell = cell
            break
    
    if best_cell:
        visualize_grid(pq, pr, wall_set, suggested=best_cell, candidates=candidates)
        print(f"\nSUGGESTED MOVE: Block {best_cell} (increases distance from {current_distance} to {best_new_distance})")
    else:
        # No improvement possible
        print("\nNo blocking move can increase escape distance!")
        print("Algorithm will fall back to blocking a neighbor.")
        visualize_grid(pq, pr, wall_set, candidates=candidates)

def main():
    # Test the ACTUAL starting scenario with some random walls
    # This simulates what happens when the game starts
    
    print("="*60)
    print("TEST: Game start scenario (pig at center, random walls)")
    print("="*60)
    
    # Pig at center
    pq, pr = 2, 5
    
    # A few random walls (simulating game start)
    walls = [
        {'q': 1, 'r': 3},
        {'q': 3, 'r': 7},
        {'q': 0, 'r': 2},
    ]
    
    analyze_position(pq, pr, walls)
    
    # Additional test scenarios
    print("\n\n")
    print("="*60)
    print("TEST: Pig moved, trying to escape left")
    print("="*60)
    
    pq, pr = 1, 5
    walls = [
        {'q': 1, 'r': 3},
        {'q': 3, 'r': 7},
        {'q': 0, 'r': 2},
        {'q': 2, 'r': 5},  # Previous AI block
    ]
    analyze_position(pq, pr, walls)
    
    print("\n\n")
    print("="*60)
    print("TEST: Near-trap scenario")
    print("="*60)
    
    pq, pr = 2, 5
    walls = [
        {'q': 1, 'r': 4}, {'q': 2, 'r': 4}, {'q': 3, 'r': 4},
        {'q': 1, 'r': 6}, {'q': 2, 'r': 6},
        {'q': 1, 'r': 5},
    ]
    analyze_position(pq, pr, walls)

if __name__ == "__main__":
    main()
