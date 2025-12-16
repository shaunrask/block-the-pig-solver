"""
Comprehensive tests for the Block the Pig AI algorithm.
Tests various scenarios to verify the AI picks optimal blocking moves.
"""
import sys
import os

# Add parent directory to path to import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app import find_optimal_block, bfs_escape_path, is_escape, COL_MIN, COL_MAX, ROW_MIN, ROW_MAX

# Helper for test compatibility - app.py now returns (dist, step), tests expect dist on escape
def bfs_escape_distance(pq, pr, blocked_cells):
    dist, _ = bfs_escape_path(pq, pr, blocked_cells)
    return dist

def find_optimal_block_wrapper(pig_pos, walls):
    # Call the actual AI logic from src.app
    move, thoughts = find_optimal_block(pig_pos, walls)
    if move:
        test_walls = set((w['q'], w['r']) for w in walls) | {(move['q'], move['r'])}
        dist, _ = bfs_escape_path(pig_pos['q'], pig_pos['r'], test_walls)
        return move, dist
    return None, 0


def find_TRUE_optimal(pig_pos, walls):
    """
    Brute force: Check ALL free cells, not just near pig.
    This is the ground truth for comparison.
    """
    pq, pr = pig_pos['q'], pig_pos['r']
    wall_set = set((w['q'], w['r']) for w in walls)
    
    current_distance = bfs_escape_distance(pq, pr, wall_set)
    
    if current_distance == float('inf') or current_distance == 0:
        return None, current_distance
    
    # Check ALL free cells
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
    
    if best_cell:
        return {'q': best_cell[0], 'r': best_cell[1]}, best_new_distance
    
    return None, current_distance

def visualize_grid(pig_pos, walls, suggested_move=None):
    """Print a simple visualization of the hex grid."""
    pq, pr = pig_pos['q'], pig_pos['r']
    wall_set = set((w['q'], w['r']) for w in walls)
    suggested = (suggested_move['q'], suggested_move['r']) if suggested_move and 'q' in suggested_move else None
    
    print("\n  Grid (q: 0-4, r: 0-10):")
    for r in range(ROW_MIN, ROW_MAX + 1):
        indent = "  " if r % 2 == 1 else ""
        row = indent
        for q in range(COL_MIN, COL_MAX + 1):
            if (q, r) == (pq, pr):
                row += " P "
            elif (q, r) == suggested:
                row += " X "
            elif (q, r) in wall_set:
                row += " # "
            elif is_escape(q, r):
                row += " . "
            else:
                row += " o "
        print(f"  r={r:2d}: {row}")
    print("  Legend: P=pig, #=wall, X=suggested, .=escape, o=interior")

# ============ TEST CASES ============

def test_case_1():
    """Pig in center, no walls - should block toward nearest escape."""
    print("\n" + "="*60)
    print("TEST 1: Pig in center (2,5), no walls")
    print("="*60)
    
    pig = {'q': 2, 'r': 5}
    walls = []
    
    move, dist = find_optimal_block_wrapper(pig, walls)
    true_move, true_dist = find_TRUE_optimal(pig, walls)
    
    visualize_grid(pig, walls, move)
    
    print(f"\n  Algorithm suggests: {move} (new distance: {dist})")
    print(f"  TRUE optimal:       {true_move} (new distance: {true_dist})")
    
    if dist == true_dist:
        print("  ✓ PASS - Same optimal distance")
    else:
        print(f"  ✗ FAIL - Algorithm missed better option!")
    
    return dist == true_dist

def test_case_2():
    """Pig one step from escape - MUST block the escape cell."""
    print("\n" + "="*60)
    print("TEST 2: Pig at (1,5), one step from left edge escape")
    print("="*60)
    
    pig = {'q': 1, 'r': 5}
    walls = []
    
    move, dist = find_optimal_block_wrapper(pig, walls)
    true_move, true_dist = find_TRUE_optimal(pig, walls)
    
    visualize_grid(pig, walls, move)
    
    print(f"\n  Current escape distance: {bfs_escape_distance(1, 5, set())}")
    print(f"  Algorithm suggests: {move} (new distance: {dist})")
    print(f"  TRUE optimal:       {true_move} (new distance: {true_dist})")
    
    # The optimal move should be (0, 5) - blocking the immediate escape
    if move and move['q'] == 0:
        print("  ✓ PASS - Correctly blocked escape direction")
    else:
        print(f"  ? Check - Is blocking {move} optimal?")
    
    return dist == true_dist

def test_case_3():
    """Pig nearly surrounded - only one escape route."""
    print("\n" + "="*60)
    print("TEST 3: Pig at (2,5) with walls creating funnel")
    print("="*60)
    
    pig = {'q': 2, 'r': 5}
    # Create walls that funnel toward one direction
    walls = [
        {'q': 1, 'r': 4}, {'q': 2, 'r': 4}, {'q': 3, 'r': 4},  # Top walls
        {'q': 1, 'r': 6}, {'q': 2, 'r': 6}, {'q': 3, 'r': 6},  # Bottom walls
        {'q': 1, 'r': 5},  # Left side
    ]
    
    move, dist = find_optimal_block(pig, walls)
    true_move, true_dist = find_TRUE_optimal(pig, walls)
    
    visualize_grid(pig, walls, move)
    
    print(f"\n  Algorithm suggests: {move} (new distance: {dist})")
    print(f"  TRUE optimal:       {true_move} (new distance: {true_dist})")
    
    if dist == true_dist:
        print("  ✓ PASS - Same optimal distance")
    else:
        print(f"  ✗ FAIL - Algorithm missed better option!")
    
    return dist == true_dist

def test_case_4():
    """Pig can be trapped with one move."""
    print("\n" + "="*60)
    print("TEST 4: Pig at (2,5) nearly trapped - one move to win")
    print("="*60)
    
    pig = {'q': 2, 'r': 5}
    # Surround pig leaving only one exit
    walls = [
        {'q': 3, 'r': 5},
        {'q': 2, 'r': 4}, {'q': 3, 'r': 4},
        {'q': 1, 'r': 5},
        {'q': 1, 'r': 6}, {'q': 2, 'r': 6},
    ]
    
    move, dist = find_optimal_block_wrapper(pig, walls)
    true_move, true_dist = find_TRUE_optimal(pig, walls)
    
    visualize_grid(pig, walls, move)
    
    print(f"\n  Algorithm suggests: {move} (new distance: {dist})")
    print(f"  TRUE optimal:       {true_move} (new distance: {true_dist})")
    
    if dist == float('inf'):
        print("  ✓ PASS - Found winning (trapping) move!")
    else:
        print(f"  ✗ FAIL - Should have trapped the pig!")
    
    return dist == true_dist

def test_case_5():
    """Pig near corner - test edge behavior."""
    print("\n" + "="*60)
    print("TEST 5: Pig at corner area (1,1)")
    print("="*60)
    
    pig = {'q': 1, 'r': 1}
    walls = []
    
    move, dist = find_optimal_block_wrapper(pig, walls)
    true_move, true_dist = find_TRUE_optimal(pig, walls)
    
    visualize_grid(pig, walls, move)
    
    print(f"\n  Algorithm suggests: {move} (new distance: {dist})")
    print(f"  TRUE optimal:       {true_move} (new distance: {true_dist})")
    
    if dist == true_dist:
        print("  ✓ PASS - Same optimal distance")
    else:
        print(f"  ✗ FAIL - Algorithm missed better option!")
    
    return dist == true_dist

def test_case_6():
    """Chokepoint test - blocking one cell should cut off multiple paths."""
    print("\n" + "="*60)
    print("TEST 6: Chokepoint scenario")
    print("="*60)
    
    pig = {'q': 2, 'r': 5}
    # Walls creating a chokepoint
    walls = [
        {'q': 1, 'r': 4}, {'q': 3, 'r': 4},  # Partial top
        {'q': 1, 'r': 6}, {'q': 3, 'r': 6},  # Partial bottom
    ]
    
    move, dist = find_optimal_block_wrapper(pig, walls)
    true_move, true_dist = find_TRUE_optimal(pig, walls)
    
    visualize_grid(pig, walls, move)
    
    print(f"\n  Algorithm suggests: {move} (new distance: {dist})")
    print(f"  TRUE optimal:       {true_move} (new distance: {true_dist})")
    
    if dist == true_dist:
        print("  ✓ PASS - Same optimal distance")
    else:
        print(f"  ✗ FAIL - Algorithm missed better option! Diff: {true_dist - dist}")
    
    return dist == true_dist

def test_case_7():
    """Test with pig already at escape cell."""
    print("\n" + "="*60)
    print("TEST 7: Pig already at escape (0, 5)")
    print("="*60)
    
    pig = {'q': 0, 'r': 5}
    walls = []
    
    move, dist = find_optimal_block_wrapper(pig, walls)
    
    print(f"  Pig is ON an escape cell (left edge)")
    print(f"  Algorithm returns: {move}")
    
    # Should return None since pig is already at escape
    if move is None:
        print("  ✓ PASS - Correctly identified pig at escape")
        return True
    else:
        print("  ✗ FAIL - Should return None when pig is at escape")
        return False

def test_all():
    """Run all tests and summarize."""
    print("\n" + "#"*60)
    print("# RUNNING ALL TESTS")
    print("#"*60)
    
    results = [
        ("Test 1: Center pig", test_case_1()),
        ("Test 2: One step from escape", test_case_2()),
        ("Test 3: Funnel walls", test_case_3()),
        ("Test 4: Nearly trapped", test_case_4()),
        ("Test 5: Corner pig", test_case_5()),
        ("Test 6: Chokepoint", test_case_6()),
        ("Test 7: Pig at escape", test_case_7()),
    ]
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed < total:
        print("\n  ⚠ Some tests failed - algorithm needs improvement!")
    else:
        print("\n  ✓ All tests passed!")

if __name__ == "__main__":
    test_all()
