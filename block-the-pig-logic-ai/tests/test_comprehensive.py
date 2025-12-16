"""
Comprehensive test suite for the minimax AI algorithm.
Tests many edge cases and game scenarios.
"""
from collections import deque
import random

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

def bfs_escape_path(start_q, start_r, blocked_cells):
    if is_escape(start_q, start_r):
        return 0, []
    queue = deque([(start_q, start_r, [])])
    visited = {(start_q, start_r)}
    while queue:
        q, r, path = queue.popleft()
        for nq, nr in get_neighbors(q, r):
            if is_valid(nq, nr) and (nq, nr) not in visited and (nq, nr) not in blocked_cells:
                new_path = path + [(nq, nr)]
                if is_escape(nq, nr):
                    return len(new_path), new_path
                visited.add((nq, nr))
                queue.append((nq, nr, new_path))
    return float('inf'), []

def find_optimal_block_minimax(pq, pr, wall_set):
    """Path-based algorithm matching app.py"""
    current_distance, current_path = bfs_escape_path(pq, pr, wall_set)
    
    if current_distance == float('inf') or current_distance == 0:
        return None, -999
    
    neighbors = [(nq, nr) for nq, nr in get_neighbors(pq, pr) 
                 if is_valid(nq, nr) and (nq, nr) not in wall_set]
    
    # Priority 1: Check for immediate trap
    for cell in neighbors:
        test_walls = wall_set | {cell}
        dist, _ = bfs_escape_path(pq, pr, test_walls)
        if dist == float('inf'):
            return cell, 100
    
    # Priority 2: Block pig's escape path
    if current_path:
        block_target = current_path[0]
        test_walls = wall_set | {block_target}
        new_dist, _ = bfs_escape_path(pq, pr, test_walls)
        
        if new_dist == float('inf'):
            return block_target, 100
        if new_dist > current_distance:
            return block_target, new_dist
        
        # Try further along path
        for path_cell in current_path[1:]:
            test_walls2 = wall_set | {path_cell}
            dist2, _ = bfs_escape_path(pq, pr, test_walls2)
            if dist2 > current_distance:
                return path_cell, dist2
    
    # Priority 3: Minimax
    candidates = set(neighbors)
    for nq, nr in neighbors:
        for nnq, nnr in get_neighbors(nq, nr):
            if is_valid(nnq, nnr) and (nnq, nnr) not in wall_set and (nnq, nnr) != (pq, pr):
                candidates.add((nnq, nnr))
    
    best_cell = None
    best_score = -float('inf')
    
    for cell in candidates:
        test_walls = wall_set | {cell}
        new_dist, new_path = bfs_escape_path(pq, pr, test_walls)
        
        if new_dist == float('inf'):
            return cell, 100
        
        if new_path:
            pig_next = new_path[0]
            final_dist, _ = bfs_escape_path(pig_next[0], pig_next[1], test_walls)
            if is_escape(pig_next[0], pig_next[1]):
                score = -100
            elif final_dist == float('inf'):
                score = 100
            else:
                score = final_dist
        else:
            score = new_dist
        
        if score > best_score:
            best_score = score
            best_cell = cell
    
    if best_cell:
        return best_cell, best_score
    
    if neighbors:
        return neighbors[0], -50
    
    return None, -999

def simulate_game(pq, pr, initial_walls, max_turns=50, verbose=False):
    """
    Simulate a full game using the AI.
    Returns: (result, turns, history)
    result: 'WIN' (trapped), 'LOSE' (escaped), 'TIMEOUT'
    """
    wall_set = set((w['q'], w['r']) for w in initial_walls)
    history = []
    
    for turn in range(max_turns):
        # AI's turn - place a wall
        ai_move, score = find_optimal_block_minimax(pq, pr, wall_set)
        
        if ai_move is None:
            # Check if pig trapped or escaped
            if bfs_escape_distance(pq, pr, wall_set) == float('inf'):
                return 'WIN', turn, history
            else:
                return 'LOSE', turn, history
        
        wall_set.add(ai_move)
        history.append(('WALL', ai_move, score))
        
        # Check if pig is trapped
        if bfs_escape_distance(pq, pr, wall_set) == float('inf'):
            return 'WIN', turn + 1, history
        
        # Pig's turn - move toward escape
        pig_move = get_pig_best_move(pq, pr, wall_set)
        
        if pig_move is None:
            return 'WIN', turn + 1, history
        
        pq, pr = pig_move
        history.append(('PIG', pig_move))
        
        # Check if pig escaped
        if is_escape(pq, pr):
            return 'LOSE', turn + 1, history
    
    return 'TIMEOUT', max_turns, history

def visualize_state(pq, pr, wall_set, last_wall=None):
    """Print grid state."""
    for r in range(ROW_MIN, ROW_MAX + 1):
        indent = "  " if r % 2 == 1 else ""
        row = indent
        for q in range(COL_MIN, COL_MAX + 1):
            if (q, r) == (pq, pr):
                row += " P "
            elif last_wall and (q, r) == last_wall:
                row += " X "
            elif (q, r) in wall_set:
                row += " # "
            elif is_escape(q, r):
                row += " . "
            else:
                row += " o "
        print(f"  r={r:2d}: {row}")

def test_scenario(name, pq, pr, walls_list, expected_result=None):
    """Test a single scenario."""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    print(f"Pig starts at ({pq}, {pr}), {len(walls_list)} initial walls")
    
    wall_set = set((w['q'], w['r']) for w in walls_list)
    current_dist = bfs_escape_distance(pq, pr, wall_set)
    print(f"Initial escape distance: {current_dist}")
    
    result, turns, history = simulate_game(pq, pr, walls_list, max_turns=30, verbose=True)
    
    print(f"Result: {result} in {turns} turns")
    
    if result == 'LOSE':
        print("\n  GAME TRACE (showing where AI failed):")
        temp_walls = set((w['q'], w['r']) for w in walls_list)
        temp_pq, temp_pr = pq, pr
        for i, action in enumerate(history[-6:]):  # Last 6 moves
            if action[0] == 'WALL':
                _, cell, score = action
                temp_walls.add(cell)
                print(f"  Turn {i//2+1}: AI blocks {cell} (score={score})")
            else:
                _, pos = action
                temp_pq, temp_pr = pos
                print(f"  Turn {i//2+1}: Pig moves to {pos}")
        print("\n  Final position:")
        visualize_state(temp_pq, temp_pr, temp_walls)
    
    if expected_result and result != expected_result:
        print(f"  *** UNEXPECTED: Expected {expected_result}, got {result}")
        return False
    
    return result == 'WIN' if expected_result == 'WIN' else True


def run_all_tests():
    print("="*70)
    print("COMPREHENSIVE AI TEST SUITE")
    print("="*70)
    
    results = []
    
    # Test 1: Pig in center, no walls - should be winnable
    results.append(test_scenario(
        "Pig in center (2,5), no walls",
        2, 5, []
    ))
    
    # Test 2: Pig at various positions
    results.append(test_scenario(
        "Pig at (1,5) - near left edge",
        1, 5, []
    ))
    
    results.append(test_scenario(
        "Pig at (3,5) - near right edge",
        3, 5, []
    ))
    
    results.append(test_scenario(
        "Pig at (2,2) - near top",
        2, 2, []
    ))
    
    results.append(test_scenario(
        "Pig at (2,8) - near bottom",
        2, 8, []
    ))
    
    # Test 3: Pig in corner areas (hardest)
    results.append(test_scenario(
        "Pig at (1,1) - corner area (HARD)",
        1, 1, []
    ))
    
    results.append(test_scenario(
        "Pig at (3,1) - corner area (HARD)",
        3, 1, []
    ))
    
    results.append(test_scenario(
        "Pig at (1,9) - corner area (HARD)",
        1, 9, []
    ))
    
    # Test 4: With some helpful walls
    results.append(test_scenario(
        "Pig at (2,5) with blocking walls",
        2, 5, [
            {'q': 1, 'r': 4}, {'q': 3, 'r': 4},
            {'q': 1, 'r': 6}, {'q': 3, 'r': 6}
        ]
    ))
    
    # Test 5: Pig almost trapped
    results.append(test_scenario(
        "Pig at (2,5) - almost trapped",
        2, 5, [
            {'q': 1, 'r': 4}, {'q': 2, 'r': 4}, {'q': 3, 'r': 4},
            {'q': 1, 'r': 5},
            {'q': 1, 'r': 6}, {'q': 2, 'r': 6}
        ],
        expected_result='WIN'
    ))
    
    # Test 6: Pig in corridor
    results.append(test_scenario(
        "Pig in horizontal corridor",
        2, 5, [
            {'q': 0, 'r': 4}, {'q': 1, 'r': 4}, {'q': 2, 'r': 4}, {'q': 3, 'r': 4}, {'q': 4, 'r': 4},
            {'q': 0, 'r': 6}, {'q': 1, 'r': 6}, {'q': 2, 'r': 6}, {'q': 3, 'r': 6}, {'q': 4, 'r': 6}
        ]
    ))
    
    # Test 7: Random scenarios
    print("\n" + "="*70)
    print("RANDOM SCENARIO TESTS (20 games)")
    print("="*70)
    
    random.seed(42)
    wins = 0
    losses = 0
    
    for i in range(20):
        # Random pig position (interior only)
        pq = random.randint(1, 3)
        pr = random.randint(2, 8)
        
        # Random walls (0-8)
        num_walls = random.randint(0, 8)
        walls = []
        wall_set = set()
        for _ in range(num_walls):
            wq = random.randint(0, 4)
            wr = random.randint(0, 10)
            if (wq, wr) != (pq, pr) and (wq, wr) not in wall_set:
                walls.append({'q': wq, 'r': wr})
                wall_set.add((wq, wr))
        
        result, turns, _ = simulate_game(pq, pr, walls, max_turns=30)
        
        if result == 'WIN':
            wins += 1
        else:
            losses += 1
            print(f"  Game {i+1}: LOSE - Pig at ({pq},{pr}), {len(walls)} walls, {turns} turns")
    
    print(f"\nRandom games: {wins} wins, {losses} losses ({100*wins/20:.0f}% win rate)")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    test_wins = sum(1 for r in results if r)
    print(f"Scenario tests: {test_wins}/{len(results)} passed")
    print(f"Random games: {wins}/20 won")
    
    if losses > 0:
        print("\n*** Some games were lost - AI needs improvement ***")
    
    return losses == 0

if __name__ == "__main__":
    run_all_tests()
