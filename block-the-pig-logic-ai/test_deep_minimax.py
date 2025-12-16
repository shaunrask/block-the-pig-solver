"""
Test deep minimax algorithm - aiming for near 100% win rate
"""
from collections import deque
import random
import time

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
    queue = deque([(start_q, start_r, 0, None)])
    visited = {(start_q, start_r)}
    while queue:
        q, r, dist, first = queue.popleft()
        for nq, nr in get_neighbors(q, r):
            if is_valid(nq, nr) and (nq, nr) not in visited and (nq, nr) not in blocked_cells:
                new_first = first if first else (nq, nr)
                if is_escape(nq, nr):
                    return dist + 1, new_first
                visited.add((nq, nr))
                queue.append((nq, nr, dist + 1, new_first))
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

def find_optimal_block(pq, pr, wall_set, max_depth=16):
    dist, pig_next = bfs_escape_path(pq, pr, wall_set)
    if dist == float('inf') or dist == 0:
        return None, -999
    
    # Get candidate moves - neighbors + cells within 2-3 steps
    moves = set()
    for nq, nr in get_neighbors(pq, pr):
        if is_valid(nq, nr) and (nq, nr) not in wall_set:
            moves.add((nq, nr))
            for nnq, nnr in get_neighbors(nq, nr):
                if is_valid(nnq, nnr) and (nnq, nnr) not in wall_set and (nnq, nnr) != (pq, pr):
                    moves.add((nnq, nnr))
    
    moves = list(moves)
    if not moves:
        return None, -999
    
    # Sort by proximity to escape path
    if pig_next:
        moves.sort(key=lambda m: 0 if m == pig_next else 1)
    
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

def simulate_game(num_initial_walls=8, opening_moves=3, max_turns=50):
    pq, pr = 2, 5
    wall_set = set()
    
    # Place random initial walls
    for _ in range(num_initial_walls):
        for attempt in range(50):
            wq = random.randint(0, 4)
            wr = random.randint(0, 10)
            if (wq, wr) != (pq, pr) and (wq, wr) not in wall_set:
                wall_set.add((wq, wr))
                break
    
    # Opening phase
    for _ in range(opening_moves):
        move, score = find_optimal_block(pq, pr, wall_set)
        if move:
            wall_set.add(move)
        dist, _ = bfs_escape_path(pq, pr, wall_set)
        if dist == float('inf'):
            return 'WIN', 0
    
    # Main game loop
    for turn in range(max_turns):
        move, score = find_optimal_block(pq, pr, wall_set)
        if move is None:
            dist, _ = bfs_escape_path(pq, pr, wall_set)
            return 'WIN' if dist == float('inf') else 'LOSE', turn
        
        wall_set.add(move)
        
        dist, pig_next = bfs_escape_path(pq, pr, wall_set)
        if dist == float('inf'):
            return 'WIN', turn + 1
        
        if pig_next:
            pq, pr = pig_next
        
        if is_escape(pq, pr):
            return 'LOSE', turn + 1
    
    return 'TIMEOUT', max_turns

def run_tests():
    print("="*60)
    print("DEEP MINIMAX TEST (max_depth=12)")
    print("="*60)
    
    random.seed(42)
    
    for num_walls in [5, 8, 10, 15]:
        random.seed(42)
        wins = 0
        losses = 0
        start = time.time()
        
        for i in range(20):
            result, turns = simulate_game(num_initial_walls=num_walls, opening_moves=3)
            if result == 'WIN':
                wins += 1
            else:
                losses += 1
                print(f"  LOSS: {num_walls} walls, game {i+1}")
        
        elapsed = time.time() - start
        print(f"{num_walls} walls + 3 opening: {wins}/20 wins ({100*wins/20:.0f}%) in {elapsed:.1f}s")
    
    print("\n" + "="*60)
    print("STRESS TEST (50 games each)")
    print("="*60)
    
    for num_walls in [5, 10, 15]:
        random.seed(123)
        wins = 0
        for _ in range(50):
            result, _ = simulate_game(num_initial_walls=num_walls, opening_moves=3)
            if result == 'WIN':
                wins += 1
        print(f"{num_walls} walls + 3 opening: {wins}/50 wins ({100*wins/50:.0f}%)")

if __name__ == "__main__":
    run_tests()
