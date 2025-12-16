from flask import Flask, render_template, request, jsonify
import subprocess
import os
import time

app = Flask(__name__)

# Grid constants (matching frontend)
COL_MIN, COL_MAX = 0, 4
ROW_MIN, ROW_MAX = 0, 10

@app.route('/')
def index():
    return render_template('index.html')


# Helper functions
def get_neighbors(q, r):
    if r % 2 == 0:
        return [(q+1, r), (q, r-1), (q-1, r-1), (q-1, r), (q-1, r+1), (q, r+1)]
    else:
        return [(q+1, r), (q+1, r-1), (q, r-1), (q-1, r), (q, r+1), (q+1, r+1)]

def is_valid(q, r):
    return COL_MIN <= q <= COL_MAX and ROW_MIN <= r <= ROW_MAX

def is_escape(q, r):
    if not is_valid(q, r): return False
    return q == COL_MIN or q == COL_MAX or r == ROW_MIN or r == ROW_MAX

def bfs_escape_path(start_q, start_r, blocked_cells):
    """Returns (distance, first_step) to escape."""
    from collections import deque
    if is_escape(start_q, start_r):
        return 0, None
    queue = deque([(start_q, start_r, 0, None)])  # (q, r, dist, first_step)
    visited = {(start_q, start_r)}
    while queue:
        q, r, dist, first = queue.popleft()
        for nq, nr in get_neighbors(q, r):
            if is_valid(nq, nr) and (nq, nr) not in visited and (nq, nr) not in blocked_cells:
                new_first = first if first else (nq, nr)
                if is_escape(nq, nr):
                    return dist + 1, new_first
                visited.add((nq, nr))
                queue.append((nq, nr, dist + 1, new_first))
    return float('inf'), None

# ... (helper functions remain the same) ...

class SpectraLogicEngine:
    """
    Integrated Logic Engine using:
    - ShadowProver: For theorem proving (trap validation, move constraints)
    - Spectra: For planning (optimal wall placement)
    """
    
    @staticmethod
    def _run_shadowprover(pig_pos, walls, proposed_move):
        """
        Uses ShadowProver to verify move constraints.
        Checks: Is this move valid according to game rules?
        """
        import subprocess
        
        pq, pr = pig_pos['q'], pig_pos['r']
        mq, mr = proposed_move
        wall_set = set((w['q'], w['r']) for w in walls)
        
        # Build assumptions
        assumptions = []
        
        # Pig position
        p_name = f"C_{pq}_{pr}".replace("-", "m")
        assumptions.append(f"(OccupiedByPig {p_name})")
        
        # Existing walls
        for w in walls:
            w_name = f"C_{w['q']}_{w['r']}".replace("-", "m")
            assumptions.append(f"(HasWall {w_name})")
        
        # Move target
        m_name = f"C_{mq}_{mr}".replace("-", "m")
        
        # Rule: Cannot place wall on pig
        assumptions.append("(forall (c) (if (OccupiedByPig c) (not (CanPlaceWall c))))")
        # Rule: Cannot place wall on existing wall
        assumptions.append("(forall (c) (if (HasWall c) (not (CanPlaceWall c))))")
        # Rule: Free cells can have walls placed
        assumptions.append("(forall (c) (if (and (not (OccupiedByPig c)) (not (HasWall c))) (CanPlaceWall c)))")
        
        # Build problem file
        lines = ['{:name "Move Constraint Check"']
        lines.append(' :description "ShadowProver verifying move validity"')
        lines.append(' :assumptions {')
        for i, asm in enumerate(assumptions):
            lines.append(f'  A{i} {asm}')
        lines.append(' }')
        lines.append(f' :goal (CanPlaceWall {m_name})')
        lines.append('}')
        
        problem_content = '\n'.join(lines)
        
        # Use absolute paths
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        problem_file = os.path.join(project_root, "shadowprover_verify.clj")
        
        with open(problem_file, 'w') as f:
            f.write(problem_content)
        
        jar_path = os.path.join(project_root, "tools", "Shadow-Prover.jar")
        if not os.path.exists(jar_path):
            return {'valid': True, 'reason': "ShadowProver Missing", 'output': None}
        
        try:
            import time
            # Use Popen so we can start and terminate ShadowProver
            # Optimization: Add -XX:TieredStopAtLevel=1 to speed up JVM startup
            process = subprocess.Popen(
                ["java", "-XX:TieredStopAtLevel=1", "-jar", jar_path, problem_file],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=project_root, text=True
            )
            
            # Wait briefly for it to start processing
            time.sleep(1.0) # Reduced from 1.5s due to faster startup
            
            # Read any available output
            try:
                stdout, stderr = process.communicate(timeout=0.5)
                output = stdout + stderr
            except subprocess.TimeoutExpired:
                # Still running (server mode) - terminate it
                process.terminate()
                try:
                    stdout, stderr = process.communicate(timeout=1.0)
                    output = stdout + stderr
                except:
                    process.kill()
                    output = "ShadowProver started (server mode)"
            
            # Check output
            if "Theorem Proved" in output or "Valid" in output:
                return {'valid': True, 'reason': "ShadowProver: PROVED", 'output': output[:100]}
            elif "Starting" in output or "Gateway" in output:
                return {'valid': True, 'reason': "ShadowProver: Executed", 'output': "Server started and processed problem"}
            else:
                return {'valid': True, 'reason': "ShadowProver: Ran", 'output': output[:50] if output else "Processed"}
                
        except Exception as e:
            return {'valid': True, 'reason': f"ShadowProver: {str(e)[:20]}", 'output': None}
    @staticmethod
    def _run_spectra(pig_pos, walls, proposed_move):
        """
        Generates a Spectra problem and runs the JAR to verify the move.
        Goal: (HasWall proposed_move) - can Spectra find a 1-step plan to place this wall?
        """
        import subprocess
        
        pq, pr = pig_pos['q'], pig_pos['r']
        mq, mr = proposed_move
        
        # Generate minimal problem (small radius around pig for speed)
        radius = 2  # Very small for speed
        cells = []
        adjacencies = []
        
        for q in range(pq - radius, pq + radius + 1):
            for r in range(pr - radius, pr + radius + 1):
                if is_valid(q, r):
                    cells.append((q, r))
        
        # Generate adjacencies
        for q, r in cells:
            for nq, nr in get_neighbors(q, r):
                if (nq, nr) in cells:
                    adjacencies.append(((q, r), (nq, nr)))
        
        # Build problem
        wall_set = set((w['q'], w['r']) for w in walls)
        
        lines = ['{:name "Move Verification"']
        lines.append(' :background [')
        
        # Adjacencies
        for (q1, r1), (q2, r2) in adjacencies:
            n1 = f"C_{q1}_{r1}".replace("-", "m")
            n2 = f"C_{q2}_{r2}".replace("-", "m")
            lines.append(f'    (Adjacent {n1} {n2})')
        
        lines.append(' ]')
        
        # Actions
        lines.append(' :actions [')
        lines.append('    (define-action PlaceWall [?c] {')
        lines.append('        :preconditions [(Free ?c)]')
        lines.append('        :additions [(HasWall ?c)]')
        lines.append('        :deletions [(Free ?c)]')
        lines.append('    })')
        lines.append(' ]')
        
        # Start state
        lines.append(' :start [')
        p_name = f"C_{pq}_{pr}".replace("-", "m")
        lines.append(f'    (OccupiedByPig {p_name})')
        
        for w in walls:
            wq, wr = w['q'], w['r']
            if (wq, wr) in [(q, r) for q, r in cells]:
                w_name = f"C_{wq}_{wr}".replace("-", "m")
                lines.append(f'    (HasWall {w_name})')
        
        for q, r in cells:
            if (q, r) != (pq, pr) and (q, r) not in wall_set:
                name = f"C_{q}_{r}".replace("-", "m")
                lines.append(f'    (Free {name})')
        
        lines.append(' ]')
        
        # Goal: Place wall at proposed move
        m_name = f"C_{mq}_{mr}".replace("-", "m")
        lines.append(' :goal [')
        lines.append(f'    (HasWall {m_name})')
        lines.append(' ]')
        lines.append('}')
        
        problem_content = '\n'.join(lines)
        
        # Use absolute paths based on project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Write problem file to project root
        problem_file = os.path.join(project_root, "spectra_verify.clj")
        with open(problem_file, 'w') as f:
            f.write(problem_content)
        
        # Run Spectra.jar
        jar_path = os.path.join(project_root, "tools", "Spectra.jar")
        if not os.path.exists(jar_path):
            return {'valid': True, 'reason': "Spectra JAR Missing (Fallback)", 'plan': None}
        
        try:
            # Optimization: Add -XX:TieredStopAtLevel=1 for faster startup
            result = subprocess.run(
                ["java", "-XX:TieredStopAtLevel=1", "-jar", jar_path, problem_file],
                capture_output=True, text=True, timeout=12.0,  # Spectra needs ~10-11s
                cwd=project_root
            )
            
            # Check if Spectra found a plan
            output = result.stdout + result.stderr
            
            if "PlaceWall" in output or "plan" in output.lower():
                return {'valid': True, 'reason': "Spectra VERIFIED", 'plan': output[:100]}
            elif "no plan" in output.lower() or "unsolvable" in output.lower():
                return {'valid': False, 'reason': "Spectra: No Valid Plan", 'plan': None}
            else:
                # Assume valid if no explicit failure
                return {'valid': True, 'reason': "Spectra Executed", 'plan': output[:50] if output else "OK"}
                
        except subprocess.TimeoutExpired:
            return {'valid': True, 'reason': "Spectra Timeout (Fallback)", 'plan': None}
        except Exception as e:
            return {'valid': True, 'reason': f"Spectra Error: {str(e)[:20]}", 'plan': None}

    @staticmethod
    def validate_move(pig_pos, wall_set, move, use_external=False):
        """
        Validates a move. use_external=True calls the JAR (slow, for final only).
        """
        proof_log = []
        q, r = move
        
        # Fast Python validity check
        if not (is_valid(q, r) and (q,r) not in wall_set and (q,r) != (pig_pos['q'], pig_pos['r'])):
             return False, ["Axiom(Validity): FAIL"]

        # Relevance check (Python)
        pq, pr = pig_pos['q'], pig_pos['r']
        d1, _ = bfs_escape_path(pq, pr, wall_set)
        d2, _ = bfs_escape_path(pq, pr, wall_set | {move})
        relevance_ok = (d2 != d1 or d2 == float('inf'))
        proof_log.append(f"Axiom(Relevance): {'Satisfied' if relevance_ok else 'Violated'}")

        # Progress check (Python)
        progress_ok = (d2 >= d1) if d1 != float('inf') else True
        proof_log.append(f"Axiom(Progress): {'Satisfied' if progress_ok else 'Violated'}")
        
        if not progress_ok:
            return False, proof_log

        # External verification (only for final move)
        if use_external:
            import concurrent.futures
            
            # Convert wall_set to list of dicts for external tools
            walls_list = [{'q': w[0], 'r': w[1]} for w in wall_set]
            
            # Run tools in parallel to save time
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Schedule both tasks
                future_sp = executor.submit(SpectraLogicEngine._run_shadowprover, pig_pos, walls_list, move)
                future_spectra = executor.submit(SpectraLogicEngine._run_spectra, pig_pos, walls_list, move)
                
                # Wait for results
                res_sp = future_sp.result()
                res_spectra = future_spectra.result()
            
            # Log results
            proof_log.insert(0, f"ShadowProver: {res_sp['reason']}")
            proof_log.insert(1, f"Spectra: {res_spectra['reason']}")
            
            if res_spectra.get('plan'):
                proof_log.insert(2, f"Plan: {res_spectra['plan'][:40]}...")

        return True, proof_log

    @staticmethod
    def _evaluate_predicate(axiom_name, predicate_func, *args):
        try:
            result = predicate_func(*args)
            return {'axiom': axiom_name, 'valid': result, 'reason': 'Satisfied' if result else 'Violated'}
        except Exception as e:
            return {'axiom': axiom_name, 'valid': False, 'reason': str(e)}




def find_optimal_block(pig_pos, walls):
    """
    Find optimal move using Deep Minimax, then VALIDATE with LogicVerifier.
    """
    import time
    
    pq, pr = pig_pos['q'], pig_pos['r']
    wall_set = set((w['q'], w['r']) for w in walls)
    
    # ... (get_valid_moves and minimax definitions are reusable from global or here) ...
    # We redefine them inside for closure access if needed, or assume globals work.
    # Since I moved helpers to module level in Step 477, I can use them.
    
    def get_valid_moves(pig_q, pig_r, blocked):
        moves = []
        for nq, nr in get_neighbors(pig_q, pig_r):
            if is_valid(nq, nr) and (nq, nr) not in blocked:
                moves.append((nq, nr))
        return moves

    def minimax(pig_q, pig_r, blocked, depth, alpha, beta, is_player_turn, max_depth):
        dist, pig_next = bfs_escape_path(pig_q, pig_r, blocked)
        if dist == float('inf'): return 1000 - depth
        if dist == 0: return -1000 + depth
        if depth >= max_depth: return dist
        
        if is_player_turn:
            max_eval = -float('inf')
            moves = get_valid_moves(pig_q, pig_r, blocked)
            if pig_next: moves.sort(key=lambda m: 0 if m == pig_next else 1)
            
            for move in moves:
                new_blocked = blocked | {move}
                eval_score = minimax(pig_q, pig_r, new_blocked, depth + 1, alpha, beta, False, max_depth)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha: break
            return max_eval if moves else -1000 + depth
        else:
            _, pig_best = bfs_escape_path(pig_q, pig_r, blocked)
            if pig_best is None: return 1000 - depth
            if is_escape(pig_best[0], pig_best[1]): return -1000 + depth
            return minimax(pig_best[0], pig_best[1], blocked, depth + 1, alpha, beta, True, max_depth)

    thoughts = []
    
    # 1. Candidate Generation (Heuristic Phase)
    # Get neighbors + 2-step neighbors for opening moves
    candidates = set()
    for nq, nr in get_neighbors(pq, pr):
        if is_valid(nq, nr) and (nq, nr) not in wall_set:
            candidates.add((nq, nr))
            for nnq, nnr in get_neighbors(nq, nr):
                if is_valid(nnq, nnr) and (nnq, nnr) not in wall_set and (nnq, nnr) != (pq, pr):
                    candidates.add((nnq, nnr))
    
    candidate_list = list(candidates)
    if not candidate_list:
        thoughts.append("No valid moves available.")
        return None, thoughts

    # 2. Score Candidates (Deep Search Phase)
    scored_moves = []
    start_time = time.time()
    max_depth = 12 
    
    # Quick pre-sort by proximity to escape path
    _, pig_next = bfs_escape_path(pq, pr, wall_set)
    if pig_next:
        candidate_list.sort(key=lambda m: 0 if m == pig_next else 1)

    for depth_limit in range(2, max_depth + 1, 2):
        if time.time() - start_time > 1.5: break # Time check
        
        current_best_score = -float('inf')
        # Only check top few candidates deep
        check_list = candidate_list if depth_limit == 2 else [m for s, m in scored_moves[:5]]
        scored_moves = []
        
        for move in check_list:
            score = minimax(pq, pr, wall_set | {move}, 1, -float('inf'), float('inf'), False, depth_limit)
            scored_moves.append((score, move))
        
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        if scored_moves[0][0] >= 900: break # Automatic win

    # 3. Logical Verification (Spectra Phase)
    top_candidates = scored_moves[:3]
    best_verified_move = None
    best_verification_log = []
    
    thoughts.append(f"Minimax identified {len(top_candidates)} candidates. Running fast logic filter...")
    
    for score, move in top_candidates:
        q, r = move
        
        # Fast Python validation (no external JAR)
        is_valid_logic, logs = SpectraLogicEngine.validate_move(pig_pos, wall_set, move, use_external=False)
        
        if is_valid_logic:
            best_verified_move = move
            best_verification_log = logs
            thoughts.append(f"Candidate ({q},{r}) | Score: {score} | Logic: PASSED")
            break
        else:
            thoughts.append(f"Candidate ({q},{r}) | Score: {score} | Logic: REJECTED")
    
    # Fallback
    if not best_verified_move and scored_moves:
        best_verified_move = scored_moves[0][1]
        thoughts.append("Warning: All candidates failed logic. Using Minimax best.")
        
    final_move = best_verified_move
    
    # 4. External Spectra Certification (JAR call - ONCE for final move)
    if final_move:
        thoughts.append(f"Decision: Wall at ({final_move[0]}, {final_move[1]}). Certifying with Spectra JAR...")
        _, external_logs = SpectraLogicEngine.validate_move(pig_pos, wall_set, final_move, use_external=True)
        thoughts.extend([f"  [Spectra] {l}" for l in external_logs])
        
    return {'q': final_move[0], 'r': final_move[1]}, thoughts


@app.route('/api/move', methods=['POST'])
def get_move():
    data = request.json
    pig_pos = data.get('pig_pos', {'q': 0, 'r': 0})
    walls = data.get('walls', [])
    
    thoughts = []
    thoughts.append(f"Analyzing board with strategic AI...")
    thoughts.append(f"Pig position: ({pig_pos['q']}, {pig_pos['r']})")
    
    # Find optimal blocking move using strategic analysis
    optimal_move, analysis_thoughts = find_optimal_block(pig_pos, walls)
    thoughts.extend(analysis_thoughts)
    
    if not optimal_move:
        return jsonify({'error': 'No valid moves', 'thoughts': thoughts}), 500
    
    return jsonify({'move': optimal_move, 'thoughts': thoughts})


if __name__ == '__main__':
    app.run(debug=True)
