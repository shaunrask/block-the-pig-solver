"""Verify Focused Reachability (Tube Logic)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from app import generate_spectra_problem

def test_focused_scope():
    """Test if Spectra problem ignores distant escapes."""
    
    # Scene: Pig at (2,5).
    # Path 1 (Short): Right to (4,5). Steps: (3,5), (4,5).
    # Path 2 (Long):  Up to (2,0). Steps: (2,4), (2,3), (2,2), (2,1), (2,0).
    
    # We place walls to ensure these look like separate paths?
    # Actually, empty board is fine. Shortest path is to closest edge.
    # (2,5) -> (3,5) -> (4,5) is dist 2.
    # (2,5) -> (1,5) -> (0,5) is dist 2.
    # (2,5) -> (2,0) is dist 5.
    
    # Let's block the Left side so Right is clearly shortest.
    # Block (1,5), (1,4), (1,6).
    walls = [
        {'q': 1, 'r': 5}, {'q': 1, 'r': 4}, {'q': 1, 'r': 6}
    ]
    pig = {'q': 2, 'r': 5}
    
    print("\nTEST: Pig (2,5) with Left blocked. Shortest path is Right to (4,5).")
    problem = generate_spectra_problem(pig, walls)
    
    if not problem:
        print("FAIL: No problem generated")
        return

    # 1. Check Primary Escape is included
    if "(Escape C_4_5)" in problem or "(Escape C_3_5)" in problem: # (3,5) is not escape, (4,5) is
         print("  ✓ Primary Escape (Right) is included")
    else:
         print("  ✗ Primary Escape (Right) MISSING!")

    # 2. Check Distant Escape is EXCLUDED
    # (2,0) is far away (Top edge).
    if "C_2_0" in problem:
        print("  ✗ Distant Escape (C_2_0) is INCLUDED (Scope too broad?)")
    else:
        print("  ✓ Distant Escape (C_2_0) is correctly EXCLUDED")

    # 3. Check Logic
    if "(not (exists (?e) (and (Escape ?e) (Reachable ?e))))" in problem:
        print("  ✓ Correct Reachability Goal")
    else:
        print("  ✗ Incorrect Goal")

if __name__ == "__main__":
    test_focused_scope()
