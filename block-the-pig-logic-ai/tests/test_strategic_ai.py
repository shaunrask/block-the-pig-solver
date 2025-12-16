"""
Test the strategic AI logic to debug incorrect move selection.
"""
import sys
sys.path.insert(0, 'src')

from collections import deque

# Grid constants
COL_MIN, COL_MAX = 0, 4
ROW_MIN, ROW_MAX = 0, 10

def get_neighbors(q, r):
    """Get hex neighbors for odd-row offset layout."""
    if r % 2 == 0:
        return [(q+1, r), (q, r-1), (q-1, r-1), (q-1, r), (q-1, r+1), (q, r+1)]
    else:
        return [(q+1, r), (q+1, r-1), (q, r-1), (q-1, r), (q, r+1), (q+1, r+1)]

def is_valid(q, r):
    return COL_MIN <= q <= COL_MAX and ROW_MIN <= r <= ROW_MAX

def is_escape(q, r):
    """Border cells are escape cells."""
    if not is_valid(q, r):
        return False
    return q == COL_MIN or q == COL_MAX or r == ROW_MIN or r == ROW_MAX

def bfs_shortest_path(start_q, start_r, wall_set):
    """Find shortest path from pig to escape."""
    queue = deque([(start_q, start_r, [])])
    visited = {(start_q, start_r)}
    
    while queue:
        q, r, path = queue.popleft()
        
        if is_escape(q, r) and (q, r) != (start_q, start_r):
            return path
        
        for nq, nr in get_neighbors(q, r):
            if is_valid(nq, nr) and (nq, nr) not in visited and (nq, nr) not in wall_set:
                visited.add((nq, nr))
                queue.append((nq, nr, path + [(nq, nr)]))
    
    return []

def visualize_board(pig_pos, walls, strategic_cells=None, selected_move=None):
    """Print ASCII visualization of the board."""
    print("\n" + "="*40)
    print(f"Pig at: {pig_pos}")
    print(f"Walls: {len(walls)}")
    print("="*40)
    
    for r in range(ROW_MIN, ROW_MAX + 1):
        indent = " " if r % 2 == 1 else ""
        row_str = indent
        for q in range(COL_MIN, COL_MAX + 1):
            if (q, r) == pig_pos:
                row_str += " 🐷"
            elif selected_move and (q, r) == selected_move:
                row_str += " ⭐"
            elif (q, r) in walls:
                row_str += " ██"
            elif strategic_cells and (q, r) in strategic_cells:
                row_str += " ◉ "
            elif is_escape(q, r):
                row_str += " ○ "
            else:
                row_str += " · "
        print(row_str)
    
    print("\nLegend: 🐷=Pig, ██=Wall, ◉=Strategic, ⭐=AI Move, ○=Escape, ·=Empty")

def test_case(name, pig_pos, walls):
    """Run a test case and show results."""
    print(f"\n{'#'*50}")
    print(f"TEST: {name}")
    print(f"{'#'*50}")
    
    wall_set = set(walls)
    pq, pr = pig_pos
    
    # Find shortest path
    path = bfs_shortest_path(pq, pr, wall_set)
    print(f"\nShortest escape path: {path}")
    
    if path:
        print(f"  First cell on path (should block): {path[0]}")
        print(f"  Path length: {len(path)} steps to escape")
    else:
        print("  No escape path found - pig is trapped!")
    
    # Get strategic cells (same logic as app.py)
    strategic_cells = []
    if path:
        for cell in path[:3]:
            strategic_cells.append(cell)
    
    print(f"\nStrategic cells to consider: {strategic_cells}")
    
    # The BEST move should be the FIRST cell on the shortest path
    best_move = path[0] if path else None
    print(f"OPTIMAL MOVE: {best_move}")
    
    visualize_board(pig_pos, wall_set, strategic_cells, best_move)
    
    return best_move

# Run test cases
print("="*60)
print("STRATEGIC AI DEBUG TEST SUITE")
print("="*60)

# Test 1: Pig in center, no walls
test_case(
    "Pig in center (2,5), no walls",
    pig_pos=(2, 5),
    walls=[]
)

# Test 2: Pig in center with some walls
test_case(
    "Pig in center with walls blocking left",
    pig_pos=(2, 5),
    walls=[(1, 5), (1, 4), (1, 6)]
)

# Test 3: Pig near corner
test_case(
    "Pig near top-left corner (1, 1)",
    pig_pos=(1, 1),
    walls=[]
)

# Test 4: Pig almost trapped (one exit)
test_case(
    "Pig almost trapped - only one escape route",
    pig_pos=(2, 5),
    walls=[(1, 4), (2, 4), (3, 4), (3, 5), (3, 6), (2, 6), (1, 6)]
)

# Test 5: Complex scenario
test_case(
    "Complex game state",
    pig_pos=(2, 5),
    walls=[(0, 3), (1, 2), (3, 7), (4, 8), (2, 9)]
)

print("\n" + "="*60)
print("ANALYSIS:")
print("="*60)
print("""
The AI should ALWAYS place a wall on the FIRST cell of the 
shortest escape path. This minimizes the pig's escape options.

If the AI is placing walls elsewhere, the issue is likely in 
how Spectra selects from the strategic cells list.

Current approach sends multiple strategic cells to Spectra,
but Spectra's (exists (?x) (Blocked ?x)) goal just picks ANY
cell, not necessarily the most strategic one.

FIX: Order cells by priority and only send the TOP choice to 
Spectra, OR change the goal to force blocking the first cell.
""")
