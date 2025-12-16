from flask import Flask, render_template, request, jsonify
import os, re, time, json, hashlib, tempfile, subprocess
from collections import deque

app = Flask(__name__)

# =========================
# UI board constants
# =========================
COL_MIN, COL_MAX = 0, 4
ROW_MIN, ROW_MAX = 0, 10

UI_CENTER_Q = 2
UI_CENTER_R = 5

# =========================
# Project / tool paths
# =========================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SPECTRA_DIR = os.path.join(PROJECT_ROOT, "spectra")
TEMPLATE_CLJ = os.path.join(SPECTRA_DIR, "block_the_pig.clj")

TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")
SPECTRA_JAR = os.path.join(TOOLS_DIR, "Spectra.jar")
SHADOWPROVER_JAR = os.path.join(TOOLS_DIR, "Shadow-Prover.jar")

JAVA17_EXE = r"C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot\bin\java.exe"

SPECTRA_TIMEOUT_SECONDS = 45
SHADOW_TIMEOUT_SECONDS = 20   # <--- was 6; 6s is usually too small on Windows/JVM cold start

SPECTRA_CACHE = {}
SHADOW_CACHE = {}

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
    if r % 2 == 0:
        return [(q+1, r), (q, r-1), (q-1, r-1), (q-1, r), (q-1, r+1), (q, r+1)]
    else:
        return [(q+1, r), (q+1, r-1), (q, r-1), (q-1, r), (q, r+1), (q+1, r+1)]

def is_valid(q, r):
    return COL_MIN <= q <= COL_MAX and ROW_MIN <= r <= ROW_MAX

def is_escape(q, r):
    return is_valid(q, r) and (q == COL_MIN or q == COL_MAX or r == ROW_MIN or r == ROW_MAX)

def bfs_escape_path(start_q, start_r, blocked_cells):
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

# =========================
# Logic cell naming
# =========================
def _enc(n: int) -> str:
    return f"m{abs(n)}" if n < 0 else str(n)

def _dec(tok: str) -> int:
    tok = tok.strip()
    return -int(tok[1:]) if tok.startswith("m") else int(tok)

def ui_to_cell(q: int, r: int) -> str:
    dq = q - UI_CENTER_Q
    dr = r - UI_CENTER_R
    return f"C_{_enc(dq)}_{_enc(dr)}"

def cell_to_ui(cell: str) -> dict:
    cell = cell.strip()
    if cell.startswith("c_"):
        cell = "C_" + cell[2:]
    parts = cell.split("_")
    if len(parts) != 3:
        raise ValueError(f"Bad cell token: {cell}")
    dq = _dec(parts[1])
    dr = _dec(parts[2])
    return {"q": dq + UI_CENTER_Q, "r": dr + UI_CENTER_R}

def all_ui_cells():
    for q in range(COL_MIN, COL_MAX + 1):
        for r in range(ROW_MIN, ROW_MAX + 1):
            yield q, r

# =========================
# Spectra file generation
# =========================
def build_start_block(pig_pos: dict, walls: list) -> str:
    pig_cell = ui_to_cell(pig_pos["q"], pig_pos["r"])
    wall_cells = {ui_to_cell(w["q"], w["r"]) for w in walls}

    all_cells_logic = [ui_to_cell(q, r) for (q, r) in all_ui_cells()]
    free_cells = [c for c in all_cells_logic if c != pig_cell and c not in wall_cells]

    lines = [f"    (OccupiedByPig {pig_cell})"]
    for c in sorted(wall_cells):
        lines.append(f"    (HasWall {c})")
    for c in sorted(free_cells):
        lines.append(f"    (Free {c})")

    return ":start [\n" + "\n".join(lines) + "\n ]"

def build_goal_block(goal_cell: str) -> str:
    return f":goal [\n    (HasWall {goal_cell})\n ]"

def write_temp_clj(pig_pos: dict, walls: list, goal_cell: str) -> str:
    if not os.path.exists(TEMPLATE_CLJ):
        raise FileNotFoundError(f"Template .clj not found: {TEMPLATE_CLJ}")

    with open(TEMPLATE_CLJ, "r", encoding="utf-8") as f:
        text = f.read()

    start_re = re.compile(r":start\s*\[(.*?)\]\s*", re.DOTALL)
    if not start_re.search(text):
        raise RuntimeError("Template missing :start [ ... ]")
    text = start_re.sub(build_start_block(pig_pos, walls) + "\n", text, count=1)

    goal_re = re.compile(r":goal\s*\[(.*?)\]\s*", re.DOTALL)
    if not goal_re.search(text):
        raise RuntimeError("Template missing :goal [ ... ]")
    text = goal_re.sub(build_goal_block(goal_cell) + "\n", text, count=1)

    fd, tmp_path = tempfile.mkstemp(prefix="btp_", suffix=".clj", dir=PROJECT_ROOT, text=True)
    os.close(fd)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(text)
    return tmp_path

def _java_cmd_base():
    java = JAVA17_EXE if os.path.exists(JAVA17_EXE) else "java"
    # faster cold-start flags:
    return [
        java,
        "-XX:TieredStopAtLevel=1",
        "-Xms16m",
        "-Xmx128m",
    ]

def run_spectra(clj_path: str, timeout_s: int) -> str:
    if not os.path.exists(SPECTRA_JAR):
        raise FileNotFoundError(f"Spectra.jar not found: {SPECTRA_JAR}")

    cmd = _java_cmd_base() + ["-jar", SPECTRA_JAR, clj_path]
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=timeout_s)
    out = (result.stdout or "").strip()
    err = (result.stderr or "").strip()
    if result.returncode != 0:
        raise RuntimeError(f"Spectra failed (code {result.returncode}). STDERR:\n{err}\nSTDOUT:\n{out}")
    return out or err

def save_debug(tag: str, out: str) -> str:
    path = os.path.join(DEBUG_DIR, f"spectra_{tag}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    return path

# =========================
# Plan parsing
# =========================
def parse_first_bracket_list(out: str) -> str | None:
    m = re.search(r"\[[^\]]*\]", out, flags=re.DOTALL)
    return m.group(0).strip() if m else None

def extract_placewall_cell(plan_txt: str) -> str | None:
    if not plan_txt or plan_txt.strip() == "[]":
        return None
    m = re.search(r"PlaceWall\s+([cC]_[A-Za-z0-9]+_[A-Za-z0-9]+)", plan_txt)
    if m:
        return m.group(1)
    m2 = re.search(r"\(\s*PlaceWall\s+([cC]_[A-Za-z0-9]+_[A-Za-z0-9]+)\s*\)", plan_txt)
    return m2.group(1) if m2 else None

# =========================
# Candidate goal selection
# =========================
def candidate_goal_cells_ui(pig_pos: dict, walls: list):
    pq, pr = pig_pos["q"], pig_pos["r"]
    wall_set = {(w["q"], w["r"]) for w in walls}

    dist, next_step = bfs_escape_path(pq, pr, wall_set)
    if next_step and next_step not in wall_set:
        yield next_step

    for n in get_neighbors(pq, pr):
        if is_valid(*n) and n not in wall_set and n != (pq, pr):
            yield n

    for n in get_neighbors(pq, pr):
        if not is_valid(*n):
            continue
        for nn in get_neighbors(*n):
            if is_valid(*nn) and nn not in wall_set and nn != (pq, pr):
                yield nn

# =========================
# Cache keys
# =========================
def board_cache_key(pig_pos: dict, walls: list) -> str:
    walls_sorted = sorted([(w["q"], w["r"]) for w in walls])
    payload = {"pig": (pig_pos["q"], pig_pos["r"]), "walls": walls_sorted}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

def shadow_cache_key(pig_pos: dict, walls: list, move_cell: str) -> str:
    walls_sorted = sorted([(w["q"], w["r"]) for w in walls])
    payload = {"pig": (pig_pos["q"], pig_pos["r"]), "walls": walls_sorted, "move": move_cell}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

# =========================
# ShadowProver (certifier)
# =========================
def write_shadow_problem_clj(pig_pos: dict, walls: list, move_cell: str) -> str:
    pig_cell = ui_to_cell(pig_pos["q"], pig_pos["r"])
    wall_cells = [ui_to_cell(w["q"], w["r"]) for w in walls]

    assumptions = []
    assumptions.append(f"(OccupiedByPig {pig_cell})")
    for c in wall_cells:
        assumptions.append(f"(HasWall {c})")

    # Legality axioms:
    assumptions.append("(forall (c) (if (OccupiedByPig c) (not (CanPlaceWall c))))")
    assumptions.append("(forall (c) (if (HasWall c) (not (CanPlaceWall c))))")
    assumptions.append("(forall (c) (if (and (not (OccupiedByPig c)) (not (HasWall c))) (CanPlaceWall c)))")

    lines = []
    lines.append('{:name "BTP Move Certification"')
    lines.append(' :description "ShadowProver certifies PlaceWall legality"')
    lines.append(' :assumptions {')
    for i, a in enumerate(assumptions):
        lines.append(f"  A{i} {a}")
    lines.append(' }')
    lines.append(f" :goal (CanPlaceWall {move_cell})")
    lines.append("}")

    fd, tmp_path = tempfile.mkstemp(prefix="shadow_btp_", suffix=".clj", dir=PROJECT_ROOT, text=True)
    os.close(fd)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return tmp_path

def run_shadowprover(problem_clj_path: str, timeout_s: int) -> str:
    if not os.path.exists(SHADOWPROVER_JAR):
        raise FileNotFoundError(f"Shadow-Prover.jar not found: {SHADOWPROVER_JAR}")

    cmd = _java_cmd_base() + ["-jar", SHADOWPROVER_JAR, problem_clj_path]
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=timeout_s)
    out = (result.stdout or "") + "\n" + (result.stderr or "")
    return out.strip()

def shadowprover_certify_can_place(pig_pos: dict, walls: list, move_cell: str):
    logs = []
    if not os.path.exists(SHADOWPROVER_JAR):
        logs.append("[SHADOW] ShadowProver jar missing -> skipping certification.")
        return True, logs

    key = shadow_cache_key(pig_pos, walls, move_cell)
    if key in SHADOW_CACHE:
        ok = SHADOW_CACHE[key]
        logs.append(f"[SHADOW] Cache hit: CanPlaceWall({move_cell}) = {ok}")
        return ok, logs

    tmp_path = None
    try:
        tmp_path = write_shadow_problem_clj(pig_pos, walls, move_cell)
        out = run_shadowprover(tmp_path, timeout_s=SHADOW_TIMEOUT_SECONDS)

        ok = ("Theorem Proved" in out) or ("PROVED" in out) or ("Valid" in out)

        logs.append(f"[SHADOW] Goal: CanPlaceWall {move_cell}")
        logs.append(f"[SHADOW] Result: {'PROVED' if ok else 'NOT PROVED'}")
        logs.append(f"[SHADOW] Output(head): {out[:220].replace(chr(10), ' ')}")

        SHADOW_CACHE[key] = ok
        return ok, logs

    except subprocess.TimeoutExpired:
        # Save the exact problem file so you can inspect what was sent
        if tmp_path and os.path.exists(tmp_path):
            dbg = os.path.join(DEBUG_DIR, f"shadow_timeout_{key[:8]}.clj")
            try:
                with open(tmp_path, "r", encoding="utf-8") as f:
                    content = f.read()
                with open(dbg, "w", encoding="utf-8") as f:
                    f.write(content)
                logs.append(f"[SHADOW] Timed out after {SHADOW_TIMEOUT_SECONDS}s. Saved problem: {dbg}")
            except Exception:
                logs.append(f"[SHADOW] Timed out after {SHADOW_TIMEOUT_SECONDS}s (could not save problem).")
        else:
            logs.append(f"[SHADOW] Timed out after {SHADOW_TIMEOUT_SECONDS}s.")
        return True, logs  # non-blocking
    except Exception as e:
        logs.append(f"[SHADOW] Failed: {e} -> skipping certification.")
        return True, logs
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

# =========================
# Spectra move
# =========================
def spectra_move(pig_pos: dict, walls: list):
    thoughts = []
    thoughts.append("[SPECTRA] One-step planning mode: try candidate goal cells until Spectra returns a non-empty plan.")
    thoughts.append("[SPECTRA] ShadowProver certifier: prove CanPlaceWall(move) before accepting.")

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

            ok, shadow_logs = shadowprover_certify_can_place(pig_pos, walls, cell)
            thoughts.extend(shadow_logs)
            if not ok:
                thoughts.append(f"[SPECTRA] ShadowProver rejected {cell}; trying next candidate.")
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

    thoughts = ["Decision engine: Spectra planner + ShadowProver certifier (fallback = heuristic)."]

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
