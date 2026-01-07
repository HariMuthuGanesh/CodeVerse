// DSA Phase 2 Controller (Option B Strict)
// Handles BST Game, RB Challenge, Tree Detective (Extra), Timer, and API interactions

let phase2Timer = null;
let timeRemaining = 900; // Default 15m
let phaseStartedAt = null; // Date object
let serverOffset = 0; // ms difference (server - client)

document.addEventListener('DOMContentLoaded', async () => {
    await initPhase2();
    initDragAndDrop();
});

async function initPhase2() {
    try {
        // Use sync endpoint to get authoritative state including started_at
        const res = await fetch('/api/phase2/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}) // Empty body just to fetch/start
        });
        const data = await res.json();

        // 1. Handle Completion / Lock
        if (data.completed) {
            lockPhase();
            document.getElementById('phase2-timer').textContent = "00:00";
            return;
        }

        // 2. Setup Timer (Server Authoritative)
        if (data.started_at) {
            // Calculate offset if possible, or just rely on UTC strings
            const serverStart = new Date(data.started_at.endsWith('Z') ? data.started_at : data.started_at + 'Z');
            phaseStartedAt = serverStart;

            // Initial sync
            updateTimerLogic();
            startTimer();
        }

        // 3. Restore State
        if (data.state) {
            restoreStates(
                data.state.bst_state,
                data.state.rb_state,
                data.state.detective_state
            );

            // Restore Scores
            const scores = data.state;
            const total = (scores.bst_score || 0) + (scores.rb_score || 0) + (scores.detective_score || 0);
            updateScoreDisplay(total);
        }

    } catch (e) {
        console.error("Init Error", e);
    }
}

function startTimer() {
    if (phase2Timer) clearInterval(phase2Timer);
    phase2Timer = setInterval(() => {
        const active = updateTimerLogic();

        // Autosave every 15s (approx, based on remaining time modulo)
        // or just use a separate interval. 
        // Using modulo on timeRemaining is risky if time sync jumps.
        // Better: separate interval or counter.
        if (active && timeRemaining % 15 === 0) {
            saveState(true); // Autosave
        }

        if (!active) {
            clearInterval(phase2Timer);
            finishRound(true);
        }
    }, 1000);
}

function updateTimerLogic() {
    if (!phaseStartedAt) return false;

    const now = new Date();
    // Assuming client time is relatively synced or we accept drift for display.
    // Server enforces the real limit.
    const diff = (now - phaseStartedAt) / 1000; // seconds
    const remaining = 900 - Math.floor(diff);

    timeRemaining = Math.max(0, remaining);
    updateTimerDisplay();

    // Autosave check (e.g., every 15s check if we haven't saved recently?)
    // Actually, we can just rely on the setInterval for a heartbeat if needed
    // But Drag-Drop triggers save, so only time sync is needed here.

    return timeRemaining > 0;
}

function updateTimerDisplay() {
    const mins = Math.floor(timeRemaining / 60);
    const secs = timeRemaining % 60;
    const el = document.getElementById('phase2-timer');
    if (el) {
        el.textContent = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
        if (timeRemaining < 60) el.classList.add('warning');
    }
}

function lockPhase() {
    // Disable all interactions
    document.body.classList.add('phase-locked');
    const modal = document.getElementById('result-modal');
    if (modal) {
        document.getElementById('result-title').textContent = "Phase Locked";
        document.getElementById('result-msg').textContent = "Time is up or you have completed this phase.";
        modal.classList.add('active');
    }
    // Disable DRAG
    document.querySelectorAll('.draggable').forEach(d => d.draggable = false);
}

// --- STATE MANAGEMENT ---

let saveTimeout = null;
function requestAutoSave() {
    // Debounce save
    if (saveTimeout) clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
        saveState(true); // Save to DB
    }, 2000); // 2 second debounce for DB writes
}

async function saveState(saveToDb = false) {
    // Capture state from DOM
    const bstState = captureBoardState('bst');
    const rbState = captureBoardState('rb');
    const detectiveState = captureBoardState('detective');

    // Also capture current local scores to persist in state?
    // Actually scores are updated via specific endpoints, but we should make sure state doesn't wipe them.
    // The specific endpoints update the state scores.
    // This payload updates the BOARD state.
    // BEWARE: If we send {bst_score: 0} here it might overwrite.
    // The sync endpoint merges keys. So we should NOT send 'bst_score' here unless we know it.
    // Better: Only send header/board state here.

    const statePayload = {
        bst_state: bstState,
        rb_state: rbState,
        detective_state: detectiveState,
    };

    const payload = {
        state: statePayload,
        save_to_db: saveToDb
    };

    try {
        if (navigator.sendBeacon && saveToDb) {
            const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
            navigator.sendBeacon('/api/phase2/sync', blob);
        } else {
            // Fire and forget usually, but await if needed
            const res = await fetch('/api/phase2/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            // Check if server says time up
            const d = await res.json();
            if (d.completed) {
                lockPhase();
            }
        }
    } catch (e) {
        console.error("Save Error", e);
    }
}

function captureBoardState(prefix) {
    const state = [];

    if (prefix === 'rb') {
        // Capture fixed nodes
        document.querySelectorAll('.rb-node').forEach(node => {
            state.push({
                id: node.id,
                color: node.style.backgroundColor || 'black'
            });
        });
        return state;
    }

    // Check Slots (BST / Detective)
    for (let i = 1; i <= 7; i++) {
        const slot = document.getElementById(`${prefix}-slot-${i}`);
        if (slot && slot.children.length > 0) {
            const el = slot.children[0];
            state.push({
                slot: i,
                value: el.dataset.value,
                color: el.dataset.color || null,
                id: el.id
            });
        }
    }
    // Detective: Items in Bank vs Slot?
    // We only save SLOTTED items. Bank items are re-generated or found.
    return state;
}

function restoreStates(bstState, rbState, detectiveState) {
    if (bstState && bstState.length > 0) restoreBoard('bst', bstState);
    if (rbState && rbState.length > 0) restoreBoard('rb', rbState);

    if (detectiveState && detectiveState.length > 0) {
        restoreBoard('detective', detectiveState);
    } else {
        initBrokenTree();
    }
}

function restoreBoard(prefix, state) {
    if (prefix === 'rb') {
        state.forEach(item => {
            const node = document.getElementById(item.id);
            if (node) {
                node.style.backgroundColor = item.color;
                // Update text color for contrast if white/black logic is simple
                // Text is white, if BG is white?? No, Red/Black. 
                // Red BG -> White Text. Black BG -> White Text.
            }
        });
        return;
    }

    // Clear slots first?
    for (let i = 1; i <= 7; i++) {
        const slot = document.getElementById(`${prefix}-slot-${i}`);
        if (slot) slot.innerHTML = '';
    }

    state.forEach(item => {
        const slot = document.getElementById(`${prefix}-slot-${item.slot}`);
        let draggable = document.getElementById(item.id);

        // If not found (Detective generated items), we might need to recreate or find in bank
        if (!draggable) {
            draggable = document.querySelector(`.draggable[data-value="${item.value}"]`);
        }

        // For Detective Initial Broken tree, nodes are created by initBrokenTree.
        // If we have state, we might need to find them or create them.
        // Simplest: If ID exists, move it.

        if (draggable && slot) {
            slot.appendChild(draggable);
        }
    });
}


// --- DRAG AND DROP ---

function initDragAndDrop() {
    const draggables = document.querySelectorAll('.draggable');
    const dropzones = document.querySelectorAll('.dropzone');
    const banks = document.querySelectorAll('.bank-container');

    draggables.forEach(d => {
        const newD = d.cloneNode(true);
        d.parentNode.replaceChild(newD, d);

        newD.addEventListener('dragstart', e => {
            newD.classList.add('dragging');
            e.dataTransfer.setData('text/plain', newD.id);
            e.dataTransfer.effectAllowed = 'move';
        });
        newD.addEventListener('dragend', () => {
            newD.classList.remove('dragging');
            requestAutoSave(); // Save on move
        });
    });

    const allZones = [...dropzones, ...banks];
    allZones.forEach(zone => {
        zone.ondragover = e => {
            e.preventDefault();
            if (zone.classList.contains('dropzone')) zone.classList.add('hovered');
        };
        zone.ondragleave = () => {
            if (zone.classList.contains('dropzone')) zone.classList.remove('hovered');
        };
        zone.ondrop = e => {
            e.preventDefault();
            if (zone.classList.contains('dropzone')) zone.classList.remove('hovered');

            const id = e.dataTransfer.getData('text/plain');
            const draggingItem = document.getElementById(id);
            if (!draggingItem) return;

            if (zone.classList.contains('dropzone')) {
                if (zone.children.length === 0) {
                    zone.appendChild(draggingItem);
                } else {
                    // Swap
                    const existing = zone.children[0];
                    const originalParent = draggingItem.parentNode;
                    zone.appendChild(draggingItem);
                    originalParent.appendChild(existing);
                }
            } else if (zone.classList.contains('bank-container')) {
                // Check correct bank
                if ((zone.id === 'bst-bank' && draggingItem.closest('#challenge-bst')) ||
                    (zone.id === 'detective-bank' && draggingItem.closest('#challenge-detective'))) {
                    zone.appendChild(draggingItem);
                }
            }
            // Logic handled by dragend listener
        };
    });
}

// --- GAME LOGIC ---

async function validateBST() {
    const result = DSATree.validateBSTFromUI('bst');
    if (result.valid) {
        displayResult("Correct!", "BST Logic Verified.", true);
        await helpers.submitBST(true);
    } else {
        displayResult("Invalid", result.error, false);
        await helpers.submitBST(false);
    }
}

async function validateDetective() {
    const result = DSATree.validateBSTFromUI('detective');
    if (result.valid) {
        displayResult("Fixed!", "Detective Challenge Complete.", true);
        await helpers.submitDetective(true);
    } else {
        displayResult("Incorrect", result.error, false);
        await helpers.submitDetective(false);
    }
}

async function validateRB() {
    const result = DSATree.validateRBFromUI();
    if (result.valid) {
        displayResult("Correct!", "Red-Black Tree Verified.", true);
        await helpers.completeRB();
    } else {
        displayResult("Invalid", result.error, false);
    }
}

async function pauseGame() {
    // Just save and show modal
    await saveState(true);
    document.getElementById('pause-modal').classList.add('active');
}

function resumeGame() {
    document.getElementById('pause-modal').classList.remove('active');
    // Timer keeps running in background (server time), so we just resume UI updates
    updateTimerLogic();
}

async function saveAndExit() {
    await saveState(true);
    window.location.href = 'phases.html';
}

function finishRound(auto = false) {
    if (auto) {
        confirmExit();
    } else {
        document.getElementById('confirm-modal').classList.add('active');
    }
}

function closeConfirm() {
    document.getElementById('confirm-modal').classList.remove('active');
}

async function confirmExit() {
    await saveState(true); // Final State Save
    await fetch('/api/phase2/exit', { method: 'POST' });
    window.location.href = 'phases.html';
}

function displayResult(title, msg, success) {
    const m = document.getElementById('result-modal');
    document.getElementById('result-title').textContent = title;
    document.getElementById('result-msg').textContent = msg;
    document.getElementById('result-title').style.color = success ? 'var(--accent-avengers)' : 'var(--accent-red-bright)';

    // Add close button
    const actionArea = document.getElementById('action-area');
    if (actionArea) {
        actionArea.innerHTML = `<button class="btn-action" onclick="document.getElementById('result-modal').classList.remove('active')">CONTINUE</button>`;
    }

    m.classList.add('active');
}

function updateScoreDisplay(str) {
    document.getElementById('score-display').textContent = `Phase 2 Score: ${str}`;
}

const helpers = {
    submitBST: async (correct) => {
        const res = await fetch('/api/bst/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ correct })
        });
        const d = await res.json();
        if (d.success) updateScoreDisplay(d.total_phase2_score || d.score); // Handler
    },
    submitDetective: async (correct) => {
        const res = await fetch('/api/detective/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ correct })
        });
        const d = await res.json();
        if (d.success) updateScoreDisplay(d.total_phase2_score || d.score);
    },
    completeRB: async () => {
        const res = await fetch('/api/rb/complete', { method: 'POST' });
        const d = await res.json();
        if (d.success) updateScoreDisplay(d.total_phase2_score || d.score);
    }
};

function showChallenge(type) {
    document.querySelectorAll('.challenge-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.challenge-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`tab-${type}`).classList.add('active');
    document.getElementById(`challenge-${type}`).classList.add('active');
}

// Logic for Broken Tree Init
function initBrokenTree() {
    const config = [
        { slot: 1, val: 50, id: 'd-node-50' },
        { slot: 2, val: 30, id: 'd-node-30' },
        { slot: 3, val: 70, id: 'd-node-70' },
        { slot: 4, val: 20, id: 'd-node-20' },
        { slot: 5, val: 60, id: 'd-node-60' }, // ERROR
        { slot: 6, val: 40, id: 'd-node-40' }, // ERROR
        { slot: 7, val: 80, id: 'd-node-80' }
    ];
    const bank = document.getElementById('detective-bank');
    if (bank) bank.innerHTML = '<p style="color: #666; font-size: 0.8rem; align-self: center;">Drag nodes here temporarily if needed</p>';

    config.forEach(c => {
        const div = document.createElement('div');
        div.className = 'draggable';
        div.draggable = true;
        div.dataset.value = c.val;
        div.textContent = c.val;
        div.id = c.id;
        div.style.background = 'var(--accent-red-bright)'; // Visual difference
        div.style.boxShadow = '0 0 5px red';

        const slot = document.getElementById(`detective-slot-${c.slot}`);
        if (slot) slot.appendChild(div);
    });
}
function toggleColor(el) {
    if (document.body.classList.contains('phase-locked')) return;

    // Toggle between black and red
    // Default in HTML is style="background:black;"
    const currentColor = el.style.backgroundColor;
    if (currentColor === 'black' || currentColor === '') {
        el.style.backgroundColor = '#AA0000'; // Red
        el.style.borderColor = 'white';
    } else {
        el.style.backgroundColor = 'black';
        el.style.borderColor = 'white';
    }
    requestAutoSave();
}
