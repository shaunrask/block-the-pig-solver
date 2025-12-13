import os
import sys
import subprocess
import re

# Add src to path
sys.path.append(os.path.dirname(__file__))

from app import generate_spectra_problem, SPECTRA_JAR

def generate_simple_problem():
    # Manual generation to ensure simple goal
    # Pig at 0,0
    # Goal: HasWall C_0_1
    
    content = """{:name "Simple Wall Test"
 :background [
    (Adjacent C_0_0 C_0_1)
    (Adjacent C_0_1 C_0_0)
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
 ]
 :goal [
    (HasWall C_0_1)
 ]
}"""
    return content

def test_simple_goal():
    print("Generating simple problem...")
    problem_content = generate_simple_problem()
    
    problem_path = os.path.join(os.path.dirname(__file__), '..', 'spectra', 'debug_simple.clj')
    with open(problem_path, 'w') as f:
        f.write(problem_content)
        
    print(f"Problem written to {problem_path}")
    
    print("Running Spectra...")
    cmd = ['java', '-jar', SPECTRA_JAR, problem_path]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..'))
    
    print("Return Code:", result.returncode)
    print("Stdout:", result.stdout)
    print("Stderr:", result.stderr)

if __name__ == "__main__":
    test_simple_goal()
