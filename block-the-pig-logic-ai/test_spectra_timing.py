"""
Quick test to verify Spectra JAR is used and timing is acceptable.
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from app import find_optimal_block

def test_move():
    # Standard game state
    pig_pos = {'q': 2, 'r': 5}
    walls = [{'q': 1, 'r': 4}, {'q': 3, 'r': 4}]  # Some initial walls
    
    print("=" * 60)
    print("TESTING SPECTRA INTEGRATION")
    print("=" * 60)
    
    start = time.time()
    move, thoughts = find_optimal_block(pig_pos, walls)
    elapsed = time.time() - start
    
    print(f"\nMove selected: {move}")
    print(f"Time taken: {elapsed:.2f}s")
    print(f"\nFull Thoughts Log:")
    for t in thoughts:
        print(f"  {t}")
    
    # Check if Spectra was used
    spectra_used = any("Spectra" in t for t in thoughts)
    
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    print(f"Spectra mentioned in output: {'YES' if spectra_used else 'NO'}")
    print(f"Time acceptable (<5s): {'YES' if elapsed < 5 else 'NO'}")
    
    if spectra_used:
        print("\n*** SPECTRA IS BEING USED ***")

if __name__ == "__main__":
    test_move()
