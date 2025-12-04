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

// Game State
const RADIUS = 5; // Updated to 5
const HEX_SIZE = 25; // Smaller hexes for larger grid
const CENTER_X = canvas.width / 2;
const CENTER_Y = canvas.height / 2;

let pigPos = { q: 0, r: 0 };
let walls = [];
let turn = 'PLAYER'; // 'PLAYER' or 'PIG'
let isGameOver = false;
let wallsPlacedCount = 0; // Track player moves

// Hex Utilities
function hexToPixel(q, r) {
    const x = HEX_SIZE * (3 / 2 * q);
    const y = HEX_SIZE * (Math.sqrt(3) / 2 * q + Math.sqrt(3) * r);
    return { x: x + CENTER_X, y: y + CENTER_Y };
}

function pixelToHex(x, y) {
    const q = (2 / 3 * (x - CENTER_X)) / HEX_SIZE;
    const r = ((-1 / 3 * (x - CENTER_X) + Math.sqrt(3) / 3 * (y - CENTER_Y))) / HEX_SIZE;
    return hexRound(q, r);
}

function hexRound(q, r) {
    let s = -q - r;
    let rq = Math.round(q);
    let rr = Math.round(r);
    let rs = Math.round(s);

    const q_diff = Math.abs(rq - q);
    const r_diff = Math.abs(rr - r);
    const s_diff = Math.abs(rs - s);

    if (q_diff > r_diff && q_diff > s_diff) {
        rq = -rr - rs;
    } else if (r_diff > s_diff) {
        rr = -rq - rs;
    }
    return { q: rq, r: rr };
}

function getNeighbors(q, r) {
    const directions = [
        { q: 1, r: 0 }, { q: 1, r: -1 }, { q: 0, r: -1 },
        { q: -1, r: 0 }, { q: -1, r: 1 }, { q: 0, r: 1 }
    ];
    return directions.map(d => ({ q: q + d.q, r: r + d.r }));
}

function isValidCell(q, r) {
    return Math.abs(q + r) <= RADIUS && Math.abs(q) <= RADIUS && Math.abs(r) <= RADIUS;
}

function isEscape(q, r) {
    return Math.abs(q) === RADIUS || Math.abs(r) === RADIUS || Math.abs(q + r) === RADIUS;
}

// Drawing
function drawHex(q, r, color, strokeColor = '#334155', lineWidth = 1) {
    const { x, y } = hexToPixel(q, r);
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
        const angle_deg = 60 * i;
        const angle_rad = Math.PI / 180 * angle_deg;
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

    // Draw Grid
    for (let q = -RADIUS; q <= RADIUS; q++) {
        for (let r = -RADIUS; r <= RADIUS; r++) {
            if (isValidCell(q, r)) {
                let color = '#1e293b'; // Default cell

                // Check if wall
                if (walls.some(w => w.q === q && w.r === r)) {
                    color = '#64748b';
                }

                drawHex(q, r, color);
            }
        }
    }

    // Draw Pig
    drawHex(pigPos.q, pigPos.r, '#ec4899', '#be185d', 3);

    // Draw "P" text
    const { x, y } = hexToPixel(pigPos.q, pigPos.r);
    ctx.fillStyle = 'white';
    ctx.font = 'bold 16px Outfit';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('🐷', x, y);
}

// Game Logic
function checkGameOver() {
    // 1. Pig Escaped?
    if (isEscape(pigPos.q, pigPos.r)) {
        endGame(false, "The Pig Escaped!");
        return true;
    }

    // 2. Pig Trapped?
    // BFS to see if ANY escape is reachable
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
            if (isValidCell(n.q, n.r) && !visited.has(key) && !walls.some(w => w.q === n.q && w.r === n.r)) {
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
    pigPos = { q: 0, r: 0 };
    walls = [];
    turn = 'PLAYER';
    isGameOver = false;
    wallsPlacedCount = 0;

    // Generate Random Walls (5-15)
    const numWalls = Math.floor(Math.random() * 11) + 5;
    for (let i = 0; i < numWalls; i++) {
        let valid = false;
        while (!valid) {
            let q = Math.floor(Math.random() * (2 * RADIUS + 1)) - RADIUS;
            let r = Math.floor(Math.random() * (2 * RADIUS + 1)) - RADIUS;

            if (isValidCell(q, r) && (q !== 0 || r !== 0) && !walls.some(w => w.q === q && w.r === r)) {
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

// Interaction
canvas.addEventListener('click', (e) => {
    if (isGameOver || turn !== 'PLAYER') return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const hex = pixelToHex(x, y);

    if (isValidCell(hex.q, hex.r)) {
        // Check if empty
        if (hex.q === pigPos.q && hex.r === pigPos.r) return;
        if (walls.some(w => w.q === hex.q && w.r === hex.r)) return;

        // Place Wall
        walls.push(hex);
        wallsPlacedCount++;

        updateUI();
        drawBoard();

        if (!checkGameOver()) {
            // Check Phase
            if (wallsPlacedCount >= 3) {
                turn = 'PIG';
                setTimeout(pigTurn, 500);
            } else {
                // Still Opening Phase, Player keeps turn
                turn = 'PLAYER';
                updateUI();
            }
        }
    }
});

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
            // Found shortest path!
            // Move is the first step in path
            if (path.length > 0) {
                bestMove = path[0];
            } else {
                // Already at escape (should be caught by checkGameOver)
                bestMove = pos;
            }
            break;
        }

        let neighbors = getNeighbors(pos.q, pos.r);
        // Randomize neighbors for variety in tie-breaking
        neighbors.sort(() => Math.random() - 0.5);

        for (let n of neighbors) {
            let key = `${n.q},${n.r}`;
            if (isValidCell(n.q, n.r) && !visited.has(key) && !walls.some(w => w.q === n.q && w.r === n.r)) {
                visited.add(key);
                let newPath = [...path, n];
                queue.push({ pos: n, path: newPath });
            }
        }
    }

    if (bestMove) {
        pigPos = bestMove;
    } else {
        // No path to escape? Move randomly to a free neighbor (stalling)
        const neighbors = getNeighbors(pigPos.q, pigPos.r);
        const validMoves = neighbors.filter(n =>
            isValidCell(n.q, n.r) && !walls.some(w => w.q === n.q && w.r === n.r)
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

// AI Integration
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
            // Execute AI Move
            walls.push(data.move);
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
        } else {
            alert("AI couldn't find a move!");
        }
    } catch (err) {
        console.error(err);
        alert("Error connecting to AI server.");
    } finally {
        aiMoveBtn.innerHTML = '<span class="icon">✨</span> Ask AI for Best Move';
        aiMoveBtn.disabled = false;
    }
});

resetBtn.addEventListener('click', resetGame);
overlayResetBtn.addEventListener('click', resetGame);

// Init
resetGame();
