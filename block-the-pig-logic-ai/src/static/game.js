const canvas = document.getElementById('hexGrid');
const ctx = canvas.getContext('2d');
const turnIndicator = document.getElementById('turnIndicator');
const wallCountDisplay = document.getElementById('wallCount');
const aiMoveBtn = document.getElementById('aiMoveBtn');
const resetBtn = document.getElementById('resetBtn');
const overlay = document.getElementById('messageOverlay');
const messageTitle = document.getElementById('messageTitle');
const messageText = document.getElementById('messageText');
const overlayResetBtn = document.getElementById('overlayResetBtn');

// =======================
// Game State / Config
// =======================

// Board is 5 columns (0..4) x 11 rows (0..10)
const COL_MIN = 0;
const COL_MAX = 4;
const ROW_MIN = 0;
const ROW_MAX = 10;
const NUM_COLS = COL_MAX - COL_MIN + 1; // 5
const NUM_ROWS = ROW_MAX - ROW_MIN + 1; // 11

// Pig starts in the visual center row/column
const PIG_START_COL = 2;  // middle column (0..4)
const PIG_START_ROW = 5;  // middle row   (0..10)

const HEX_SIZE_DEFAULT = 25;
let HEX_SIZE = HEX_SIZE_DEFAULT;
let CENTER_X = canvas.width / 2;
let CENTER_Y = canvas.height / 2;
const SQRT3 = Math.sqrt(3);

let pigPos = { q: PIG_START_COL, r: PIG_START_ROW }; // q=col, r=row
let walls = [];
let turn = 'PLAYER'; // 'PLAYER' or 'PIG'
let isGameOver = false;
let wallsPlacedCount = 0; // Track player wall moves

// Precompute the center offset so that (PIG_START_COL, PIG_START_ROW) is at canvas center
function basePixelForCell(col, row) {
    // Odd-row (row) offset, pointy-topped layout:
    // x' = size * sqrt(3) * (col + 0.5*(row%2))
    // y' = size * 1.5 * row
    const x = HEX_SIZE * SQRT3 * (col + 0.5 * (row & 1));
    const y = HEX_SIZE * 1.5 * row;
    return { x, y };
}
let PIG_BASE_POS = basePixelForCell(PIG_START_COL, PIG_START_ROW);

function resizeCanvas() {
    const container = document.querySelector('.main-area');
    if (!container) return;

    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    CENTER_X = canvas.width / 2;
    CENTER_Y = canvas.height / 2;

    // Calculate HEX_SIZE to fit
    // Board width approx: (NUM_COLS + 0.5) * HEX_SIZE * sqrt(3)
    // Board height approx: (NUM_ROWS * 1.5 + 0.5) * HEX_SIZE
    // We add some padding (0.8 factor)
    const boardWidthHex = (NUM_COLS + 1) * SQRT3;
    const boardHeightHex = (NUM_ROWS * 1.5 + 1);

    const sizeW = (canvas.width * 0.8) / boardWidthHex;
    const sizeH = (canvas.height * 0.8) / boardHeightHex;
    HEX_SIZE = Math.min(sizeW, sizeH);

    // Recalculate base pos with new HEX_SIZE
    PIG_BASE_POS = basePixelForCell(PIG_START_COL, PIG_START_ROW);

    drawBoard();
}

window.addEventListener('resize', resizeCanvas);
// Call once after script load (at bottom) or now
setTimeout(resizeCanvas, 0);

// =======================
// Hex Utilities (odd-row offset, pointy-top)
// =======================

// Cell -> pixel (center) relative to canvas
function hexToPixel(q, r) {
    const base = basePixelForCell(q, r);
    // Center the board so the pig's start cell is at canvas center
    const dx = base.x - PIG_BASE_POS.x;
    const dy = base.y - PIG_BASE_POS.y;
    return { x: CENTER_X + dx, y: CENTER_Y + dy };
}

// For clicks: brute-force search nearest cell center.
// Board is small (55 cells), so this is simple & robust.
function pixelToHex(x, y) {
    let bestCell = null;
    let bestDist2 = Infinity;

    for (let q = COL_MIN; q <= COL_MAX; q++) {
        for (let r = ROW_MIN; r <= ROW_MAX; r++) {
            const { x: cx, y: cy } = hexToPixel(q, r);
            const dx = cx - x;
            const dy = cy - y;
            const dist2 = dx * dx + dy * dy;
            if (dist2 < bestDist2 && dist2 <= HEX_SIZE * HEX_SIZE) {
                bestDist2 = dist2;
                bestCell = { q, r };
            }
        }
    }

    return bestCell; // may be null if click was far from any hex
}

// Odd-row neighbors (pointy-top, redblobgames "odd-r" horizontal layout)
function getNeighbors(q, r) {
    const isOdd = r & 1;

    // row is even
    const dirsEven = [
        { q: +1, r: 0 },   // E
        { q: 0, r: -1 },  // NE
        { q: -1, r: -1 },  // NW
        { q: -1, r: 0 },   // W
        { q: -1, r: +1 },  // SW
        { q: 0, r: +1 }   // SE
    ];

    // row is odd
    const dirsOdd = [
        { q: +1, r: 0 },   // E
        { q: +1, r: -1 },  // NE
        { q: 0, r: -1 },  // NW
        { q: -1, r: 0 },   // W
        { q: 0, r: +1 },  // SW
        { q: +1, r: +1 }   // SE
    ];

    const dirs = isOdd ? dirsOdd : dirsEven;
    return dirs.map(d => ({ q: q + d.q, r: r + d.r }));
}

// =======================
// Board Helpers
// =======================
function isInsideBoard(q, r) {
    return (
        q >= COL_MIN && q <= COL_MAX &&
        r >= ROW_MIN && r <= ROW_MAX
    );
}

function isPlayableCell(q, r) {
    return isInsideBoard(q, r);
}

function hasWall(q, r) {
    return walls.some(w => w.q === q && w.r === r);
}

/**
 * Escape rule:
 * A cell is an escape cell if it lies on the border of the 5×11 board.
 * Pig escapes immediately upon stepping onto any border cell.
 */
function isEscape(q, r) {
    if (!isInsideBoard(q, r)) return false;

    return (
        q === COL_MIN ||
        q === COL_MAX ||
        r === ROW_MIN ||
        r === ROW_MAX
    );
}

// =======================
// Drawing
// =======================
function drawHex(q, r, color, strokeColor = '#cbd5e1', lineWidth = 1) {
    const { x, y } = hexToPixel(q, r);
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
        // 30° offset for "point-up" hexes
        const angle_rad = Math.PI / 180 * (60 * i + 30);
        const px = x + HEX_SIZE * Math.cos(angle_rad);
        const py = y + HEX_SIZE * Math.sin(angle_rad);
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = lineWidth;
    ctx.stroke();
}

function drawBoard() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw 5×11 staggered rows:
    // row0:  XXXXX
    // row1:   XXXXX
    // row2:  XXXXX
    // etc.
    for (let q = COL_MIN; q <= COL_MAX; q++) {
        for (let r = ROW_MIN; r <= ROW_MAX; r++) {
            if (!isPlayableCell(q, r)) continue;

            let fill = '#f1f5f9'; // Light slate
            let stroke = '#cbd5e1'; // Lighter slate border
            let lineWidth = 1;

            if (hasWall(q, r)) {
                fill = '#475569'; // Dark slate for walls
                stroke = '#334155'; // Darker border
                lineWidth = 2;
            }

            drawHex(q, r, fill, stroke, lineWidth);
        }
    }

    // Draw pig on top
    drawHex(pigPos.q, pigPos.r, '#fce7f3', '#db2777', 3);

    const { x, y } = hexToPixel(pigPos.q, pigPos.r);
    ctx.fillStyle = '#db2777';
    ctx.font = 'bold 20px Outfit';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('🐷', x, y);
}

// =======================
// Game Logic
// =======================
function checkGameOver() {
    // 1. Pig Escaped?
    if (isEscape(pigPos.q, pigPos.r)) {
        endGame(false, "The Pig Escaped!");
        return true;
    }

    // 2. Pig Trapped?
    if (!canReachEscape(pigPos)) {
        endGame(true, "You Trapped the Pig!");
        return true;
    }

    return false;
}

function canReachEscape(startPos) {
    let queue = [startPos];
    let visited = new Set();
    visited.add(`${startPos.q},${startPos.r}`);

    while (queue.length > 0) {
        let current = queue.shift();

        if (isEscape(current.q, current.r)) return true;

        let neighbors = getNeighbors(current.q, current.r);
        for (let n of neighbors) {
            let key = `${n.q},${n.r}`;
            if (
                isPlayableCell(n.q, n.r) &&
                !visited.has(key) &&
                !hasWall(n.q, n.r)
            ) {
                visited.add(key);
                queue.push(n);
            }
        }
    }
    return false;
}

function endGame(win, message) {
    isGameOver = true;
    messageTitle.textContent = win ? "Victory!" : "Defeat";
    messageTitle.style.color = win ? "#4ade80" : "#ef4444";
    messageText.textContent = message;
    overlay.classList.remove('hidden');
}

function resetGame() {
    pigPos = { q: PIG_START_COL, r: PIG_START_ROW };
    walls = [];
    turn = 'PLAYER';
    isGameOver = false;
    wallsPlacedCount = 0;

    // Random walls (5–15) anywhere on the board except pig start
    const numWalls = Math.floor(Math.random() * 11) + 5;
    for (let i = 0; i < numWalls; i++) {
        let valid = false;
        while (!valid) {
            let q = Math.floor(Math.random() * NUM_COLS) + COL_MIN;
            let r = Math.floor(Math.random() * NUM_ROWS) + ROW_MIN;

            if (
                isPlayableCell(q, r) &&
                (q !== pigPos.q || r !== pigPos.r) &&
                !hasWall(q, r)
            ) {
                walls.push({ q, r });
                valid = true;
            }
        }
    }

    updateUI();
    drawBoard();
    overlay.classList.add('hidden');
}

function updateUI() {
    let statusText = "";
    if (turn === 'PLAYER') {
        if (wallsPlacedCount < 3) {
            statusText = `Opening Phase (${3 - wallsPlacedCount} left)`;
        } else {
            statusText = "Your Turn";
        }
    } else {
        statusText = "Pig's Turn";
    }

    turnIndicator.textContent = statusText;
    turnIndicator.className = turn === 'PLAYER' ? "value player-turn" : "value pig-turn";
    wallCountDisplay.textContent = walls.length;
    aiMoveBtn.disabled = turn !== 'PLAYER' || isGameOver;
}

// =======================
// Interaction
// =======================
canvas.addEventListener('click', (e) => {
    if (isGameOver || turn !== 'PLAYER') return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const hex = pixelToHex(x, y);

    if (!hex) return; // clicked outside any cell

    const { q, r } = hex;

    if (!isPlayableCell(q, r)) return;

    // Check if empty
    if (q === pigPos.q && r === pigPos.r) return;
    if (hasWall(q, r)) return;

    // Place Wall
    walls.push({ q, r });
    wallsPlacedCount++;

    updateUI();
    drawBoard();

    if (!checkGameOver()) {
        if (wallsPlacedCount >= 3) {
            turn = 'PIG';
            setTimeout(pigTurn, 500);
        } else {
            turn = 'PLAYER';
            updateUI();
        }
    }
});

// =======================
// Pig Turn
// =======================
function pigTurn() {
    if (isGameOver) return;

    // BFS for Shortest Path to Escape
    let queue = [{ pos: pigPos, path: [] }];
    let visited = new Set();
    visited.add(`${pigPos.q},${pigPos.r}`);

    let bestMove = null;

    while (queue.length > 0) {
        let { pos, path } = queue.shift();

        if (isEscape(pos.q, pos.r)) {
            if (path.length > 0) {
                bestMove = path[0];
            } else {
                bestMove = pos;
            }
            break;
        }

        let neighbors = getNeighbors(pos.q, pos.r);
        neighbors.sort(() => Math.random() - 0.5); // variety

        for (let n of neighbors) {
            let key = `${n.q},${n.r}`;
            if (
                isPlayableCell(n.q, n.r) &&
                !visited.has(key) &&
                !hasWall(n.q, n.r)
            ) {
                visited.add(key);
                let newPath = [...path, n];
                queue.push({ pos: n, path: newPath });
            }
        }
    }

    if (bestMove) {
        pigPos = bestMove;
    } else {
        // No path to escape? Move randomly to a free playable neighbor
        const neighbors = getNeighbors(pigPos.q, pigPos.r);
        const validMoves = neighbors.filter(n =>
            isPlayableCell(n.q, n.r) && !hasWall(n.q, n.r)
        );
        if (validMoves.length > 0) {
            pigPos = validMoves[0];
        }
    }

    turn = 'PLAYER';
    updateUI();
    drawBoard();
    checkGameOver();
}

// =======================
// AI Integration
// =======================
aiMoveBtn.addEventListener('click', async () => {
    if (turn !== 'PLAYER' || isGameOver) return;

    aiMoveBtn.textContent = "Thinking...";
    aiMoveBtn.disabled = true;

    const phase = wallsPlacedCount < 3 ? 'OPENING' : 'MAIN';

    try {
        const response = await fetch('/api/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pig_pos: pigPos, walls: walls, phase: phase })
        });

        const data = await response.json();

        if (data.move) {
            // Display Thoughts
            const thoughtLog = document.getElementById('thoughtLog');
            thoughtLog.innerHTML = ''; // Clear placeholder

            if (data.thoughts && data.thoughts.length > 0) {
                data.thoughts.forEach(thought => {
                    const p = document.createElement('p');
                    p.textContent = `> ${thought}`;

                    // Simple highlighting
                    if (thought.includes("Decision")) p.className = "highlight";
                    if (thought.includes("Spectra confirms")) p.className = "success";
                    if (thought.includes("Spectra suggested")) p.className = "warning";

                    thoughtLog.appendChild(p);
                });
                // Scroll to bottom
                thoughtLog.scrollTop = thoughtLog.scrollHeight;
            }

            const { q, r } = data.move;
            if (isPlayableCell(q, r) && !hasWall(q, r) && (q !== pigPos.q || r !== pigPos.r)) {
                walls.push({ q, r });
                wallsPlacedCount++;

                updateUI();
                drawBoard();

                if (!checkGameOver()) {
                    if (wallsPlacedCount >= 3) {
                        turn = 'PIG';
                        setTimeout(pigTurn, 500);
                    } else {
                        turn = 'PLAYER';
                        updateUI();
                    }
                }
            }
        } else {
            alert("AI couldn't find a move!");
        }
    } catch (err) {
        console.error(err);
        alert("Error connecting to AI server.");
    } finally {
        aiMoveBtn.innerHTML = 'Ask AI for Best Move';
        aiMoveBtn.disabled = false;
    }
});

resetBtn.addEventListener('click', resetGame);
overlayResetBtn.addEventListener('click', resetGame);

// =======================
// Auto Complete Feature
// =======================
const autoCompleteBtn = document.getElementById('autoCompleteBtn');
let isAutoPlaying = false;

async function autoPlayStep() {
    if (isGameOver || !isAutoPlaying) {
        stopAutoPlay();
        return;
    }

    if (turn !== 'PLAYER') {
        // Wait for pig's turn to complete
        setTimeout(autoPlayStep, 300);
        return;
    }

    const phase = wallsPlacedCount < 3 ? 'OPENING' : 'MAIN';

    try {
        const response = await fetch('/api/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pig_pos: pigPos, walls: walls, phase: phase })
        });

        const data = await response.json();

        if (data.move && isAutoPlaying) {
            // Display Thoughts
            const thoughtLog = document.getElementById('thoughtLog');
            thoughtLog.innerHTML = '';

            if (data.thoughts && data.thoughts.length > 0) {
                data.thoughts.forEach(thought => {
                    const p = document.createElement('p');
                    p.textContent = `> ${thought}`;
                    if (thought.includes("computed") || thought.includes("Decision")) p.className = "highlight";
                    if (thought.includes("ShadowProver")) p.className = "success";
                    thoughtLog.appendChild(p);
                });
                thoughtLog.scrollTop = thoughtLog.scrollHeight;
            }

            const { q, r } = data.move;
            if (isPlayableCell(q, r) && !hasWall(q, r) && (q !== pigPos.q || r !== pigPos.r)) {
                walls.push({ q, r });
                wallsPlacedCount++;

                updateUI();
                drawBoard();

                if (!checkGameOver() && isAutoPlaying) {
                    if (wallsPlacedCount >= 3) {
                        turn = 'PIG';
                        // Let pig move, then continue auto-play
                        setTimeout(() => {
                            pigTurn();
                            // Schedule next auto-play step after pig finishes
                            setTimeout(autoPlayStep, 800);
                        }, 500);
                    } else {
                        turn = 'PLAYER';
                        updateUI();
                        // Continue during opening phase (faster)
                        setTimeout(autoPlayStep, 300);
                    }
                } else {
                    stopAutoPlay();
                }
            } else {
                stopAutoPlay();
            }
        } else {
            stopAutoPlay();
        }
    } catch (err) {
        console.error(err);
        stopAutoPlay();
    }
}

function startAutoPlay() {
    if (isGameOver) {
        resetGame();
    }
    isAutoPlaying = true;
    autoCompleteBtn.innerHTML = 'Stop Auto Play';
    autoCompleteBtn.classList.add('active');
    aiMoveBtn.disabled = true;
    resetBtn.disabled = true;
    autoPlayStep();
}

function stopAutoPlay() {
    isAutoPlaying = false;
    autoCompleteBtn.innerHTML = 'Auto Complete Game';
    autoCompleteBtn.classList.remove('active');
    aiMoveBtn.disabled = false;
    resetBtn.disabled = false;
}

autoCompleteBtn.addEventListener('click', () => {
    if (isAutoPlaying) {
        stopAutoPlay();
    } else {
        startAutoPlay();
    }
});

// Init
resetGame();
