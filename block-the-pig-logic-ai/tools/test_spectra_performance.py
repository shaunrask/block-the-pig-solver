import os
import time
import subprocess
import concurrent.futures

SPECTRA_JAR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Spectra.jar'))

def generate_spectra_problem(radius, pig_pos, walls, phase, target_wall=None):
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
    
    # PigMove
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

def run_test(radius, timeout=60):
    print(f"\n--- Testing Radius {radius} ---")
    
    # Setup a simple problem: Pig at center, no walls yet
    pig_pos = {'q': 0, 'r': 0}
    walls = [] # Empty board
    phase = 'MAIN'
    
    # Goal: Trapped (this forces the planner to find a full trapping strategy)
    # The default app logic only validates a SINGLE move.
    # To stress test "loading forever", we should ask it to Solve the game (Trapped).
    problem_content = generate_spectra_problem(radius, pig_pos, walls, phase, target_wall=None)
    
    problem_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'spectra', f'perf_test_r{radius}.clj'))
    
    with open(problem_path, 'w') as f:
        f.write(problem_content)
        
    print(f"Problem generated at {problem_path}")
    print(f"Starting Spectra (Timeout: {timeout}s)...")
    
    start_time = time.time()
    
    try:
        cmd = ['java', '-jar', SPECTRA_JAR, problem_path]
        # Using subprocess with timeout
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..'), timeout=timeout)
        
        duration = time.time() - start_time
        print(f"Completed in {duration:.2f} seconds")
        print(f"Return Code: {result.returncode}")
        
        if result.returncode != 0:
            print("Stderr:", result.stderr)
            
        print("Output Snippet:", result.stdout[:200] + "...")
        
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT! Spectra failed to finish within {timeout} seconds.")
    except Exception as e:
        print(f"Error running Spectra: {e}")

if __name__ == "__main__":
    # Test Radius 4 first (baseline)
    run_test(radius=4, timeout=30)
    
    # Test Radius 5 (larger)
    run_test(radius=5, timeout=60)
