import sys
import os
import subprocess
import re

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app import generate_spectra_problem
# define SPECTRA_JAR manually since we might not be importing it correctly from app if CWD is different
SPECTRA_JAR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tools', 'Spectra.jar'))

def test_spectra_empty_output():
    # Case from user
    pig_pos = {'q': 2, 'r': 5}
    target = {'q': 3, 'r': 4}
    
    # We don't know the exact walls, but let's assume some walls exist but NOT at (3,4)
    walls = [
        {'q': 0, 'r': 0},
        {'q': 1, 'r': 1}, 
        # Add some distant walls
    ]
    
    phase = 'MAIN'
    
    print(f"Generating problem with Target: {target}")
    content = generate_spectra_problem(pig_pos, walls, phase, target_wall=target)
    
    problem_path = os.path.join(os.path.dirname(__file__), 'spectra', 'repro_test.clj')
    os.makedirs(os.path.join(os.path.dirname(__file__), 'spectra'), exist_ok=True)
    
    with open(problem_path, 'w') as f:
        f.write(content)
        
    print(f"Problem written to {problem_path}")
    print("Running Spectra...")
    
    cmd = ['java', '-jar', SPECTRA_JAR, problem_path]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))
    
    print("Spectra Output raw:")
    print(result.stdout)
    
    match = re.search(r'PlaceWall\s*\(?[Cc]_([m\d]+)_([m\d]+)\)?', result.stdout, re.IGNORECASE)
    if match:
        print("Found Move:", match.groups())
    else:
        print("No move found in output (Empty Plan or Failure)")

if __name__ == "__main__":
    test_spectra_empty_output()
