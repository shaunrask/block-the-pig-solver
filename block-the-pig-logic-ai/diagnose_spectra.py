"""
Comprehensive test suite to diagnose Spectra's strategic logic issues.
Focus: Why doesn't it block when pig is one move from escape?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

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
    if not is_valid(q, r):
        return False
    return q == COL_MIN or q == COL_MAX or r == ROW_MIN or r == ROW_MAX

def bfs_shortest_path(pq, pr, wall_set):
    """Find shortest path to escape, return list of cells (first is immediate next step)."""
    queue = deque([(pq, pr, [])])
    visited = {(pq, pr)}
    
    while queue:
        q, r, path = queue.popleft()
        
        if is_escape(q, r) and (q, r) != (pq, pr):
            return path
        
        for nq, nr in get_neighbors(q, r):
            if is_valid(nq, nr) and (nq, nr) not in visited and (nq, nr) not in wall_set:
                visited.add((nq, nr))
                queue.append((nq, nr, path + [(nq, nr)]))
    
    return []

def visualize(pig_pos, walls, highlight=None):
    """Print ASCII visualization."""
    wall_set = set(walls)
    for r in range(ROW_MIN, ROW_MAX + 1):
        indent = " " if r % 2 == 1 else ""
        row_str = indent
        for q in range(COL_MIN, COL_MAX + 1):
            if (q, r) == pig_pos:
                row_str += "🐷"
            elif highlight and (q, r) == highlight:
                row_str += "⭐"
            elif (q, r) in wall_set:
                row_str += "██"
            elif is_escape(q, r):
                row_str += "○ "
            else:
                row_str += "· "
        print(row_str)

def test_case(name, pig_pos, walls):
    """Test a scenario and show what SHOULD be blocked."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    
    wall_set = set(walls)
    path = bfs_shortest_path(pig_pos[0], pig_pos[1], wall_set)
    
    print(f"Pig at: {pig_pos}")
    print(f"Shortest path to escape: {path}")
    
    if path:
        should_block = path[0]
        print(f">>> MUST BLOCK: {should_block} <<<")
        print(f"Path length: {len(path)} moves to escape")
        
        if len(path) == 1:
            print("🚨 CRITICAL: Pig escapes in 1 move! Must block NOW!")
        
        visualize(pig_pos, wall_set, should_block)
    else:
        print("Pig is trapped or already escaped!")
        visualize(pig_pos, wall_set)
    
    return path[0] if path else None

# TEST CASES

print("="*60)
print("SPECTRA STRATEGIC LOGIC DIAGNOSTIC TESTS")
print("="*60)

# Critical case: Pig one move from escape (right edge)
must_block_1 = test_case(
    "CRITICAL: Pig at (3, 5) - ONE move from escape (col 4)",
    pig_pos=(3, 5),
    walls=[]
)
print(f"\nExpected block: (4, 5) or similar escape cell")

# Critical case: Pig one move from escape (left edge)
must_block_2 = test_case(
    "CRITICAL: Pig at (1, 5) - ONE move from escape (col 0)",
    pig_pos=(1, 5),
    walls=[]
)
print(f"\nExpected block: (0, 5) or the actual escape adjacent")

# Critical case: Pig one move from top edge
must_block_3 = test_case(
    "CRITICAL: Pig at (2, 1) - ONE move from escape (row 0)",
    pig_pos=(2, 1),
    walls=[]
)

# Normal case: Pig in center
test_case(
    "NORMAL: Pig at (2, 5) center - 2 moves from any escape",
    pig_pos=(2, 5),
    walls=[]
)

# Blocked path case
test_case(
    "BLOCKED: Pig surrounded on right - must go left",
    pig_pos=(2, 5),
    walls=[(3, 4), (3, 5), (3, 6), (4, 5)]
)

# Now test what Spectra actually generates
print("\n" + "="*60)
print("TESTING SPECTRA PROBLEM GENERATION")
print("="*60)

from app import generate_spectra_problem

# Test critical case
pig = {'q': 3, 'r': 5}  # One move from right edge!
walls = []
problem = generate_spectra_problem(pig, walls)

print(f"\nPig at (3, 5) - should prioritize blocking (4, 5)!")
print("Generated Spectra problem:")
print(problem)

# Check if the critical cell is marked
if "C_4_5" in problem:
    print("\n✓ C_4_5 is in the problem (good)")
else:
    print("\n✗ C_4_5 NOT in problem - THIS IS THE BUG!")

if "OnEscapePath C_4_5" in problem:
    print("✓ C_4_5 marked as OnEscapePath (good)")
else:
    print("✗ C_4_5 NOT marked as OnEscapePath - may not be prioritized!")

print("\n" + "="*60)
print("DIAGNOSIS")
print("="*60)
print("""
Key findings:
1. The BFS finds the CORRECT shortest path
2. But the problem generation may not mark the IMMEDIATE escape cell
3. Spectra's (exists) goal picks ANY cell, not the most urgent

FIX NEEDED:
- When pig is 1 move from escape, FORCE that cell as the only option
- Prioritize cells by distance to pig (closer = more urgent)
- Don't use (exists) - use specific blocking goal for critical cases
""")
