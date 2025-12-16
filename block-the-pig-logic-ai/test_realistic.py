"""
Realistic game test - matches actual game conditions.
Game starts with 5-15 random walls and player gets 3 opening moves.
"""
from collections import deque
import random

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

def find_optimal_block(pq, pr, wall_set):
    """Algorithm matching app.py with tie-breaking"""
    current_distance, current_path = bfs_escape_path(pq, pr, wall_set)
    
    if current_distance == float('inf') or current_distance == 0:
        return None, -999
    
    neighbors = [(nq, nr) for nq, nr in get_neighbors(pq, pr) 
                 if is_valid(nq, nr) and (nq, nr) not in wall_set]
    
    # Priority 1: Immediate trap
    for cell in neighbors:
        test_walls = wall_set | {cell}
        dist, _ = bfs_escape_path(pq, pr, test_walls)
        if dist == float('inf'):
            return cell, 100
    
    # Priority 2: Block escape path
    if current_path:
        block_target = current_path[0]
        test_walls = wall_set | {block_target}
        new_dist, _ = bfs_escape_path(pq, pr, test_walls)
        
        if new_dist == float('inf'):
            return block_target, 100
        if new_dist > current_distance:
            return block_target, new_dist
        
        for path_cell in current_path[1:]:
            test_walls2 = wall_set | {path_cell}
            dist2, _ = bfs_escape_path(pq, pr, test_walls2)
            if dist2 > current_distance:
                return path_cell, dist2
    
    # Priority 3: Minimax with tie-breaking
    candidates = set(neighbors)
    for nq, nr in neighbors:
        for nnq, nnr in get_neighbors(nq, nr):
            if is_valid(nnq, nnr) and (nnq, nnr) not in wall_set and (nnq, nnr) != (pq, pr):
                candidates.add((nnq, nnr))
    
    best_results = []
    
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
        
        # Tie-breaking priority
        priority = 0
        if cell in neighbors:
            priority = 2
        elif current_path and cell in current_path:
            priority = 1
        
        best_results.append((score, priority, cell))
    
    best_results.sort(key=lambda x: (-x[0], -x[1]))
    
    if best_results:
        return best_results[0][2], best_results[0][0]
    if neighbors:
        return neighbors[0], -50
    return None, -999

def simulate_game_realistic(num_initial_walls=8, opening_moves=3, max_turns=50):
    """
    Simulate a realistic game:
    1. Start with random walls (like the actual game)
    2. Player gets opening phase moves (pig doesn't move)
    3. Then alternating moves
    """
    pq, pr = 2, 5  # Pig starts at center
    wall_set = set()
    
    # Place random initial walls
    for _ in range(num_initial_walls):
        for attempt in range(50):
            wq = random.randint(0, 4)
            wr = random.randint(0, 10)
            if (wq, wr) != (pq, pr) and (wq, wr) not in wall_set:
                wall_set.add((wq, wr))
                break
    
    # Opening phase - place walls without pig moving
    for _ in range(opening_moves):
        move, _ = find_optimal_block(pq, pr, wall_set)
        if move:
            wall_set.add(move)
        dist, _ = bfs_escape_path(pq, pr, wall_set)
        if dist == float('inf'):
            return 'WIN', 0
    
    # Main game loop
    for turn in range(max_turns):
        # AI places wall
        move, _ = find_optimal_block(pq, pr, wall_set)
        if move is None:
            dist, _ = bfs_escape_path(pq, pr, wall_set)
            return 'WIN' if dist == float('inf') else 'LOSE', turn
        
        wall_set.add(move)
        
        # Check if pig trapped
        dist, path = bfs_escape_path(pq, pr, wall_set)
        if dist == float('inf'):
            return 'WIN', turn + 1
        
        # Pig moves
        if path:
            pq, pr = path[0]
        
        # Check if pig escaped
        if is_escape(pq, pr):
            return 'LOSE', turn + 1
    
    return 'TIMEOUT', max_turns

def run_realistic_tests():
    print("="*60)
    print("REALISTIC GAME SIMULATION")
    print("(8 initial walls + 3 opening moves, matching actual game)")
    print("="*60)
    
    random.seed(42)
    wins = 0
    losses = 0
    
    for i in range(100):
        result, turns = simulate_game_realistic(num_initial_walls=8, opening_moves=3)
        if result == 'WIN':
            wins += 1
        else:
            losses += 1
    
    print(f"\n100 games with 8 initial walls + 3 opening moves:")
    print(f"  Wins: {wins}")
    print(f"  Losses: {losses}")
    print(f"  Win rate: {100*wins/100:.0f}%")
    
    # Also test with different wall counts
    print("\n" + "="*60)
    print("VARYING INITIAL CONDITIONS")
    print("="*60)
    
    for num_walls in [5, 10, 15]:
        for opening in [0, 3, 5]:
            random.seed(123)  # Consistent seed for comparison
            wins = 0
            for _ in range(50):
                result, _ = simulate_game_realistic(num_initial_walls=num_walls, opening_moves=opening)
                if result == 'WIN':
                    wins += 1
            print(f"  {num_walls} initial walls, {opening} opening moves: {wins}/50 wins ({100*wins/50:.0f}%)")

if __name__ == "__main__":
    run_realistic_tests()
