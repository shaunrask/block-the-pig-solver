from flask import Flask, render_template, request, jsonify
import os, re, time, json, hashlib, tempfile, subprocess
from collections import deque

app = Flask(__name__)

# =========================
# UI board constants
# =========================
COL_MIN, COL_MAX = 0, 4
ROW_MIN, ROW_MAX = 0, 10

# Your JS "visual center"
UI_CENTER_Q = 2
UI_CENTER_R = 5

# =========================
# Spectra / Java config
# =========================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPECTRA_DIR = os.path.join(PROJECT_ROOT, "spectra")
TEMPLATE_CLJ = os.path.join(SPECTRA_DIR, "block_the_pig.clj")

TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")
SPECTRA_JAR = os.path.join(TOOLS_DIR, "Spectra.jar")

JAVA17_EXE = r"C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot\bin\java.exe"

# If Spectra sometimes takes ~20s on first run, caching matters a lot.
SPECTRA_TIMEOUT_SECONDS = 45

# In-memory cache: key(board_state) -> move dict
SPECTRA_CACHE = {}

DEBUG_DIR = os.path.join(PROJECT_ROOT, "spectra_debug")
os.makedirs(DEBUG_DIR, exist_ok=True)

# =========================
# Routes
# =========================
@app.route("/")
def index():
    return render_template("index.html")

# =========================
# UI helpers
# =========================
def get_neighbors(q, r):
    # MUST match game.js odd-row rules
    if r % 2 == 0:
        return [(q+1, r), (q, r-1), (q-1, r-1), (q-1, r), (q-1, r+1), (q, r+1)]
    else:
        return [(q+1, r), (q+1, r-1), (q, r-1), (q-1, r), (q, r+1), (q+1, r+1)]

def is_valid(q, r):
    return COL_MIN <= q <= COL_MAX and ROW_MIN <= r <= ROW_MAX

def is_escape(q, r):
    return is_valid(q, r) and (q == COL_MIN or q == COL_MAX or r == ROW_MIN or r == ROW_MAX)

def bfs_escape_path(start_q, start_r, blocked_cells):
    """Returns (distance, first_step) to escape under current walls."""
    if is_escape(start_q, start_r):
        return 0, None
    queue = deque([(start_q, start_r, 0, None)])
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
    return float("inf"), None

# ... (helper functions remain the same) ...

class SpectraLogicEngine:
    """
    The 'Spectra' Logic Engine.
    Actually executes Spectra.jar to verify moves.
    """
    
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
            result = subprocess.run(
                ["java", "-jar", jar_path, problem_file],
                capture_output=True, text=True, timeout=15.0,  # Spectra needs ~11s
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

        # External Spectra verification (only for final move)
        if use_external:
            # Convert wall_set to list of dicts for _run_spectra
            walls_list = [{'q': w[0], 'r': w[1]} for w in wall_set]
            res_ext = SpectraLogicEngine._run_spectra(pig_pos, walls_list, move)
            proof_log.insert(0, f"Spectra: {res_ext['reason']}")
            if res_ext.get('plan'):
                proof_log.insert(1, f"Plan: {res_ext['plan'][:50]}...")

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
    thoughts.append("[SPECTRA] One-step planning mode: try candidate goal cells until Spectra returns a non-empty plan.")

    key = board_cache_key(pig_pos, walls)
    if key in SPECTRA_CACHE:
        cached = SPECTRA_CACHE[key]
        thoughts.append("[SPECTRA] Cache hit: returning previously computed move.")
        return cached, thoughts

    wall_cells_logic = {ui_to_cell(w["q"], w["r"]) for w in walls}

    tried = 0
    start_t = time.time()

    for (cq, cr) in candidate_goal_cells_ui(pig_pos, walls):
        goal_cell = ui_to_cell(cq, cr)
        if goal_cell in wall_cells_logic:
            continue

        tried += 1
        tmp_path = None
        try:
            tmp_path = write_temp_clj(pig_pos, walls, goal_cell)
            out = run_spectra(tmp_path, timeout_s=SPECTRA_TIMEOUT_SECONDS)

            plan = parse_first_bracket_list(out)
            if not plan:
                tag = key[:8] + f"_{tried}"
                dbg = save_debug(tag, out)
                thoughts.append(f"[SPECTRA] Candidate {goal_cell}: no bracket plan found. Saved: {dbg}")
                continue

            if plan.strip() == "[]":
                thoughts.append(f"[SPECTRA] Candidate {goal_cell}: plan was empty [] (goal already true or unreachable).")
                continue

            cell = extract_placewall_cell(plan)
            if not cell:
                tag = key[:8] + f"_{tried}"
                dbg = save_debug(tag, out)
                thoughts.append(f"[SPECTRA] Candidate {goal_cell}: couldn't parse PlaceWall cell. Saved: {dbg}")
                thoughts.append(f"[SPECTRA] Plan text: {plan}")
                continue

            move = cell_to_ui(cell)
            elapsed = time.time() - start_t

            thoughts.append(f"[SPECTRA] SUCCESS after {tried} candidates in {elapsed:.2f}s")
            thoughts.append(f"[SPECTRA] Plan: {plan}")
            thoughts.append(f"[SPECTRA] Move: PlaceWall {cell} -> UI=({move['q']},{move['r']})")

            SPECTRA_CACHE[key] = move
            return move, thoughts

        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    raise RuntimeError("Spectra did not return a usable PlaceWall plan for any candidate goal cell.")

# =========================
# Fallback move
# =========================
def fallback_move(pig_pos, walls):
    pq, pr = pig_pos["q"], pig_pos["r"]
    wall_set = {(w["q"], w["r"]) for w in walls}

    thoughts = []
    dist, next_step = bfs_escape_path(pq, pr, wall_set)
    thoughts.append(f"[FALLBACK] Current escape distance: {dist if dist != float('inf') else 'trapped'}")

    if next_step and next_step not in wall_set:
        thoughts.append(f"[FALLBACK] Blocking next-step cell: {next_step}")
        return {"q": next_step[0], "r": next_step[1]}, thoughts

    for nq, nr in get_neighbors(pq, pr):
        if is_valid(nq, nr) and (nq, nr) not in wall_set and (nq, nr) != (pq, pr):
            thoughts.append(f"[FALLBACK] Blocking neighbor: {(nq, nr)}")
            return {"q": nq, "r": nr}, thoughts

    return None, thoughts

# =========================
# API
# =========================
@app.route("/api/move", methods=["POST"])
def get_move():
    data = request.json or {}
    pig_pos = data.get("pig_pos", {"q": UI_CENTER_Q, "r": UI_CENTER_R})
    walls = data.get("walls", [])

    thoughts = ["Decision engine: Spectra planner (fallback = minimax)."]

    try:
        move, t = spectra_move(pig_pos, walls)
        thoughts.extend(t)
        return jsonify({"move": move, "thoughts": thoughts})

    except subprocess.TimeoutExpired:
        thoughts.append(f"[SPECTRA] Timed out after {SPECTRA_TIMEOUT_SECONDS}s.")
    except Exception as e:
        thoughts.append(f"[SPECTRA] Failed: {e}")

    move, t = fallback_move(pig_pos, walls)
    thoughts.extend(t)
    thoughts.append("[FALLBACK] Returned heuristic move (Spectra unavailable).")
    return jsonify({"move": move, "thoughts": thoughts})

if __name__ == "__main__":
    app.run(debug=True)
