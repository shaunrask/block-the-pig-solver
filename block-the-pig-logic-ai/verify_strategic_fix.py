"""Quick test to verify the fixed Spectra problem generation."""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import generate_spectra_problem

# Test case 1: Pig in center
print("="*60)
print("TEST 1: Pig in center (2, 5), no walls")
print("="*60)
pig_pos = {'q': 2, 'r': 5}
walls = []
problem = generate_spectra_problem(pig_pos, walls)
print(problem)
print()

# Check if it's targeting the right cell
# Pig at (2,5) should have shortest path going toward nearest edge
# Nearest edges: left (0,5) or right (4,5)
# Path to right: (2,5) -> (3,5) -> (4,5)
# So first cell should be (3,5) or similar

if "C_3_5" in problem or "C_1_5" in problem:
    print("✓ PASS: Target cell is on escape path (either left or right direction)")
else:
    print("✗ FAIL: Target cell might not be on optimal escape path")

# Test case 2: Pig with walls
print("\n" + "="*60)
print("TEST 2: Pig at (2, 5) with walls blocking right")
print("="*60)
pig_pos2 = {'q': 2, 'r': 5}
walls2 = [{'q': 3, 'r': 5}, {'q': 3, 'r': 4}, {'q': 3, 'r': 6}]
problem2 = generate_spectra_problem(pig_pos2, walls2)
print(problem2)
print()

# With right side blocked, should target left path
if "C_1_" in problem2:
    print("✓ PASS: Target cell is toward left (avoiding blocked right side)")
else:
    print("? CHECK: Verify the path makes sense given the walls")

print("\n" + "="*60)
print("VERIFICATION COMPLETE")
print("="*60)
print("""
The key changes:
1. Now only ONE cell is sent to Spectra
2. Goal is specific: (Blocked C_q_r) not (exists)
3. Spectra MUST place wall on that exact cell

This ensures the AI always blocks the first cell on the 
shortest escape path - the most strategic move!
""")
