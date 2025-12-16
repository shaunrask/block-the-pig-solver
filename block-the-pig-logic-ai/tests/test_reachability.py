"""Test Reachability Logic generation."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from app import generate_spectra_problem

def check_logic(name, problem, expected_features):
    print(f"\nTEST: {name}")
    if not problem:
        print("FAIL: No problem generated")
        return False
        
    all_pass = True
    for feature in expected_features:
        if feature in problem:
            print(f"  ✓ Found: {feature.strip()[:40]}...")
        else:
            print(f"  ✗ MISSING: {feature}")
            all_pass = False
            
    # Check if goal is Reachability based
    if "(not (exists (?e) (and (Escape ?e) (Reachable ?e))))" in problem:
        print("  ✓ Goal is correct (No Reachable Escape)")
    else:
        # Check if fallback
        if "Block the Pig - Fallback" in problem:
            print("  ! Using Fallback (Deterministic)")
        else:
            print("  ✗ Goal format incorrect")
            all_pass = False
            
    return all_pass

print("="*60)
print("REACHABILITY VERIFICATION")
print("="*60)

# 1. Pig in center (Complex graph)
pig = {'q': 2, 'r': 5}
walls = []
prob1 = generate_spectra_problem(pig, walls)
check_logic("Pig Center (Should use Reachability)", prob1, [
    "(forall (?c) (if (PigAt ?c) (Reachable ?c)))",
    "(Reachable ?c1) (Adjacent ?c1 ?c2) (Free ?c2)",
    "(Escape C_",
    "(PigAt C_2_5)"
])

# 2. Pig Trapped (Fallback)
walls_trap = [{'q': n[0], 'r': n[1]} for n in [(1,5), (2,4), (3,5), (2,6), (1,4), (3,4)]] # Roughly surrounding
prob2 = generate_spectra_problem(pig, walls_trap)
# Note: If completely trapped with NO escape path, generate_spectra_problem returns None or fallback

if prob2 and "Fallback" in prob2:
    print("\nTEST: Trapped Pig -> Fallback generated correctly")
elif prob2 is None:
    print("\nTEST: Trapped Pig -> None (No moves possible), also correct")
else:
    print(f"\nTEST: Trapped Pig -> Unexpected output: {prob2[:100]}")

print("\n" + "="*60)
