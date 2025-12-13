import os
import sys
import subprocess
import re

# Add src to path
sys.path.append(os.path.dirname(__file__))

from app import generate_spectra_problem, SPECTRA_JAR

def test_simple_case():
    # Pig at 0,0
    pig_pos = {'q': 0, 'r': 0}
    
    # Walls surrounding 0,0 except one spot
    # Neighbors of 0,0: (1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)
    # Let's block all except (0,1)
    walls = [
        {'q': 1, 'r': 0},
        {'q': 1, 'r': -1},
        {'q': 0, 'r': -1},
        {'q': -1, 'r': 0},
        {'q': -1, 'r': 1}
    ]
    
    phase = 'MAIN'
    
    # Manual generation with explicit goal
    content = """{:name "Explicit Goal Test"
 :background [
    (Adjacent C_0_0 C_0_1)
    (Adjacent C_0_1 C_0_0)
    (Adjacent C_0_0 C_1_0)
    (Adjacent C_1_0 C_0_0)
    (Adjacent C_0_0 C_1_m1)
    (Adjacent C_1_m1 C_0_0)
    (Adjacent C_0_0 C_0_m1)
    (Adjacent C_0_m1 C_0_0)
    (Adjacent C_0_0 C_m1_0)
    (Adjacent C_m1_0 C_0_0)
    (Adjacent C_0_0 C_m1_1)
    (Adjacent C_m1_1 C_0_0)
    
    (HasWall C_1_0)
    (HasWall C_1_m1)
    (HasWall C_0_m1)
    (HasWall C_m1_0)
    (HasWall C_m1_1)
    
    (Free C_0_1)
    (OccupiedByPig C_0_0)
    
    (forall (c) (if (OccupiedByPig c) (not (HasWall c))))
 ]
 :actions [
    (define-action PlaceWall [?c] {
        :preconditions [(Free ?c)]
        :additions [(HasWall ?c)]
        :deletions [(Free ?c)]
    })
 ]
 :start [
    (OccupiedByPig C_0_0)
    (Free C_0_1)
    (HasWall C_1_0)
    (HasWall C_1_m1)
    (HasWall C_0_m1)
    (HasWall C_m1_0)
    (HasWall C_m1_1)
 ]
 :goal [
    (forall (c1) (if (OccupiedByPig c1) (forall (c2) (if (Adjacent c1 c2) (HasWall c2)))))
 ]
}"""
    
    problem_path = os.path.join(os.path.dirname(__file__), '..', 'spectra', 'debug_explicit.clj')
    with open(problem_path, 'w') as f:
        f.write(content)
        
    print(f"Problem written to {problem_path}")
    
    print("Running Spectra...")
    cmd = ['java', '-jar', SPECTRA_JAR, problem_path]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..'))
    
    print("Return Code:", result.returncode)
    print("Stdout:", result.stdout)
    print("Stderr:", result.stderr)
    
    match = re.search(r'PlaceWall\s*\(?[Cc]_([m\d]+)_([m\d]+)\)?', result.stdout, re.IGNORECASE)
    if match:
        print("Found Move:", match.groups())
    else:
        print("No move found.")

if __name__ == "__main__":
    test_simple_case()
