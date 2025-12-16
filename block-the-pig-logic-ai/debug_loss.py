"""
Debug specific losing games to understand why we lose
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
        return 0, None
    queue = deque([(start_q, start_r, None)])
    visited = {(start_q, start_r)}
    while queue:
        q, r, first = queue.popleft()
        for nq, nr in get_neighbors(q, r):
            if is_valid(nq, nr) and (nq, nr) not in visited and (nq, nr) not in blocked_cells:
                new_first = first if first else (nq, nr)
                if is_escape(nq, nr):
                    return len(visited), new_first
                visited.add((nq, nr))
                queue.append((nq, nr, new_first))
    return float('inf'), None

def get_valid_moves(pig_q, pig_r, blocked):
    moves = []
    for nq, nr in get_neighbors(pig_q, pig_r):
        if is_valid(nq, nr) and (nq, nr) not in blocked:
            moves.append((nq, nr))
    return moves

def minimax(pig_q, pig_r, blocked, depth, alpha, beta, is_player_turn, max_depth):
    dist, pig_next = bfs_escape_path(pig_q, pig_r, blocked)
    
    if dist == float('inf'):
        return 1000 - depth
    if dist == 0:
        return -1000 + depth
    if depth >= max_depth:
        return dist
    
    if is_player_turn:
        max_eval = -float('inf')
        moves = get_valid_moves(pig_q, pig_r, blocked)
        if pig_next:
            moves.sort(key=lambda m: 0 if m == pig_next else 1)
        for move in moves:
            new_blocked = blocked | {move}
            eval_score = minimax(pig_q, pig_r, new_blocked, depth + 1, alpha, beta, False, max_depth)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval if moves else -1000 + depth
    else:
        _, pig_best = bfs_escape_path(pig_q, pig_r, blocked)
        if pig_best is None:
            return 1000 - depth
        if is_escape(pig_best[0], pig_best[1]):
            return -1000 + depth
        return minimax(pig_best[0], pig_best[1], blocked, depth + 1, alpha, beta, True, max_depth)

def find_optimal_block(pq, pr, wall_set, max_depth=12):
    dist, _ = bfs_escape_path(pq, pr, wall_set)
    if dist == float('inf') or dist == 0:
        return None, -999
    
    moves = get_valid_moves(pq, pr, wall_set)
    if not moves:
        return None, -999
    
    best_move = moves[0]
    best_score = -float('inf')
    
    for depth_limit in range(2, max_depth + 1, 2):
        for move in moves:
            score = minimax(pq, pr, wall_set | {move}, 1, -float('inf'), float('inf'), False, depth_limit)
            if score > best_score:
                best_score = score
                best_move = move
            if score >= 900:
                return move, score
    
    return best_move, best_score

def visualize(pq, pr, wall_set):
    print("Grid:")
    for r in range(ROW_MIN, ROW_MAX + 1):
        indent = "  " if r % 2 == 1 else ""
        row = indent
        for q in range(COL_MIN, COL_MAX + 1):
            if (q, r) == (pq, pr):
                row += " P "
            elif (q, r) in wall_set:
                row += " # "
            elif is_escape(q, r):
                row += " . "
            else:
                row += " o "
        print(f"r={r:2d}: {row}")

def debug_game(seed, num_walls=5):
    print(f"\n{'='*60}")
    print(f"DEBUG: seed={seed}, num_walls={num_walls}")
    print(f"{'='*60}")
    
    random.seed(seed)
    pq, pr = 2, 5
    wall_set = set()
    
    # Place random initial walls
    for _ in range(num_walls):
        for attempt in range(50):
            wq = random.randint(0, 4)
            wr = random.randint(0, 10)
            if (wq, wr) != (pq, pr) and (wq, wr) not in wall_set:
                wall_set.add((wq, wr))
                break
    
    print(f"Initial walls: {sorted(wall_set)}")
    dist, _ = bfs_escape_path(pq, pr, wall_set)
    print(f"Initial pig distance: {dist}")
    
    # Opening phase
    print("\n--- OPENING PHASE (3 moves, pig doesn't move) ---")
    for i in range(3):
        move, score = find_optimal_block(pq, pr, wall_set, max_depth=16)
        if move:
            wall_set.add(move)
            dist, _ = bfs_escape_path(pq, pr, wall_set)
            print(f"Opening {i+1}: Block {move}, score={score}, new_dist={dist}")
            if dist == float('inf'):
                print("WIN during opening!")
                return
    
    visualize(pq, pr, wall_set)
    
    # Main game
    print("\n--- MAIN GAME ---")
    for turn in range(20):
        dist, pig_next = bfs_escape_path(pq, pr, wall_set)
        print(f"\nTurn {turn+1}: Pig at ({pq},{pr}), dist={dist}, next_move={pig_next}")
        
        move, score = find_optimal_block(pq, pr, wall_set, max_depth=16)
        if move is None:
            if dist == float('inf'):
                print("WIN!")
            else:
                print("No moves - LOSE")
            return
        
        wall_set.add(move)
        print(f"  AI blocks {move} (score={score})")
        
        dist, pig_next = bfs_escape_path(pq, pr, wall_set)
        if dist == float('inf'):
            print("  Pig TRAPPED - WIN!")
            return
        
        if pig_next:
            pq, pr = pig_next
            print(f"  Pig moves to {pig_next}")
        
        if is_escape(pq, pr):
            print("  Pig ESCAPED - LOSE!")
            visualize(pq, pr, wall_set)
            return

# Debug first loss with 5 walls
debug_game(42, num_walls=5)
