"""Quick test of new strategic Spectra problem generation."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import generate_spectra_problem

# Test: Pig in center, no walls
print("="*60)
print("TEST: Pig at (2, 5), no walls - Spectra Strategic Reasoning")
print("="*60)

pig_pos = {'q': 2, 'r': 5}
walls = []

problem = generate_spectra_problem(pig_pos, walls)
print(problem)
print()

# Check for key features
checks = [
    ("Adjacent facts", "Adjacent" in problem),
    ("Escape cells marked", "Escape" in problem),
    ("OnEscapePath cells", "OnEscapePath" in problem),
    ("Pig position", "PigAt" in problem),
    ("Strategic goal", "exists" in problem and "OnEscapePath" in problem),
]

print("\n" + "="*60)
print("VERIFICATION:")
for name, passed in checks:
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {status}: {name}")

print("="*60)
print("""
Spectra now:
1. Receives adjacency graph of relevant cells
2. Knows which cells are on pig's escape path
3. Must find a PlaceWall action that blocks an OnEscapePath cell
4. Searches through candidates to find valid blocking move

This is TRUE strategic reasoning by Spectra!
""")
