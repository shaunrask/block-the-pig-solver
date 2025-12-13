import os
import time
import subprocess
import sys

SPECTRA_JAR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tools', 'Spectra.jar'))

def generate_spectra_problem(radius):
    # Reduced version for speed of writing script
    cells = []
    # Generate cells
    for q in range(-radius, radius + 1):
        for r in range(-radius, radius + 1):
            if -radius <= q + r <= radius:
                cells.append((q, r))

    # Adjacencies
    adjacencies = []
    directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
    for q, r in cells:
        for dq, dr in directions:
            nq, nr = q + dq, r + dr
            if (nq, nr) in cells:
                adjacencies.append(((q, r), (nq, nr)))

    background = []
    for (q1, r1), (q2, r2) in adjacencies:
        n1 = f"C_{q1}_{r1}".replace("-", "m")
        n2 = f"C_{q2}_{r2}".replace("-", "m")
        background.append(f"(Adjacent {n1} {n2})")
    
    # Just needed axioms
    background.append("(forall (c) (if (OccupiedByPig c) (not (HasWall c))))")
    background.append("(iff Trapped (forall (c1) (if (OccupiedByPig c1) (forall (c2) (if (Adjacent c1 c2) (HasWall c2))))))")

    actions = []
    actions.append("""
        (define-action PlaceWall [?c] {
            :preconditions [(Free ?c)]
            :additions [(HasWall ?c)]
            :deletions [(Free ?c)]
        })
    """)
    actions.append("""
        (define-action PigMove [?a ?b] {
            :preconditions [(OccupiedByPig ?a) (Adjacent ?a ?b) (Free ?b)]
            :additions [(OccupiedByPig ?b) (Free ?a)]
            :deletions [(OccupiedByPig ?a) (Free ?b)]
        })
    """)

    start = []
    pig_pos = (0,0)
    p_name = f"C_{0}_{0}"
    start.append(f"(OccupiedByPig {p_name})")
    for c in cells:
        if c != pig_pos:
            name = f"C_{c[0]}_{c[1]}".replace("-", "m")
            start.append(f"(Free {name})")

    goal = ["(Trapped)"]

    output = []
    output.append("{:name \"PerfTest\"")
    output.append(" :background " + str(background).replace("'", ""))
    output.append(" :actions [\n" + "\n".join(actions) + "\n]")
    output.append(" :start " + str(start).replace("'", ""))
    output.append(" :goal " + str(goal).replace("'", ""))
    output.append("}")
    return "".join(output)

# Actually use the original generator logic to be safe about formatting (Clojure-like)
# Re-using the logic from previous file but ensuring correct formatting manually here is risky.
# Let's import the tool.
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
# Oh wait, the tool is a script, not a module structure I can easily import if not in path.
# I'll just load the file content I wrote earlier.

from tools.test_spectra_performance import generate_spectra_problem
# This import works because I am in block-the-pig-logic-ai and tools is a subdir.

def test_r5():
    radius = 5
    print(f"Generating R{radius} problem...")
    content = generate_spectra_problem(radius, {'q':0,'r':0}, [], 'MAIN', None)
    
    path = os.path.abspath(os.path.join('spectra', 'perf_test_r5_v2.clj'))
    with open(path, 'w') as f:
        f.write(content)
        
    print(f"Running Spectra on {path}...")
    start = time.time()
    try:
        # 120s timeout
        proc = subprocess.run(['java', '-jar', SPECTRA_JAR, path], capture_output=True, text=True, timeout=120)
        dur = time.time() - start
        print(f"Finished in {dur:.2f}s")
        print("Stdout:", proc.stdout[:500])
        print("Stderr:", proc.stderr)
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT after {time.time()-start:.2f}s")

if __name__ == "__main__":
    test_r5()
