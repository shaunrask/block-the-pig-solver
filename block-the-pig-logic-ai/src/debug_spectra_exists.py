import os
import sys
import subprocess
import re

# Add src to path
sys.path.append(os.path.dirname(__file__))

from app import generate_spectra_problem, SPECTRA_JAR

def test_exists_goal():
    # Manual generation with 'not exists' goal
    content = """{:name "Exists Goal Test"
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
    (not (exists (n) (and (Adjacent C_0_0 n) (Free n))))
 ]
}"""
    
    problem_path = os.path.join(os.path.dirname(__file__), '..', 'spectra', 'debug_exists.clj')
    with open(problem_path, 'w') as f:
        f.write(content)
        
    print(f"Problem written to {problem_path}")
    
    print("Running Spectra...")
    cmd = ['java', '-jar', SPECTRA_JAR, problem_path]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..'))
    
    print("Return Code:", result.returncode)
    print("Stdout:", result.stdout)
    print("Stderr:", result.stderr)

if __name__ == "__main__":
    test_exists_goal()
