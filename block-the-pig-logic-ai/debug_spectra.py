import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from app import find_optimal_block
import time

pig_pos = {'q': 2, 'r': 5}
walls = [{'q': 1, 'r': 4}]

print("Running AI with Spectra verification...")
start = time.time()
move, thoughts = find_optimal_block(pig_pos, walls)
elapsed = time.time() - start

print(f"\n{'='*60}")
print(f"MOVE: {move}")
print(f"TIME: {elapsed:.1f}s")
print(f"{'='*60}")
print("THOUGHTS:")
for t in thoughts:
    print(f"  {t}")
print(f"{'='*60}")

# Check for Spectra proof
has_spectra_proof = any("PlaceWall" in str(t) or "VERIFIED" in str(t) for t in thoughts)
print(f"\nSPECTRA ACTUALLY PRODUCED OUTPUT: {'YES!' if has_spectra_proof else 'No'}")
