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
    # Use logic_ai to define the grid, ensuring consistency with frontend
    cells = []
    escapes = []
    
    # 5x11 Grid (0..4, 0..10)
    for q in range(5):
        for r in range(11):
            cells.append((q, r))
            if logic_ai.is_escape(q, r):
                escapes.append((q, r))

    # Generate adjacencies using logic_ai.get_neighbors
    adjacencies = []
    for q, r in cells:
        neighbors = logic_ai.get_neighbors(q, r)
        for nq, nr in neighbors:
            if logic_ai.is_valid(nq, nr):
                # Add directed edge (or undirected if added twice)
                # We can add all valid neighbors
                adjacencies.append(((q, r), (nq, nr)))

    # Build Background (Axioms)
    background = []
    
    # 1. Adjacency Axioms
    for (q1, r1), (q2, r2) in adjacencies:
        n1 = f"C_{q1}_{r1}".replace("-", "m")
        n2 = f"C_{q2}_{r2}".replace("-", "m")
        background.append(f"(Adjacent {n1} {n2})")

    # 2. Escape Axioms
    for q, r in escapes:
        name = f"C_{q}_{r}".replace("-", "m")
        background.append(f"(Escape {name})")

    # 3. Domain Rules
    background.append("(forall (c) (if (OccupiedByPig c) (not (HasWall c))))")
    background.append("(forall (c) (if (HasWall c) (not (Escape c))))")

    # Trapped Definition
    background.append("(iff Trapped (forall (c1) (if (OccupiedByPig c1) (forall (c2) (if (Adjacent c1 c2) (HasWall c2))))))")

    # Build Actions
    actions = []
    
    # PlaceWall
    actions.append("""
        (define-action PlaceWall [?c] {
            :preconditions [(Free ?c)]
            :additions [(HasWall ?c)]
            :deletions [(Free ?c)]
        })
    """)
    
    # PigMove - Only include if in MAIN phase
    if phase == 'MAIN':
        actions.append("""
            (define-action PigMove [?a ?b] {
                :preconditions [(OccupiedByPig ?a) (Adjacent ?a ?b) (Free ?b)]
                :additions [(OccupiedByPig ?b) (Free ?a)]
                :deletions [(OccupiedByPig ?a) (Free ?b)]
            })
        """)

    # Build Start
    start = []
    
    # Pig Position
    pq, pr = pig_pos['q'], pig_pos['r']
    p_name = f"C_{pq}_{pr}".replace("-", "m")
    start.append(f"(OccupiedByPig {p_name})")
    
    # Walls
    wall_set = set()
    for w in walls:
        wq, wr = w['q'], w['r']
        w_name = f"C_{wq}_{wr}".replace("-", "m")
        start.append(f"(HasWall {w_name})")
        wall_set.add((wq, wr))

    # Free cells
    for c in cells:
        if c != (pq, pr) and c not in wall_set:
            name = f"C_{c[0]}_{c[1]}".replace("-", "m")
            start.append(f"(Free {name})")

    # Build Goal
    goal = []
    if target_wall:
        tq, tr = target_wall['q'], target_wall['r']
        t_name = f"C_{tq}_{tr}".replace("-", "m")
        goal.append(f"(HasWall {t_name})")
    else:
        goal.append("(Trapped)")

    # Format Output
    output = []
    output.append("{:name \"Block the Pig Planning\"")
    output.append(" :background [")
    for b in background:
        output.append(f"    {b}")
    output.append(" ]")
    
    output.append(" :actions [")
    for a in actions:
        output.append(a)
    output.append(" ]")
    
    output.append(" :start [")
    for s in start:
        output.append(f"    {s}")
    output.append(" ]")
    
    output.append(" :goal [")
    for g in goal:
        output.append(f"    {g}")
    output.append(" ]")
    output.append("}")

    return "\n".join(output)

if __name__ == '__main__':
    app.run(debug=True)
