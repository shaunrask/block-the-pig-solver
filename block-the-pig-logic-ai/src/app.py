import os
import re
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Grid constants (matching frontend)
COL_MIN, COL_MAX = 0, 4
ROW_MIN, ROW_MAX = 0, 10

# Py4J Gateway - connects to Spectra server (much faster than subprocess)
gateway = None

def get_gateway():
    """Get or create Py4J gateway to Spectra server."""
    global gateway
    if gateway is None:
        try:
            from py4j.java_gateway import JavaGateway
            gateway = JavaGateway()
            print("Connected to Spectra Py4J server")
        except Exception as e:
            print(f"Warning: Could not connect to Py4J server: {e}")
            return None
    return gateway

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
    
    # Generate Spectra problem
    problem_content = generate_spectra_problem(pig_pos, walls)
    
    if not problem_content:
        thoughts.append("No valid moves available.")
        return jsonify({'error': 'No valid moves', 'thoughts': thoughts}), 500
    
    # Save problem for debugging
    problem_path = os.path.join(os.path.dirname(__file__), '..', 'spectra', 'current_problem.clj')
    with open(problem_path, 'w') as f:
        f.write(problem_content)
    
    thoughts.append("Calling Spectra via Py4J (fast mode)...")
    
    try:
        gw = get_gateway()
        if gw:
            # Use Py4J - FAST (JVM already running)
            result = gw.entry_point.proveFromDescription(problem_content)
            print(f"Spectra Py4J Output: {result}")
            
            # Parse output
            match = re.search(r'\(PlaceWall\s+C_(\d+)_(\d+)\)', str(result), re.IGNORECASE)
            if match:
                q = int(match.group(1))
                r = int(match.group(2))
                
                thoughts.append(f"Spectra found move: ({q}, {r})")
                thoughts.append("Executed via Py4J (< 1 second).")
                
                return jsonify({'move': {'q': q, 'r': r}, 'thoughts': thoughts})
            else:
                thoughts.append("Spectra: No plan found.")
                return jsonify({'error': 'No plan found', 'thoughts': thoughts}), 500
        else:
            # Fallback to subprocess (slow)
            thoughts.append("Py4J not available, using subprocess (slower)...")
            return run_spectra_subprocess(problem_content, problem_path, thoughts)
            
    except Exception as e:
        print(f"Spectra Error: {e}")
        thoughts.append(f"Error: {str(e)}")
        # Fallback to subprocess
        return run_spectra_subprocess(problem_content, problem_path, thoughts)


def run_spectra_subprocess(problem_content, problem_path, thoughts):
    """Fallback: run Spectra via subprocess (slow, ~10s)."""
    import subprocess
    
    TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools'))
    SPECTRA_JAR = os.path.join(TOOLS_DIR, 'Spectra.jar')
    
    try:
        cmd = ['java', '-jar', SPECTRA_JAR, problem_path]
        result = subprocess.run(cmd, capture_output=True, text=True, 
                                cwd=os.path.join(os.path.dirname(__file__), '..'),
                                timeout=60)
        
        output = result.stdout
        print(f"Spectra Output: {output}")
        
        match = re.search(r'\(PlaceWall\s+C_(\d+)_(\d+)\)', output, re.IGNORECASE)
        if match:
            q = int(match.group(1))
            r = int(match.group(2))
            
            thoughts.append(f"Spectra found move: ({q}, {r})")
            thoughts.append("(subprocess mode - slower)")
            
            return jsonify({'move': {'q': q, 'r': r}, 'thoughts': thoughts})
        else:
            thoughts.append("Spectra: No plan found.")
            return jsonify({'error': 'No plan found', 'thoughts': thoughts}), 500
            
    except Exception as e:
        thoughts.append(f"Subprocess error: {str(e)}")
        return jsonify({'error': str(e), 'thoughts': thoughts}), 500


def generate_spectra_problem(pig_pos, walls):
    """
    Generate a Spectra planning problem.
    Spectra will find a valid PlaceWall action adjacent to the pig.
    """
    pq, pr = pig_pos['q'], pig_pos['r']
    wall_set = set((w['q'], w['r']) for w in walls)
    
    def cell_name(q, r):
        return f"C_{q}_{r}"
    
    def get_neighbors(q, r):
        if r % 2 == 0:
            return [(q+1, r), (q, r-1), (q-1, r-1), (q-1, r), (q-1, r+1), (q, r+1)]
        else:
            return [(q+1, r), (q+1, r-1), (q, r-1), (q-1, r), (q, r+1), (q+1, r+1)]
    
    def is_valid(q, r):
        return COL_MIN <= q <= COL_MAX and ROW_MIN <= r <= ROW_MAX
    
    # Find free cells adjacent to pig
    free_adjacent = []
    for nq, nr in get_neighbors(pq, pr):
        if is_valid(nq, nr) and (nq, nr) not in wall_set and (nq, nr) != (pq, pr):
            free_adjacent.append((nq, nr))
    
    if not free_adjacent:
        return None
    
    # Build Spectra problem
    output = []
    output.append('{:name       "Block the Pig"')
    output.append(' :background [')
    
    # Mark cells adjacent to pig
    for nq, nr in get_neighbors(pq, pr):
        if is_valid(nq, nr) and (nq, nr) not in wall_set:
            output.append(f'    (AdjacentToPig {cell_name(nq, nr)})')
    
    output.append(' ]')
    
    # PlaceWall action with strategic constraint
    output.append(' :actions    [')
    output.append('    (define-action PlaceWall [?c] {')
    output.append('        :preconditions [(Free ?c) (AdjacentToPig ?c)]')
    output.append('        :additions     [(Blocked ?c)]')
    output.append('        :deletions     [(Free ?c)]')
    output.append('    })')
    output.append(' ]')
    
    # Start: Mark free cells
    output.append(' :start      [')
    for q, r in free_adjacent:
        output.append(f'    (Free {cell_name(q, r)})')
    output.append(' ]')
    
    # Goal: Block any adjacent cell
    output.append(' :goal       [(exists (?x) (Blocked ?x))]')
    output.append('}')
    
    return "\n".join(output)


if __name__ == '__main__':
    app.run(debug=True)
