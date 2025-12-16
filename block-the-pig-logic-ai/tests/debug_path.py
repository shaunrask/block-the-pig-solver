from collections import deque

def get_neighbors(q, r):
    if r % 2 == 0:
        return [(q+1, r), (q, r-1), (q-1, r-1), (q-1, r), (q-1, r+1), (q, r+1)]
    else:
        return [(q+1, r), (q+1, r-1), (q, r-1), (q-1, r), (q, r+1), (q+1, r+1)]

def is_valid(q, r):
    return 0 <= q <= 4 and 0 <= r <= 10

def is_escape(q, r):
    if not is_valid(q, r): return False
    return q == 0 or q == 4 or r == 0 or r == 10

def bfs_escape_path(start_q, start_r, blocked_cells):
    if is_escape(start_q, start_r):
        return 0, []
    queue = deque([(start_q, start_r, [])])
    visited = {(start_q, start_r)}
    while queue:
        q, r, path = queue.popleft()
        for nq, nr in get_neighbors(q, r):
            if is_valid(nq, nr) and (nq, nr) not in visited and (nq, nr) not in blocked_cells:
                new_path = path + [(nq, nr)]
                if is_escape(nq, nr):
                    return len(new_path), new_path
                visited.add((nq, nr))
                queue.append((nq, nr, new_path))
    return float('inf'), []

# Test: pig at (2,5), no walls
dist, path = bfs_escape_path(2, 5, set())
print(f"Pig at (2,5): distance={dist}")
print(f"Path: {path}")
print(f"First cell to block: {path[0] if path else None}")

# After blocking first cell on path
if path:
    block = path[0]
    new_dist, new_path = bfs_escape_path(2, 5, {block})
    print(f"\nAfter blocking {block}:")
    print(f"New distance: {new_dist}, new path: {new_path}")
    print(f"Does new_dist > old_dist? {new_dist} > {dist} = {new_dist > dist}")

# Simulate what the algorithm does
print("\n=== Simulating Algorithm ===")
pq, pr = 2, 5
wall_set = set()

current_dist, current_path = bfs_escape_path(pq, pr, wall_set)
print(f"Current path: {current_path}")

if current_path:
    block_target = current_path[0]
    print(f"Block target: {block_target}")
    test_walls = wall_set | {block_target}
    new_dist, _ = bfs_escape_path(pq, pr, test_walls)
    print(f"After blocking {block_target}: new_dist={new_dist}, old_dist={current_dist}")
    print(f"Condition (new_dist > current_dist): {new_dist > current_dist}")
    
    if new_dist > current_dist:
        print("Algorithm WOULD block this cell!")
    else:
        print("Algorithm SKIPS to minimax because blocking doesn't improve distance")
        
        # What does minimax choose?
        neighbors = [(nq, nr) for nq, nr in get_neighbors(pq, pr) 
                     if is_valid(nq, nr) and (nq, nr) not in wall_set]
        print(f"Neighbors: {neighbors}")
        
        candidates = set(neighbors)
        for nq, nr in neighbors:
            for nnq, nnr in get_neighbors(nq, nr):
                if is_valid(nnq, nnr) and (nnq, nnr) not in wall_set and (nnq, nnr) != (pq, pr):
                    candidates.add((nnq, nnr))
        
        print(f"All candidates ({len(candidates)}): {sorted(candidates)}")
        
        best_cell = None
        best_score = float('-inf')
        
        for cell in candidates:
            test_walls = wall_set | {cell}
            new_dist, new_path = bfs_escape_path(pq, pr, test_walls)
            
            if new_path:
                pig_next = new_path[0]
                final_dist, _ = bfs_escape_path(pig_next[0], pig_next[1], test_walls)
                if is_escape(pig_next[0], pig_next[1]):
                    score = -100
                elif final_dist == float('inf'):
                    score = 100
                else:
                    score = final_dist
            else:
                score = new_dist
            
            print(f"  Cell {cell}: score={score}")
            
            if score > best_score:
                best_score = score
                best_cell = cell
        
        print(f"\nMinimax chooses: {best_cell} with score {best_score}")
