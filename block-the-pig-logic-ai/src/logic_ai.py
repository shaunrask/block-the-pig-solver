import collections

# Hex Grid Utils (copied/adapted from game.js logic)
# Axial coordinates (q, r)

def get_neighbors(q, r):
    # odd-r offset neighbors logic from game.js
    # But wait, game.js uses "odd-r" (horizontal layout)?
    # Let's check game.js again.
    # "Odd-row neighbors (pointy-top, redblobgames 'odd-r' horizontal layout)"
    # dirsEven = [[1,0], [0,-1], [-1,-1], [-1,0], [-1,1], [0,1]]
    # dirsOdd  = [[1,0], [1,-1], [0,-1], [-1,0], [0,1], [1,1]]
    
    is_odd = (r % 2 == 1)
    if is_odd:
        directions = [
            (1, 0), (1, -1), (0, -1),
            (-1, 0), (0, 1), (1, 1)
        ]
    else:
        directions = [
            (1, 0), (0, -1), (-1, -1),
            (-1, 0), (-1, 1), (0, 1)
        ]
    
    return [(q + dq, r + dr) for dq, dr in directions]

def is_valid(q, r):
    return 0 <= q <= 4 and 0 <= r <= 10

def is_escape(q, r):
    return q == 0 or q == 4 or r == 0 or r == 10

def bfs_escape(start_node, walls):
    # Returns path to escape or None
    queue = collections.deque([[start_node]])
    visited = {start_node}
    
    while queue:
        path = queue.popleft()
        curr = path[-1]
        
        if is_escape(curr[0], curr[1]):
            return path
        
        for n in get_neighbors(curr[0], curr[1]):
            if is_valid(n[0], n[1]) and n not in walls and n not in visited:
                visited.add(n)
                new_path = list(path)
                new_path.append(n)
                queue.append(new_path)
                
    return None

def find_best_move(pig_pos, walls):
    # pig_pos: {'q': int, 'r': int}
    # walls: list of {'q': int, 'r': int}
    
    pq, pr = pig_pos['q'], pig_pos['r']
    wall_set = set((w['q'], w['r']) for w in walls)
    
    thoughts = []
    thoughts.append(f"Analyzing board state...")
    thoughts.append(f"Pig position: ({pq}, {pr})")
    thoughts.append(f"Wall count: {len(walls)}")
    
    # 1. Check if pig can escape
    path = bfs_escape((pq, pr), wall_set)
    
    if not path:
        thoughts.append("Pig is already trapped! No escape path found.")
        # Just place a random wall to finish
        # Find a free spot
        for q in range(5):
            for r in range(11):
                if (q, r) not in wall_set and (q, r) != (pq, pr):
                    return {'q': q, 'r': r}, thoughts
        return None, thoughts

    thoughts.append(f"Found shortest escape path: {len(path)-1} steps.")
    thoughts.append(f"Path: {path}")
    
    # 2. Strategy: Block the immediate next step or the most critical bottleneck?
    # Simple strategy: Block the first step of the shortest path (if valid)
    # But we can't block the pig's current position.
    # The path includes start node. path[0] is pig. path[1] is next step.
    
    if len(path) > 1:
        target = path[1]
        thoughts.append(f"Identified critical gap at ({target[0]}, {target[1]}).")
        thoughts.append(f"Evaluating wall placement at ({target[0]}, {target[1]})...")
        
        # Verify if this actually helps?
        # (For now, just return this move)
        thoughts.append(f"Decision: Block ({target[0]}, {target[1]}) to cut off escape route.")
        return {'q': target[0], 'r': target[1]}, thoughts
    else:
        # Pig is AT escape? Should be game over.
        thoughts.append("Pig is at escape boundary!")
        return None, thoughts

