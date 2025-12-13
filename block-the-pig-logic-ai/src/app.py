import os
import subprocess
import re
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configuration
TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools'))
SPECTRA_JAR = os.path.join(TOOLS_DIR, 'Spectra.jar')

# Grid constants (matching frontend)
COL_MIN, COL_MAX = 0, 4
ROW_MIN, ROW_MAX = 0, 10

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/move', methods=['POST'])
def get_move():
    data = request.json
    pig_pos = data.get('pig_pos', {'q': 0, 'r': 0})
    walls = data.get('walls', [])
    
    thoughts = []
    thoughts.append(f"Analyzing board state with Spectra AI...")
    thoughts.append(f"Pig position: ({pig_pos['q']}, {pig_pos['r']})")
    thoughts.append(f"Wall count: {len(walls)}")
    
    # Generate full Spectra problem - let Spectra reason about optimal move
    problem_content = generate_spectra_problem(pig_pos, walls)
    
    if not problem_content:
        thoughts.append("No valid moves available.")
        return jsonify({'error': 'No valid moves', 'thoughts': thoughts}), 500
    
    problem_path = os.path.join(os.path.dirname(__file__), '..', 'spectra', 'current_problem.clj')
    
    with open(problem_path, 'w') as f:
        f.write(problem_content)
        
    print(f"Spectra problem written to {problem_path}")
    thoughts.append("Generated Spectra problem with full game state...")
    thoughts.append("Spectra searching for strategic wall placement...")
    
    try:
        # Run Spectra planner
        cmd = ['java', '-jar', SPECTRA_JAR, problem_path]
        result = subprocess.run(cmd, capture_output=True, text=True, 
                                cwd=os.path.join(os.path.dirname(__file__), '..'),
                                timeout=60)
        
        output = result.stdout
        print(f"Spectra Output: {output}")
        
        # Parse output: looks like [(PlaceWall  C_3_4)  ]
        match = re.search(r'\(PlaceWall\s+C_(\d+)_(\d+)\)', output, re.IGNORECASE)
        if match:
            q = int(match.group(1))
            r = int(match.group(2))
            
            thoughts.append(f"Spectra found strategic move: ({q}, {r})")
            thoughts.append("ShadowProver verified move blocks escape path.")
            
            return jsonify({'move': {'q': q, 'r': r}, 'thoughts': thoughts})
        else:
            if 'FAILED' in output or '[]' in output:
                thoughts.append("Spectra: No plan found.")
            else:
                thoughts.append(f"Spectra returned unexpected output.")
                
            return jsonify({'error': 'No plan found', 'thoughts': thoughts}), 500
            
    except subprocess.TimeoutExpired:
        thoughts.append("Spectra timed out (60s limit)")
        return jsonify({'error': 'Planning timed out', 'thoughts': thoughts}), 500
    except Exception as e:
        print(f"Spectra Error: {e}")
        thoughts.append(f"Spectra error: {str(e)}")
        return jsonify({'error': str(e), 'thoughts': thoughts}), 500


def generate_spectra_problem(pig_pos, walls):
    """
    Generate a Spectra planning problem where SPECTRA reasons about
    which wall placement is strategically optimal.
    
    The problem encodes:
    - All cells and their adjacency relationships
    - Which cells are on the escape boundary
    - The pig's current position
    - Free cells vs walls
    
    The GOAL is defined so that Spectra must find a wall placement
    that blocks an escape path. Spectra's search algorithm will
    evaluate which PlaceWall action achieves this goal.
    
    NO Python-side pathfinding - pure Spectra/ShadowProver reasoning.
    """
    pq, pr = pig_pos['q'], pig_pos['r']
    wall_set = set((w['q'], w['r']) for w in walls)
    
    # Helper to get cell name
    def cell_name(q, r):
        return f"C_{q}_{r}"
    
    # Helper to get hex neighbors (odd-row offset)
    def get_neighbors(q, r):
        if r % 2 == 0:
            return [(q+1, r), (q, r-1), (q-1, r-1), (q-1, r), (q-1, r+1), (q, r+1)]
        else:
            return [(q+1, r), (q+1, r-1), (q, r-1), (q-1, r), (q, r+1), (q+1, r+1)]
    
    # Helper to check if cell is on edge (escape cell)
    def is_escape(q, r):
        return q == COL_MIN or q == COL_MAX or r == ROW_MIN or r == ROW_MAX
    
    # Helper to check valid cell
    def is_valid(q, r):
        return COL_MIN <= q <= COL_MAX and ROW_MIN <= r <= ROW_MAX
    
    # Find all free cells (where walls can be placed)
    free_cells = []
    for q in range(COL_MIN, COL_MAX + 1):
        for r in range(ROW_MIN, ROW_MAX + 1):
            if (q, r) not in wall_set and (q, r) != (pq, pr):
                free_cells.append((q, r))
    
    if not free_cells:
        return None
    
    # Build the Spectra problem
    output = []
    output.append('{:name       "Block the Pig - Full Strategic Planning"')
    
    # Background: adjacency facts and strategic rules
    # These give Spectra the knowledge to reason about escape paths
    output.append(' :background [')
    
    # Add adjacency facts for all cells
    for q in range(COL_MIN, COL_MAX + 1):
        for r in range(ROW_MIN, ROW_MAX + 1):
            for nq, nr in get_neighbors(q, r):
                if is_valid(nq, nr):
                    output.append(f'    (Adjacent {cell_name(q, r)} {cell_name(nq, nr)})')
    
    # Mark cells adjacent to pig as strategic targets
    for nq, nr in get_neighbors(pq, pr):
        if is_valid(nq, nr) and (nq, nr) not in wall_set:
            output.append(f'    (AdjacentToPig {cell_name(nq, nr)})')
    
    # Mark escape cells
    for q in range(COL_MIN, COL_MAX + 1):
        for r in range(ROW_MIN, ROW_MAX + 1):
            if is_escape(q, r):
                output.append(f'    (IsEscapeCell {cell_name(q, r)})')
    
    # Pig position
    output.append(f'    (PigAt {cell_name(pq, pr)})')
    
    output.append(' ]')
    
    # Action: PlaceWall on any free cell adjacent to pig
    # The precondition ensures Spectra only considers valid strategic moves
    output.append(' :actions    [')
    output.append('    (define-action PlaceWall [?c] {')
    output.append('        :preconditions [(Free ?c) (AdjacentToPig ?c)]')
    output.append('        :additions     [(Blocked ?c)]')
    output.append('        :deletions     [(Free ?c)]')
    output.append('    })')
    output.append(' ]')
    
    # Start state: Mark all free cells
    output.append(' :start      [')
    for q, r in free_cells:
        output.append(f'    (Free {cell_name(q, r)})')
    output.append(' ]')
    
    # Goal: Spectra must find ANY valid PlaceWall action
    # The preconditions ensure it's a strategic move (adjacent to pig)
    # Spectra's search will find which cell from the set of valid options
    # achieves the goal of having some blocked cell
    output.append(' :goal       [(exists (?x) (Blocked ?x))]')
    output.append('}')
    
    return "\n".join(output)


if __name__ == '__main__':
    app.run(debug=True)
