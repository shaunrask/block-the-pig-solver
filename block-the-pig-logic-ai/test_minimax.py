"""
Test the new minimax algorithm.
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

def bfs_escape_distance(start_q, start_r, blocked_cells):
    if is_escape(start_q, start_r):
        return 0
    queue = deque([(start_q, start_r, 0)])
    visited = {(start_q, start_r)}
    while queue:
        q, r, dist = queue.popleft()
        for nq, nr in get_neighbors(q, r):
            if is_valid(nq, nr) and (nq, nr) not in visited and (nq, nr) not in blocked_cells:
                if is_escape(nq, nr):
                    return dist + 1
                visited.add((nq, nr))
                queue.append((nq, nr, dist + 1))
    return float('inf')

def get_pig_best_move(pig_q, pig_r, blocked_cells):
    if is_escape(pig_q, pig_r):
        return (pig_q, pig_r)
    queue = deque([(pig_q, pig_r, [])])
    visited = {(pig_q, pig_r)}
    while queue:
        q, r, path = queue.popleft()
        if is_escape(q, r):
            if path:
                return path[0]
            return (q, r)
        for nq, nr in get_neighbors(q, r):
            if is_valid(nq, nr) and (nq, nr) not in visited and (nq, nr) not in blocked_cells:
                visited.add((nq, nr))
                queue.append((nq, nr, path + [(nq, nr)]))
    return None

def find_optimal_block_minimax(pq, pr, wall_set):
    """2-ply minimax algorithm."""
    current_distance = bfs_escape_distance(pq, pr, wall_set)
    
    if current_distance == float('inf') or current_distance == 0:
        return None, []
    
    candidates = set()
    for nq, nr in get_neighbors(pq, pr):
        if is_valid(nq, nr) and (nq, nr) not in wall_set:
            candidates.add((nq, nr))
    for nq, nr in list(candidates):
        for nnq, nnr in get_neighbors(nq, nr):
            if is_valid(nnq, nnr) and (nnq, nnr) not in wall_set and (nnq, nnr) != (pq, pr):
                candidates.add((nnq, nnr))
    
    best_cell = None
    best_score = -float('inf')
    results = []
    
    for cell in sorted(candidates):
        test_walls = wall_set | {cell}
        
        dist_after_wall = bfs_escape_distance(pq, pr, test_walls)
        if dist_after_wall == float('inf'):
            return cell, [("TRAP", cell)]
        
        pig_move = get_pig_best_move(pq, pr, test_walls)
        if pig_move is None:
            return cell, [("TRAP", cell)]
        
        new_pig_q, new_pig_r = pig_move
        
        if is_escape(new_pig_q, new_pig_r):
            score = -100
        else:
            score = bfs_escape_distance(new_pig_q, new_pig_r, test_walls)
            if score == float('inf'):
                score = 100
        
        results.append((cell, score, pig_move))
        
        if score > best_score:
            best_score = score
            best_cell = cell
    
    return best_cell, results

def visualize_grid(pq, pr, wall_set, suggested=None):
    print("\n  Grid:")
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
            elif is_escape(q, r):
                row += " . "
            else:
                row += " o "
        print(f"  r={r:2d}: {row}")

def test_scenario(name, pq, pr, walls_list):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    
    wall_set = set((w['q'], w['r']) for w in walls_list)
    current_dist = bfs_escape_distance(pq, pr, wall_set)
    print(f"Pig at ({pq}, {pr}), current escape distance: {current_dist}")
    
    best_cell, results = find_optimal_block_minimax(pq, pr, wall_set)
    
    if isinstance(results, list) and len(results) > 0 and results[0][0] == "TRAP":
        print(f"WINNING MOVE: {best_cell}")
        visualize_grid(pq, pr, wall_set, best_cell)
        return
    
    # Sort by score descending
    results_sorted = sorted(results, key=lambda x: -x[1])
    
    print(f"\nTop 5 moves (by score after pig responds):")
    for cell, score, pig_move in results_sorted[:5]:
        score_str = "ESCAPE!" if score == -100 else ("TRAP!" if score == 100 else str(score))
        marker = " <-- BEST" if cell == best_cell else ""
        print(f"  Block {cell} -> pig moves to {pig_move} -> escape_dist: {score_str}{marker}")
    
    visualize_grid(pq, pr, wall_set, best_cell)
    
    if best_cell:
        print(f"\nSUGGESTED: Block {best_cell}")

# Run tests
test_scenario("Pig in center, no walls", 2, 5, [])
test_scenario("Pig moved left", 1, 5, [])
test_scenario("Pig near corner", 1, 1, [])
test_scenario("Pig with some walls", 2, 5, [
    {'q': 1, 'r': 4}, {'q': 3, 'r': 6}
])
