"""
Additional stress tests for the Block the Pig AI algorithm.
Tests many random and edge-case scenarios.
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

def find_optimal_block(pq, pr, wall_set):
    """Copy of algorithm from app.py"""
    current_distance = bfs_escape_distance(pq, pr, wall_set)
    
    if current_distance == float('inf') or current_distance == 0:
        return None, current_distance
    
    candidates = set()
    for nq, nr in get_neighbors(pq, pr):
        if is_valid(nq, nr) and (nq, nr) not in wall_set:
            candidates.add((nq, nr))
    
    for nq, nr in list(candidates):
        for nnq, nnr in get_neighbors(nq, nr):
            if is_valid(nnq, nnr) and (nnq, nnr) not in wall_set and (nnq, nnr) != (pq, pr):
                candidates.add((nnq, nnr))
    
    best_cell = None
    best_new_distance = current_distance
    
    for cell in candidates:
        test_walls = wall_set | {cell}
        new_distance = bfs_escape_distance(pq, pr, test_walls)
        if new_distance > best_new_distance:
            best_new_distance = new_distance
            best_cell = cell
    
    if best_cell:
        return best_cell, best_new_distance
    
    for nq, nr in get_neighbors(pq, pr):
        if is_valid(nq, nr) and (nq, nr) not in wall_set:
            return (nq, nr), current_distance
    
    return None, current_distance

def find_TRUE_optimal(pq, pr, wall_set):
    """Brute force check ALL cells"""
    current_distance = bfs_escape_distance(pq, pr, wall_set)
    
    if current_distance == float('inf') or current_distance == 0:
        return None, current_distance
    
    best_cell = None
    best_new_distance = current_distance
    
    for q in range(COL_MIN, COL_MAX + 1):
        for r in range(ROW_MIN, ROW_MAX + 1):
            if (q, r) not in wall_set and (q, r) != (pq, pr):
                test_walls = wall_set | {(q, r)}
                new_distance = bfs_escape_distance(pq, pr, test_walls)
                if new_distance > best_new_distance:
                    best_new_distance = new_distance
                    best_cell = (q, r)
    
    return best_cell, best_new_distance

def test_position(pq, pr, walls_list, test_name):
    """Test a single position and compare to true optimal."""
    wall_set = set((w['q'], w['r']) for w in walls_list)
    
    algo_cell, algo_dist = find_optimal_block(pq, pr, wall_set)
    true_cell, true_dist = find_TRUE_optimal(pq, pr, wall_set)
    
    if algo_dist == true_dist:
        return True, algo_cell, true_cell, algo_dist, true_dist
    else:
        return False, algo_cell, true_cell, algo_dist, true_dist

def run_stress_tests():
    print("="*60)
    print("STRESS TESTS: Testing all interior positions")
    print("="*60)
    
    failures = []
    total = 0
    
    # Test all interior positions (non-edge cells)
    for pq in range(1, 4):  # 1, 2, 3
        for pr in range(1, 10):  # 1-9
            total += 1
            passed, algo, true, algo_d, true_d = test_position(pq, pr, [], f"({pq},{pr}) no walls")
            if not passed:
                failures.append((pq, pr, [], algo, true, algo_d, true_d))
                print(f"  FAIL: Pig at ({pq},{pr}): algo={algo}(dist={algo_d}), true={true}(dist={true_d})")
    
    print(f"\n  Interior positions (no walls): {total - len(failures)}/{total} passed")
    
    # Test with some random wall configurations
    print("\n" + "="*60)
    print("STRESS TESTS: Random wall configurations")
    print("="*60)
    
    random.seed(42)  # Reproducible
    
    for i in range(20):
        # Random pig position in interior
        pq = random.randint(1, 3)
        pr = random.randint(2, 8)
        
        # Random walls (3-8 walls)
        num_walls = random.randint(3, 8)
        walls = []
        wall_set = set()
        for _ in range(num_walls):
            wq = random.randint(0, 4)
            wr = random.randint(0, 10)
            if (wq, wr) != (pq, pr) and (wq, wr) not in wall_set:
                walls.append({'q': wq, 'r': wr})
                wall_set.add((wq, wr))
        
        total += 1
        passed, algo, true, algo_d, true_d = test_position(pq, pr, walls, f"random_{i}")
        if not passed:
            failures.append((pq, pr, walls, algo, true, algo_d, true_d))
            print(f"  FAIL #{i}: Pig at ({pq},{pr}), {len(walls)} walls")
            print(f"         algo={algo}(dist={algo_d}), true={true}(dist={true_d})")
    
    print(f"\n  Random configs: {20 - len([f for f in failures if len(f[2]) > 0])}/20 passed")
    
    # Test specific tricky scenarios
    print("\n" + "="*60)
    print("STRESS TESTS: Tricky scenarios")
    print("="*60)
    
    tricky_tests = [
        # Pig at various distances from escape
        (2, 2, [], "Close to top edge"),
        (2, 8, [], "Close to bottom edge"),
        (1, 5, [], "Close to left edge"),
        (3, 5, [], "Close to right edge"),
        
        # Pig with partial surrounding
        (2, 5, [{'q': 1, 'r': 5}, {'q': 3, 'r': 5}], "Blocked left and right"),
        (2, 5, [{'q': 2, 'r': 4}, {'q': 2, 'r': 6}], "Blocked top and bottom"),
        
        # Narrow corridor
        (2, 5, [
            {'q': 1, 'r': 4}, {'q': 2, 'r': 4}, {'q': 3, 'r': 4},
            {'q': 1, 'r': 6}, {'q': 2, 'r': 6}, {'q': 3, 'r': 6}
        ], "Horizontal corridor"),
    ]
    
    for pq, pr, walls, name in tricky_tests:
        total += 1
        passed, algo, true, algo_d, true_d = test_position(pq, pr, walls, name)
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
        if not passed:
            failures.append((pq, pr, walls, algo, true, algo_d, true_d))
            print(f"         Pig at ({pq},{pr}): algo={algo}(dist={algo_d}), true={true}(dist={true_d})")
    
    # Summary
    print("\n" + "="*60)
    print("OVERALL SUMMARY")
    print("="*60)
    print(f"  Total tests: {total}")
    print(f"  Passed: {total - len(failures)}")
    print(f"  Failed: {len(failures)}")
    
    if failures:
        print("\n  FAILURE DETAILS:")
        for pq, pr, walls, algo, true, algo_d, true_d in failures[:5]:  # Show first 5
            print(f"    Pig({pq},{pr}), {len(walls)} walls: algo={algo}({algo_d}) vs true={true}({true_d})")
    
    return len(failures) == 0

if __name__ == "__main__":
    success = run_stress_tests()
    if success:
        print("\n✓ All stress tests passed!")
    else:
        print("\n✗ Some stress tests failed - algorithm needs work!")
