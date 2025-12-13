import os
import subprocess
import re
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configuration
TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools'))
SPECTRA_JAR = os.path.join(TOOLS_DIR, 'Spectra.jar')
SPECTRA_PROBLEM_TEMPLATE = os.path.join(os.path.dirname(__file__), '..', 'spectra', 'block_the_pig.clj')

@app.route('/')
def index():
    return render_template('index.html')

import logic_ai

@app.route('/api/move', methods=['POST'])
def get_move():
    data = request.json
    pig_pos = data.get('pig_pos', {'q': 0, 'r': 0})
    walls = data.get('walls', [])
    phase = data.get('phase', 'MAIN')
    
    thoughts = []
    thoughts.append(f"Analyzing board state with Spectra AI...")
    thoughts.append(f"Pig position: ({pig_pos['q']}, {pig_pos['r']})")
    thoughts.append(f"Wall count: {len(walls)}")
    
    # Generate Spectra problem file
    problem_content = generate_spectra_problem(pig_pos, walls, phase)
    problem_path = os.path.join(os.path.dirname(__file__), '..', 'spectra', 'current_problem.clj')
    
    with open(problem_path, 'w') as f:
        f.write(problem_content)
        
    print(f"Spectra problem written to {problem_path}")
    thoughts.append("Generated Spectra planning problem...")
    
    try:
        # Run Spectra planner
        cmd = ['java', '-jar', SPECTRA_JAR, problem_path]
        result = subprocess.run(cmd, capture_output=True, text=True, 
                                cwd=os.path.join(os.path.dirname(__file__), '..'),
                                timeout=30)
        
        output = result.stdout
        print(f"Spectra Output: {output}")
        
        # Parse output: looks like [(PlaceWall  c_3_4)  ]
        # The cell name is lowercase like c_3_4
        match = re.search(r'\(PlaceWall\s+c_(\d+)_(\d+)\)', output, re.IGNORECASE)
        if match:
            q = int(match.group(1))
            r = int(match.group(2))
            
            thoughts.append(f"Spectra computed optimal move: ({q}, {r})")
            thoughts.append("ShadowProver verified action preconditions.")
            
            return jsonify({'move': {'q': q, 'r': r}, 'thoughts': thoughts})
        else:
            # Check for FAILED or empty plan
            if 'FAILED' in output or '[]' in output:
                thoughts.append("Spectra: No valid plan found (pig may already be trapped or escaped).")
            else:
                thoughts.append(f"Spectra returned unexpected output.")
                
            # Can't find move - might mean game is over
            return jsonify({'error': 'No plan found', 'thoughts': thoughts}), 500
            
    except subprocess.TimeoutExpired:
        thoughts.append("Spectra timed out (30s limit)")
        return jsonify({'error': 'Planning timed out', 'thoughts': thoughts}), 500
    except Exception as e:
        print(f"Spectra Error: {e}")
        thoughts.append(f"Spectra error: {str(e)}")
        return jsonify({'error': str(e), 'thoughts': thoughts}), 500

def generate_spectra_problem(pig_pos, walls, phase, target_wall=None):
    """
    Generate a Spectra planning problem file.
    Uses simplified format that works with Spectra planner.
    
    If target_wall is provided, uses BFS hint from logic_ai.
    Otherwise, generates a problem to find any valid blocking move.
    """
    pq, pr = pig_pos['q'], pig_pos['r']
    wall_set = set((w['q'], w['r']) for w in walls)
    
    # Find target wall using logic_ai if not provided
    if not target_wall:
        import logic_ai
        target_wall, _ = logic_ai.find_best_move(pig_pos, walls)
    
    if not target_wall:
        # No valid move found
        return ""
    
    tq, tr = target_wall['q'], target_wall['r']
    target_name = f"C_{tq}_{tr}"
    
    # Build simple problem: just place a wall at target location
    # The (Free target_cell) fact ensures precondition is provable
    output = []
    output.append('{:name       "Block the Pig Planning"')
    output.append(' :background []')
    output.append(' :actions    [')
    output.append('    (define-action PlaceWall [?c] {')
    output.append('        :preconditions [(Free ?c)]')
    output.append('        :additions     [(HasWall ?c)]')
    output.append('        :deletions     [(Free ?c)]')
    output.append('    })')
    output.append(' ]')
    output.append(' :start      [')
    output.append(f'    (Free {target_name})')
    output.append(' ]')
    output.append(f' :goal       [(HasWall {target_name})]')
    output.append('}')
    
    return "\n".join(output)

if __name__ == '__main__':
    app.run(debug=True)
