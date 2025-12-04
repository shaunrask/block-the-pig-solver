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

@app.route('/api/move', methods=['POST'])
def get_move():
    data = request.json
    pig_pos = data.get('pig_pos', {'q': 0, 'r': 0})
    walls = data.get('walls', [])
    phase = data.get('phase', 'MAIN') # 'OPENING' or 'MAIN'
    
    # 1. Generate Spectra Problem File
    problem_content = generate_spectra_problem(pig_pos, walls, phase)
    problem_path = os.path.join(os.path.dirname(__file__), '..', 'spectra', 'current_problem.clj')
    
    with open(problem_path, 'w') as f:
        f.write(problem_content)
        
    # 2. Run Spectra
    try:
        # Run Spectra
        cmd = ['java', '-jar', SPECTRA_JAR, problem_path]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..'))
        
        if result.returncode != 0:
            print("Spectra Error:", result.stderr)
            return jsonify({'error': 'Spectra failed', 'details': result.stderr}), 500
            
        # 3. Parse Output
        output = result.stdout
        print("Spectra Output:", output)
        
        # Expected output format: [(PlaceWall  c_m2_2)  ]
        # Regex to match PlaceWall with optional spaces and case insensitivity
        match = re.search(r'PlaceWall\s*\(?[Cc]_([m\d]+)_([m\d]+)\)?', output, re.IGNORECASE)
        if match:
            q_str, r_str = match.groups()
            q = int(q_str.replace('m', '-'))
            r = int(r_str.replace('m', '-'))
            return jsonify({'move': {'q': q, 'r': r}})
        else:
            return jsonify({'error': 'No move found in output'}), 500

    except Exception as e:
        print("Server Error:", e)
        return jsonify({'error': str(e)}), 500

def generate_spectra_problem(pig_pos, walls, phase):
    radius = 5 # Updated to Radius 5
    cells = []
    adjacencies = []
    escapes = []

    # Generate cells
    for q in range(-radius, radius + 1):
        for r in range(-radius, radius + 1):
            if -radius <= q + r <= radius:
                cells.append((q, r))
                if abs(q) == radius or abs(r) == radius or abs(q + r) == radius:
                    escapes.append((q, r))

    # Generate adjacencies
    directions = [
        (1, 0), (1, -1), (0, -1),
        (-1, 0), (-1, 1), (0, 1)
    ]

    for q, r in cells:
        for dq, dr in directions:
            nq, nr = q + dq, r + dr
            if (nq, nr) in cells:
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
