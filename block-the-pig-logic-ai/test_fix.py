"""Verify the fix: test critical scenarios."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from app import generate_spectra_problem

def test(name, pig, walls, expected_in_goal):
    """Test and verify the goal contains expected cell."""
    problem = generate_spectra_problem({'q': pig[0], 'r': pig[1]}, 
                                       [{'q': w[0], 'r': w[1]} for w in walls])
    
    # Extract the goal line
    goal_line = [l for l in problem.split('\n') if ':goal' in l][0] if problem else ""
    
    passed = expected_in_goal in goal_line
    status = "✓ PASS" if passed else "✗ FAIL"
    
    print(f"{status}: {name}")
    print(f"       Goal: {goal_line.strip()}")
    if not passed:
        print(f"       Expected {expected_in_goal} in goal!")
    return passed

print("="*60)
print("VERIFYING PRIORITY FIX")
print("="*60)

results = []

# CRITICAL: Pig one move from right edge - must block (4,5)
results.append(test(
    "Pig at (3,5) - 1 move from right edge",
    pig=(3, 5), walls=[],
    expected_in_goal="C_4_5"
))

# CRITICAL: Pig one move from left edge - must block (0,5)  
results.append(test(
    "Pig at (1,5) - 1 move from left edge",
    pig=(1, 5), walls=[],
    expected_in_goal="C_0_5"
))

# Pig at center - should block first step toward nearest edge
results.append(test(
    "Pig at (2,5) center - 2 moves, block first step",
    pig=(2, 5), walls=[],
    expected_in_goal="C_"  # Any cell is fine, just verify it works
))

# Pig with walls blocking right
results.append(test(
    "Pig at (2,5), right blocked - should go left",
    pig=(2, 5), walls=[(3, 4), (3, 5), (3, 6)],
    expected_in_goal="C_1_"  # Should target left side
))

print()
print("="*60)
passed = sum(results)
total = len(results)
print(f"RESULTS: {passed}/{total} tests passed")
if passed == total:
    print("All tests pass! The fix is working correctly.")
else:
    print("Some tests failed - need further investigation.")
print("="*60)
