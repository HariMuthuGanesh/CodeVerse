// DSA Phase 2 Controller
// Handles BST Game, RB Challenge, Tree Detective (Extra), Timer, and API interactions

let phase2Timer = null;
let timeRemaining = 600;

document.addEventListener('DOMContentLoaded', async () => {
    await initPhase2();
    initDragAndDrop();
});

async function initPhase2() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();

        // Check if finished
        if (data.phase2_details && data.phase2_details.bst && data.phase2_details.bst.status === 'exited') {
            window.location.href = '/phases.html';
            return;
        }

        // Restore Time
        timeRemaining = data.phase2_details.time_remaining || 600;
        updateTimerDisplay();
        startTimer();

        // Restore Score Display
        const phase2Score = data.phase2_score || 0;
        document.getElementById('score-display').textContent = `Phase 2 Score: ${phase2Score}`;

        // Restore Node States
        restoreStates(
            data.phase2_details.bst.state,
            data.phase2_details.rb.state,
            data.phase2_details.detective.state
        );

    } catch (e) {
        console.error("Init Error", e);
    }
}

function startTimer() {
    if (phase2Timer) clearInterval(phase2Timer);
    phase2Timer = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();

        if (timeRemaining % 10 === 0) saveState(false); // Autosave every 10s

        if (timeRemaining <= 0) {
            clearInterval(phase2Timer);
            finishRound(true); // Auto finish
        }
    }, 1000);
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

// --- STATE MANAGEMENT ---

async function saveState(saveToDb = false) {
    // Capture state from DOM
    const bstState = captureBoardState('bst');
    const rbState = captureBoardState('rb');
    const detectiveState = captureBoardState('detective');

    const payload = {
        time_remaining: timeRemaining,
        bst_state: bstState,
        rb_state: rbState,
        detective_state: detectiveState,
        save_to_db: saveToDb
    };

    try {
        if (navigator.sendBeacon && saveToDb) {
            const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
            navigator.sendBeacon('/api/phase2/sync', blob);
        } else {
            await fetch('/api/phase2/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }
    } catch (e) {
        console.error("Save Error", e);
    }
}

function captureBoardState(prefix) {
    const state = [];
    // Check Slots
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
    // Also capture bank? No, items always start in bank if not in slot logic fails. 
    // Wait, for Detective, items might be moving around.
    // If an item is NOT in a slot, it's in the bank. We don't need to persist bank position explicitly if we just reset unslotted items to bank.
    return state;
}

function restoreStates(bstState, rbState, detectiveState) {
    // BST
    if (bstState && bstState.length > 0) {
        restoreBoard('bst', bstState);
    }

    // RB
    if (rbState && rbState.length > 0) {
        restoreBoard('rb', rbState);
    }

    // Detective
    if (detectiveState && detectiveState.length > 0 && detectiveState.some(x => x.slot)) {
        restoreBoard('detective', detectiveState);
    } else {
        // Initialize Detective "Broken" Tree Default
        initBrokenTree();
    }
}

function restoreBoard(prefix, state) {
    state.forEach(item => {
        const slot = document.getElementById(`${prefix}-slot-${item.slot}`);
        // Find element
        let draggable = null;

        // For Detective, IDs are unique generated.
        // If we can't find by ID (first load), try value.
        draggable = document.getElementById(item.id) ||
            document.querySelector(`#${prefix}-bank .draggable[data-value="${item.value}"]`) ||
            document.querySelector(`.draggable[data-value="${item.value}"]`); // fallback

        if (draggable && slot) {
            slot.appendChild(draggable);
        }
    });
}

// --- ACTIONS ---

async function pauseGame() {
    // Stop Timer
    clearInterval(phase2Timer);
    phase2Timer = null; // Ensure null logic works

    // Open Modal
    document.getElementById('pause-modal').classList.add('active');

    // Save State (without exit) - Beacon or Async?
    // User expects "Paused". Saving is good practice.
    await saveState(true);
}

function resumeGame() {
    // Close Modal
    document.getElementById('pause-modal').classList.remove('active');

    // Resume Timer
    startTimer();
}

async function saveAndExit() {
    await saveState(true);
    window.location.href = 'phases.html';
}

// ... (keep validateBST etc) ...

// Updated Broken Tree (Deep Violations)
function initBrokenTree() {
    // Detective Hard Mode: Deep Violations
    // Correct Tree: 
    //        50
    //    30      70
    //  20  40   60  80

    // Broken Tree: Swap 40 (Left-Right) and 60 (Right-Left)
    // 60 is placed at Slot 5 (Child of 30). 60 > 30 OK. But 60 > 50 (Root) -> VIOLATION (Deep).
    // 40 is placed at Slot 6 (Child of 70). 40 < 70 OK. But 40 < 50 (Root) -> VIOLATION (Deep).

    const config = [
        { slot: 1, val: 50, id: 'd-node-50' },
        { slot: 2, val: 30, id: 'd-node-30' },
        { slot: 3, val: 70, id: 'd-node-70' },

        { slot: 4, val: 20, id: 'd-node-20' }, // Correct
        { slot: 5, val: 60, id: 'd-node-60' }, // ERROR: 60 > 30 (OK locally), but > 50 (Global Fail)

        { slot: 6, val: 40, id: 'd-node-40' }, // ERROR: 40 < 70 (OK locally), but < 50 (Global Fail)
        { slot: 7, val: 80, id: 'd-node-80' }  // Correct
    ];

    const bank = document.getElementById('detective-bank');
    bank.innerHTML = '<p style="color: #666; font-size: 0.8rem; align-self: center;">Drag nodes here temporarily if needed</p>'; // Reset + Hint

    config.forEach(c => {
        const div = document.createElement('div');
        div.className = 'draggable';
        div.draggable = true;
        div.dataset.value = c.val;
        div.textContent = c.val;
        div.id = c.id;
        div.style.background = 'var(--accent-red-bright)'; // Visual difference
        div.style.boxShadow = '0 0 5px red';

        // Place in slot
        const slot = document.getElementById(`detective-slot-${c.slot}`);
        if (slot) slot.appendChild(div);
    });
}

// --- DRAG AND DROP LOGIC (Global) ---

function initDragAndDrop() {
    // Re-select all
    const draggables = document.querySelectorAll('.draggable');
    const dropzones = document.querySelectorAll('.dropzone');
    const banks = document.querySelectorAll('.bank-container');

    draggables.forEach(d => {
        // Remove old listeners to avoid duplicates if re-run
        const newD = d.cloneNode(true);
        d.parentNode.replaceChild(newD, d);

        newD.addEventListener('dragstart', e => {
            newD.classList.add('dragging');
            e.dataTransfer.setData('text/plain', newD.id);
            e.dataTransfer.effectAllowed = 'move';
        });
        newD.addEventListener('dragend', () => {
            newD.classList.remove('dragging');
        });
    });

    const allZones = [...dropzones, ...banks];

    allZones.forEach(zone => {
        // Simple dragover/leave/drop
        // Cloning zone removes children? No. But it removes listeners.
        // Be careful replacing zones if they have children.
        // Better: use a flag or ensure init only runs once per element.
        // For now, let's just add listeners and hope duplication isn't fatal (it usually fires twice).
        // Or strip all listeners.
        // Actually, 'initBrokenTree' creates NEW elements.
        // Let's just attach to document delegation or run specific logic for new nodes.

        // Simplified: Just add to everything.
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

            // Logic
            if (zone.classList.contains('dropzone')) {
                if (zone.children.length === 0) {
                    zone.appendChild(draggingItem);
                } else {
                    // Swap?
                    // Yes, useful for Detective.
                    const existing = zone.children[0];
                    const originalParent = draggingItem.parentNode;

                    zone.appendChild(draggingItem);
                    originalParent.appendChild(existing);
                }
            } else if (zone.classList.contains('bank-container')) {
                if (zone.id === 'bst-bank' && draggingItem.closest('#challenge-bst')) zone.appendChild(draggingItem);
                if (zone.id === 'rb-bank' && draggingItem.closest('#challenge-rb')) zone.appendChild(draggingItem);
                if (zone.id === 'detective-bank' && draggingItem.closest('#challenge-detective')) zone.appendChild(draggingItem);
            }
        };
    });
}


// --- ACTIONS ---

async function validateBST() {
    const result = DSATree.validateBSTFromUI('bst'); // Updated to support prefix
    if (result.valid) {
        displayResult("Correct!", "The Timeline is secure. Valid BST constructed.", true);
        await helpers.submitBST(true);
    } else {
        displayResult("Invalid BST", result.error, false);
        await helpers.submitBST(false);
    }
}

async function validateDetective() {
    // Reuse BST Logic but with 'detective' prefix
    const result = DSATree.validateBSTFromUI('detective');

    if (result.valid) {
        displayResult("Correct!", "Sabotage Repaired. System Online.", true);
        await helpers.submitDetective(true);
    } else {
        displayResult("Incorrect Fix", "The tree is still invalid: " + result.error, false);
        await helpers.submitDetective(false);
    }
}

async function validateRB() {
    const result = DSATree.validateRBFromUI(); // RB likely handles its own ids
    if (result.valid) {
        displayResult("Correct!", "Red-Black Tree Integrity Verified.", true);
        await helpers.completeRB();
    } else {
        displayResult("Invalid RB Tree", result.error, false);
    }
}

// pauseGame, resumeGame etc are defined above.
// Legacy pauseAndLeave removed.

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
    await saveState(true);
    await fetch('/api/phase2/exit', { method: 'POST' });
    window.location.href = 'phases.html';
}

function displayResult(title, msg, success) {
    const m = document.getElementById('result-modal');
    document.getElementById('result-title').textContent = title;
    document.getElementById('result-msg').textContent = msg;
    document.getElementById('result-title').style.color = success ? 'var(--accent-avengers)' : 'var(--accent-red-bright)';

    const area = document.getElementById('action-area');
    area.innerHTML = `<button class="btn-action" onclick="document.getElementById('result-modal').classList.remove('active')">CLOSE</button>`;

    m.classList.add('active');
}


// --- API HELPERS ---
const helpers = {
    submitBST: async (correct) => {
        const res = await fetch('/api/bst/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ correct })
        });
        const d = await res.json();
        if (d.success) {
            document.getElementById('score-display').textContent = `Phase 2 Score: ${d.total_phase2_score}`;
        }
    },
    submitDetective: async (correct) => {
        const res = await fetch('/api/detective/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ correct })
        });
        const d = await res.json();
        if (d.success) {
            document.getElementById('score-display').textContent = `Phase 2 Score: ${d.total_phase2_score}`;
        }
    },
    completeRB: async () => {
        const res = await fetch('/api/rb/complete', { method: 'POST' });
        const d = await res.json();
        if (d.success) {
            document.getElementById('score-display').textContent = `Phase 2 Score: ${d.total_phase2_score}`;
        }
    }
};

// --- NAVIGATION ---
function showChallenge(type) {
    document.querySelectorAll('.challenge-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.challenge-content').forEach(c => c.classList.remove('active'));

    document.getElementById(`tab-${type}`).classList.add('active');
    document.getElementById(`challenge-${type}`).classList.add('active');
}
