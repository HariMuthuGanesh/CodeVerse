// DSA Phase 2 Controller (Option B Strict)
// Handles BST Game, RB Challenge, Tree Detective (Extra), and API interactions
// Timer removed - unlimited time

document.addEventListener('DOMContentLoaded', async () => {
    await initPhase2();
    initDragAndDrop();
    initRBColorDragDrop();
});

async function initPhase2() {
    try {
        // Use sync endpoint to get authoritative state
        const res = await fetch('/api/phase2/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}) // Empty body just to fetch/start
        });
        const data = await res.json();

        // 1. Handle Completion / Lock
        if (data.completed) {
            lockPhase();
            return;
        }

        // 2. Restore State (no timer logic)
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

// Timer functions removed - unlimited time

function lockPhase() {
    // Disable all interactions
    document.body.classList.add('phase-locked');
    const modal = document.getElementById('result-modal');
    if (modal) {
        document.getElementById('result-title').textContent = "Phase Locked";
        document.getElementById('result-msg').textContent = "Time is up or you have completed this phase.";
        modal.classList.add('active');

        // Remove Action Area buttons to prevent clicking "Continue"
        const actionArea = document.getElementById('action-area');
        if (actionArea) actionArea.innerHTML = '';
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
        saveState();
    }, 2000);
}

async function saveState() {
    // Capture state from DOM
    const bstState = captureBoardState('bst');
    const rbState = captureBoardState('rb');
    const detectiveState = captureBoardState('detective');

    const statePayload = {
        bst_state: bstState,
        rb_state: rbState,
        detective_state: detectiveState,
    };

    const payload = {
        state: statePayload
    };

    try {
        // Fire and forget usually, but await if needed
        const res = await fetch('/api/phase2/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const d = await res.json();
        if (d.completed) {
            lockPhase();
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
            }
        });
        return;
    }

    // Clear slots first
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
            if (!draggable) {
                // Should exist but just in case
                return;
            }
        }

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
        // Avoid adding multiple listeners if re-init
        // Clone to clear listeners
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
        };
    });
}

// --- GAME LOGIC ---

async function validateBST() {
    // Client Side Check (Fast Feedback)
    // Optional: we can remove this and rely purely on server, but good UX to show "Analysing..."
    // Let's rely on server for the authoritative check.

    // We still use client text to show "Verifying..."
    displayResult("Verifying...", "Analyzing Temporal structure...", true);
    document.getElementById('action-area').innerHTML = ''; // Hide buttons while loading

    await helpers.submitBST(); // Sends state
}

async function validateDetective() {
    displayResult("Verifying...", "Analyzing Anomalies...", true);
    document.getElementById('action-area').innerHTML = '';
    await helpers.submitDetective();
}

async function validateRB() {
    displayResult("Verifying...", "Checking Quantum Stability...", true);
    document.getElementById('action-area').innerHTML = '';
    await helpers.completeRB();
}

async function pauseGame() {
    await saveState();
    document.getElementById('pause-modal').classList.add('active');
}

function resumeGame() {
    document.getElementById('pause-modal').classList.remove('active');
    // Timer removed - unlimited time
}

async function saveAndExit() {
    await saveState();
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
    await saveState(); // Final State Save
    
    // CRITICAL: Get phase completion status from API response (DB-driven)
    try {
        const res = await fetch('/api/phase2/exit', { method: 'POST' });
        const data = await res.json();
        
        if (data.success) {
            // Phase 3 is now unlocked - this comes from Supabase, not localStorage
            console.log('[PHASE2] Phase 2 completed, Phase 3 unlocked from DB:', {
                phase2_completed: data.phase2_completed,
                phase3_completed: data.phase3_completed
            });
        } else {
            console.error('[PHASE2] Exit failed:', data.error);
            alert('Failed to complete Phase 2: ' + (data.error || 'Unknown error'));
            return;
        }
    } catch (error) {
        console.error('[PHASE2] Exit error:', error);
        alert('Error completing Phase 2. Please try again.');
        return;
    }
    
    window.location.href = 'phases.html';
}

function displayResult(title, msg, success) {
    const m = document.getElementById('result-modal');
    const tEl = document.getElementById('result-title');
    const mEl = document.getElementById('result-msg');

    tEl.textContent = title;
    mEl.textContent = msg;
    tEl.style.color = success ? 'var(--accent-avengers)' : 'var(--accent-red-bright)';

    // Add close button if not locked
    const actionArea = document.getElementById('action-area');
    if (actionArea && !document.body.classList.contains('phase-locked')) {
        actionArea.innerHTML = `<button class="btn-action" onclick="document.getElementById('result-modal').classList.remove('active')">CONTINUE</button>`;
    }

    m.classList.add('active');
}

function updateScoreDisplay(val) {
    document.getElementById('score-display').textContent = `Phase 2 Score: ${val}`;
}

// --- HELPERS (API) ---

const helpers = {
    submitBST: async () => {
        // Collect Slots
        const slots = {};
        for (let i = 1; i <= 7; i++) {
            const slot = document.getElementById(`bst-slot-${i}`);
            if (slot && slot.children.length > 0) {
                slots[i] = parseInt(slot.children[0].dataset.value);
            }
        }

        const res = await fetch('/api/bst/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ slots: slots })
        });
        const d = await res.json();

        displayResult(d.valid ? "Correct!" : "Invalid Structure", d.message, d.valid);

        // Update total score from d.score (which is just this component score). 
        // We might want to fetch full score or just trust UI update?
        // Let's refetch sync to be safe or just trigger sync
        requestAutoSave();
        // Manually update UI score if we knew total, but sync will handle it or we can just update this part
        // The displayResult is mostly what matters.
    },

    submitDetective: async () => {
        const slots = {};
        for (let i = 1; i <= 7; i++) {
            const slot = document.getElementById(`detective-slot-${i}`);
            if (slot && slot.children.length > 0) {
                slots[i] = parseInt(slot.children[0].dataset.value);
            }
        }

        const res = await fetch('/api/detective/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ slots: slots })
        });
        const d = await res.json();

        displayResult(d.valid ? "Fixed!" : "Not Quite...", d.message, d.valid);
        requestAutoSave();
    },

    completeRB: async () => {
        // Collect Nodes - use data-color attribute for drag-and-drop
        const nodes = [];
        document.querySelectorAll('.rb-node').forEach(n => {
            const color = n.dataset.color || (n.style.backgroundColor.includes('AA0000') || n.style.backgroundColor.includes('red') ? 'red' : 'black');
            nodes.push({
                id: n.id, // rb-node-1
                color: color,
                value: parseInt(n.dataset.value)
            });
        });

        const res = await fetch('/api/rb/complete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nodes: nodes })
        });
        const d = await res.json();

        displayResult(d.valid ? "Stable!" : "Unstable", d.message, d.valid);
        requestAutoSave();
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
    // Only init if empty?
    const s1 = document.getElementById('detective-slot-1');
    if (s1 && s1.children.length > 0) return; // Already populated

    const config = [
        { slot: 1, val: 50, id: 'd-node-50' },
        { slot: 2, val: 30, id: 'd-node-30' },
        { slot: 3, val: 70, id: 'd-node-70' },
        { slot: 4, val: 20, id: 'd-node-20' },
        { slot: 5, val: 60, id: 'd-node-60' }, // ERROR: 60 > 50 (Root), should be right of 50. But it's in left subtree (child of 30, right child). 30->60. 60>30 ok. But 60 > 50 (grandparent). Violation!
        { slot: 6, val: 40, id: 'd-node-40' }, // ERROR: 40 < 50. In right subtree (child of 70). 70->40. 40<70 ok. But 40 < 50 (grandprant). Violation!
        { slot: 7, val: 80, id: 'd-node-80' }
    ];
    // This creates "Deep Violations" as requested.
    // 60 is right child of 30. Valid local (60>30). Invalid global (60 > 50, but in Left subtree).

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

// Red-Black Tree drag-and-drop color handling
function initRBColorDragDrop() {
    const colorBank = document.querySelectorAll('#challenge-rb .bank-container .draggable[data-color]');
    const rbNodes = document.querySelectorAll('.rb-node.dropzone');
    
    colorBank.forEach(colorEl => {
        colorEl.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', e.target.dataset.color);
            e.target.style.opacity = '0.5';
        });
        
        colorEl.addEventListener('dragend', (e) => {
            e.target.style.opacity = '1';
        });
    });
    
    rbNodes.forEach(node => {
        node.addEventListener('dragover', (e) => {
            e.preventDefault();
            node.style.border = '2px dashed var(--accent-avengers)';
        });
        
        node.addEventListener('dragleave', (e) => {
            node.style.border = '';
        });
        
        node.addEventListener('drop', (e) => {
            e.preventDefault();
            const color = e.dataTransfer.getData('text/plain');
            
            if (color === 'black') {
                node.style.backgroundColor = 'black';
                node.dataset.color = 'black';
            } else if (color === 'red') {
                node.style.backgroundColor = '#AA0000';
                node.dataset.color = 'red';
            }
            
            node.style.border = '';
            requestAutoSave();
        });
    });
}
