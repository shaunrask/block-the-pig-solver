import sys
import os
import subprocess
import time

# Add src to path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from app import generate_spectra_problem, SPECTRA_JAR

def test_fix():
    print("Testing 5x11 Grid Generation...")
    
    # Simulate a mid-game state
    pig_pos = {'q': 2, 'r': 5} # Center
    walls = [{'q': 0, 'r': 0}, {'q': 1, 'r': 1}, {'q': 4, 'r': 10}]
    phase = 'MAIN'
    
    # Generate problem with NO target wall (Solve for Trapped)
    # This is the hardest case.
    content = generate_spectra_problem(pig_pos, walls, phase, target_wall=None)
    
    problem_path = os.path.abspath(os.path.join('spectra', 'verify_fix.clj'))
    with open(problem_path, 'w') as f:
        f.write(content)
        
    print(f"Problem written to {problem_path}")
    print("Running Spectra...")
    
    start = time.time()
    try:
        cmd = ['java', '-jar', SPECTRA_JAR, problem_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=os.path.dirname(__file__))
        
        dur = time.time() - start
        print(f"Finished in {dur:.2f}s")
        if result.returncode != 0:
            print("Stderr:", result.stderr)
        else:
            print("Spectra Output Snippet:", result.stdout[:200])
            
            if "PlaceWall" in result.stdout:
                print("SUCCESS: Plan found!")
            else:
                print("WARNING: No plan found (might be valid if pig can escape optimally?)")
                # If pig can escape, Trapped is impossible.
                # But on an almost empty 5x11 board, pig CAN escape.
                # So Spectra might say "No Plan" (i.e. cannot force trap).
                # This is Correct behavior.
                # But it should return FAST.
                
    except subprocess.TimeoutExpired:
        print("TIMEOUT! Fix did not solve performance issue.")

if __name__ == "__main__":
    test_fix()
