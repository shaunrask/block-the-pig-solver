import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from app import find_optimal_block
import time

pig_pos = {'q': 2, 'r': 5}
walls = [{'q': 1, 'r': 4}]

print("=" * 70)
print("TESTING SHADOWPROVER + SPECTRA INTEGRATION")
print("=" * 70)

start = time.time()
move, thoughts = find_optimal_block(pig_pos, walls)
elapsed = time.time() - start

print(f"\nMOVE: {move}")
print(f"TIME: {elapsed:.1f}s")
print(f"\nTHOUGHTS:")
for t in thoughts:
    print(f"  {t}")

print(f"\n{'=' * 70}")
print("VERIFICATION:")
print(f"  ShadowProver used: {'YES' if any('ShadowProver' in str(t) for t in thoughts) else 'NO'}")
print(f"  Spectra used: {'YES' if any('Spectra' in str(t) for t in thoughts) else 'NO'}")
print(f"  Plan produced: {'YES' if any('PlaceWall' in str(t) or 'Plan' in str(t) for t in thoughts) else 'NO'}")
print("=" * 70)
