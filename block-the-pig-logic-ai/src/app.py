from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Grid constants (matching frontend)
COL_MIN, COL_MAX = 0, 4
ROW_MIN, ROW_MAX = 0, 10

@app.route('/')
def index():
    return render_template('index.html')


def find_optimal_block(pig_pos, walls):
    """
    Find the optimal cell to block using 2-ply minimax:
    1. We place a wall
    2. Pig makes its best move (toward escape)
    3. Evaluate the resulting escape distance
    
    The best wall is one that maximizes escape distance AFTER pig responds.
    
    Returns:
        (best_move_dict, thoughts_list)
    """
    from collections import deque
    
    pq, pr = pig_pos['q'], pig_pos['r']
    wall_set = set((w['q'], w['r']) for w in walls)
    
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
        """BFS to find minimum distance from a position to any escape cell."""
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
        """Get the pig's best move (first step on shortest path to escape)."""
        if is_escape(pig_q, pig_r):
            return (pig_q, pig_r)  # Already escaped
        
        # BFS to find path
        queue = deque([(pig_q, pig_r, [])])
        visited = {(pig_q, pig_r)}
        
        while queue:
            q, r, path = queue.popleft()
            
            if is_escape(q, r):
                if path:
                    return path[0]  # First step
                return (q, r)
            
            for nq, nr in get_neighbors(q, r):
                if is_valid(nq, nr) and (nq, nr) not in visited and (nq, nr) not in blocked_cells:
                    visited.add((nq, nr))
                    queue.append((nq, nr, path + [(nq, nr)]))
        
        return None  # Trapped
    
    thoughts = []
    
    # Current escape distance without any new wall
    current_distance = bfs_escape_distance(pq, pr, wall_set)
    thoughts.append(f"Current escape distance: {current_distance if current_distance != float('inf') else 'trapped'}")
    
    if current_distance == float('inf'):
        thoughts.append("Pig is already trapped!")
        return None, thoughts
    
    if current_distance == 0:
        thoughts.append("Pig is already at an escape - too late to block!")
        return None, thoughts
    
    # Get candidate cells: neighbors of pig + cells within 2 steps
    candidates = set()
    
    for nq, nr in get_neighbors(pq, pr):
        if is_valid(nq, nr) and (nq, nr) not in wall_set:
            candidates.add((nq, nr))
    
    for nq, nr in list(candidates):
        for nnq, nnr in get_neighbors(nq, nr):
            if is_valid(nnq, nnr) and (nnq, nnr) not in wall_set and (nnq, nnr) != (pq, pr):
                candidates.add((nnq, nnr))
    
    thoughts.append(f"Evaluating {len(candidates)} moves with lookahead...")
    
    # Evaluate each candidate with 2-ply minimax
    best_cell = None
    best_score = -float('inf')
    
    for cell in candidates:
        # Step 1: Place wall
        test_walls = wall_set | {cell}
        
        # Check if this immediately traps the pig
        dist_after_wall = bfs_escape_distance(pq, pr, test_walls)
        if dist_after_wall == float('inf'):
            # Winning move!
            thoughts.append(f"Found winning move at ({cell[0]}, {cell[1]}) - traps the pig!")
            return {'q': cell[0], 'r': cell[1]}, thoughts
        
        # Step 2: Simulate pig's response (pig moves toward escape)
        pig_move = get_pig_best_move(pq, pr, test_walls)
        
        if pig_move is None:
            # Pig would be trapped after our wall
            thoughts.append(f"Found winning move at ({cell[0]}, {cell[1]}) - traps the pig!")
            return {'q': cell[0], 'r': cell[1]}, thoughts
        
        # Step 3: Evaluate position after pig moves
        new_pig_q, new_pig_r = pig_move
        
        # Check if pig escapes
        if is_escape(new_pig_q, new_pig_r):
            # This wall placement lets pig escape - bad!
            score = -100
        else:
            # Score = escape distance from pig's new position
            score = bfs_escape_distance(new_pig_q, new_pig_r, test_walls)
            if score == float('inf'):
                score = 100  # Trapped = very good
        
        if score > best_score:
            best_score = score
            best_cell = cell
    
    if best_cell:
        if best_score == 100:
            thoughts.append(f"Best block: ({best_cell[0]}, {best_cell[1]}) - forces trap after pig moves")
        elif best_score > 0:
            thoughts.append(f"Best block: ({best_cell[0]}, {best_cell[1]}) - escape distance after pig moves: {best_score}")
        else:
            thoughts.append(f"Best defensive block: ({best_cell[0]}, {best_cell[1]})")
        return {'q': best_cell[0], 'r': best_cell[1]}, thoughts
    
    # Fallback: block first neighbor
    for nq, nr in get_neighbors(pq, pr):
        if is_valid(nq, nr) and (nq, nr) not in wall_set:
            thoughts.append(f"Fallback: blocking neighbor ({nq}, {nr})")
            return {'q': nq, 'r': nr}, thoughts
    
    thoughts.append("No valid moves available")
    return None, thoughts


@app.route('/api/move', methods=['POST'])
def get_move():
    data = request.json
    pig_pos = data.get('pig_pos', {'q': 0, 'r': 0})
    walls = data.get('walls', [])
    
    thoughts = []
    thoughts.append(f"Analyzing board with strategic AI...")
    thoughts.append(f"Pig position: ({pig_pos['q']}, {pig_pos['r']})")
    
    # Find optimal blocking move using strategic analysis
    optimal_move, analysis_thoughts = find_optimal_block(pig_pos, walls)
    thoughts.extend(analysis_thoughts)
    
    if not optimal_move:
        return jsonify({'error': 'No valid moves', 'thoughts': thoughts}), 500
    
    return jsonify({'move': optimal_move, 'thoughts': thoughts})


if __name__ == '__main__':
    app.run(debug=True)

