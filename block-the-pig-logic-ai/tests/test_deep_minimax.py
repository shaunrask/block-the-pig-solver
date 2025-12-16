"""
Test deep minimax algorithm - aiming for near 100% win rate
"""
from collections import deque
import random
import time

COL_MIN, COL_MAX = 0, 4
ROW_MIN, ROW_MAX = 0, 10

import sys
import os

# Add parent directory to path to import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app import find_optimal_block, bfs_escape_path, is_escape

def find_optimal_block_wrapper(pq, pr, wall_set):
    """Wrapper to adapt app.py API to test expectations."""
    pig = {'q': pq, 'r': pr}
    walls = [{'q': q, 'r': r} for q, r in wall_set]
    
    move_dict, thoughts = find_optimal_block(pig, walls)
    
    if move_dict:
        return (move_dict['q'], move_dict['r']), 0 
    return None, 0

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
        move, score = find_optimal_block_wrapper(pq, pr, wall_set)
        if move:
            wall_set.add(move)
        dist, _ = bfs_escape_path(pq, pr, wall_set)
        if dist == float('inf'):
            return 'WIN', 0
    
    # Main game loop
    for turn in range(max_turns):
        move, score = find_optimal_block_wrapper(pq, pr, wall_set)
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
