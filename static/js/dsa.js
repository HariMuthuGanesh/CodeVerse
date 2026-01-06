// DSA Phase 2 Controller
// Handles BST Game, RB Challenge, Timer, and API interactions

let bstRoot = null;
let currentQuestionIndex = 0;
let phase2Timer = null;
let timeRemaining = 600;

// BST Questions (Generated or Static)
const BST_QUESTIONS = [
    { type: 'insert', val: 50, text: "Insert Node 50" },
    { type: 'insert', val: 30, text: "Insert Node 30" },
    { type: 'insert', val: 70, text: "Insert Node 70" },
    { type: 'insert', val: 20, text: "Insert Node 20" },
    { type: 'insert', val: 40, text: "Insert Node 40" },
    { type: 'insert', val: 60, text: "Insert Node 60" },
    { type: 'insert', val: 80, text: "Insert Node 80" },
    { type: 'search', val: 40, text: "Search for Node 40" },
    { type: 'delete', val: 20, text: "Delete Node 20" },
    { type: 'inorder', val: null, text: "Verify Inorder Traversal" }
];

document.addEventListener('DOMContentLoaded', async () => {
    await initPhase2();
    initDragAndDrop(); // For RB
});

async function initPhase2() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();

        // Restore Time
        timeRemaining = data.phase2_details.time_remaining || 600;
        updateTimerDisplay();
        startTimer();

        // Restore BST Progress
        const bstState = data.phase2_details.bst;
        document.getElementById('score-display').textContent = `BST Score: ${bstState.score}`;

        // Restore Question Index (Approximation based on attempted)
        // Ideally we store 'current_question_index' in DB, but 'attempted' is a decent proxy if linear
        // If attempted = 0 -> Q0. If attempted = 1 -> Q1.
        currentQuestionIndex = bstState.attempted;

        // Rebuild Tree State? 
        // We don't store the tree structure, so we must replay questions to restore state.
        rebuildTreeUpTo(currentQuestionIndex);

        updateQuestionDisplay();

    } catch (e) {
        console.error("Init Error", e);
    }
}

function startTimer() {
    if (phase2Timer) clearInterval(phase2Timer);
    phase2Timer = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();

        if (timeRemaining % 10 === 0) saveTimer(false); // Autosave every 10s

        if (timeRemaining <= 0) {
            clearInterval(phase2Timer);
            finishRound();
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

async function saveTimer(async = true) {
    // Use beacon or fetch
    const payload = JSON.stringify({ time_remaining: timeRemaining });
    if (navigator.sendBeacon) {
        const blob = new Blob([payload], { type: 'application/json' });
        navigator.sendBeacon('/api/phase2/timer', blob);
    } else {
        await fetch('/api/phase2/timer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: payload
        });
    }
}

// --- BST GAME LOGIC ---

function rebuildTreeUpTo(index) {
    bstRoot = null;
    for (let i = 0; i < index; i++) {
        // Replay actions to Current State
        // Assuming user answered correctly or we just assume the 'correct' state for the next question?
        // To be fair, usually we give the correct state for the next Q.
        const q = BST_QUESTIONS[i];
        if (q.type === 'insert') bstRoot = DSATree.insertBST(bstRoot, q.val);
        else if (q.type === 'delete') bstRoot = DSATree.deleteBST(bstRoot, q.val);
    }
    DSATree.renderTreeToDOM(bstRoot, 'bst-viz');
}

function updateQuestionDisplay() {
    if (currentQuestionIndex >= BST_QUESTIONS.length) {
        document.getElementById('bst-question').textContent = "All BST operations completed!";
        document.querySelector('.controls-area').style.display = 'none';
        return;
    }
    const q = BST_QUESTIONS[currentQuestionIndex];
    document.getElementById('bst-question').textContent = `Question ${currentQuestionIndex + 1}: ${q.text}`;
}

async function handleBSTAction(actionType) {
    if (currentQuestionIndex >= BST_QUESTIONS.length) return;

    const q = BST_QUESTIONS[currentQuestionIndex];
    const inputVal = parseInt(document.getElementById('bst-input').value);

    let correct = false;
    let msg = "";

    // Validation Logic
    if (actionType !== q.type) {
        alert("Wrong operation! Read the question.");
        return;
    }

    if (actionType === 'insert') {
        if (inputVal === q.val) {
            bstRoot = DSATree.insertBST(bstRoot, inputVal);
            correct = true;
        } else {
            msg = "Wrong value inserted.";
        }
    } else if (actionType === 'search') {
        if (inputVal === q.val) {
            // Visual highlight logic could go here
            correct = true;
        } else {
            msg = "Wrong value searched.";
        }
    } else if (actionType === 'delete') {
        if (inputVal === q.val) {
            bstRoot = DSATree.deleteBST(bstRoot, inputVal);
            correct = true;
        } else {
            msg = "Wrong value deleted.";
        }
    } else if (actionType === 'inorder') {
        // Simple check
        correct = true;
    }

    if (correct) {
        // Submit Score
        await submitBSTAnswer(true);
        currentQuestionIndex++;
        DSATree.renderTreeToDOM(bstRoot, 'bst-viz'); // Update Visual
        updateQuestionDisplay();
    } else {
        alert(msg || "Incorrect. Try again.");
        // Optional: submitAnswer(false) if we want to track attempts
        await submitBSTAnswer(false);
    }

    document.getElementById('bst-input').value = '';
}

async function submitBSTAnswer(isCorrect) {
    try {
        const res = await fetch('/api/bst/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ correct: isCorrect })
        });
        const data = await res.json();
        if (data.success) {
            document.getElementById('score-display').textContent = `BST Score: ${data.bst_score}`;
        }
    } catch (e) {
        console.error("Score Error", e);
    }
}

// --- NAVIGATION & TABS ---

function showChallenge(type) {
    document.querySelectorAll('.challenge-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.challenge-content').forEach(c => c.classList.remove('active'));

    document.getElementById(`tab-${type}`).classList.add('active');
    document.getElementById(`challenge-${type}`).classList.add('active');

    if (type === 'bst') DSATree.renderTreeToDOM(bstRoot, 'bst-viz');
}

async function leaveRound(finished = false) {
    clearInterval(phase2Timer);
    await saveTimer(); // Pause

    if (!finished) {
        // Just leave
        window.location.href = 'phases.html';
    } else {
        // Exit API
        await fetch('/api/phase2/exit', { method: 'POST' });
        window.location.href = 'phases.html';
    }
}

function displayConfirm() {
    document.getElementById('confirm-modal').classList.add('active');
}
function closeConfirm() {
    document.getElementById('confirm-modal').classList.remove('active');
}
function finishRound() {
    displayConfirm();
}
async function confirmExit() {
    await leaveRound(true);
}

// --- LEGACY RB SUPPORT ---

function initDragAndDrop() {
    // Only for RB
    const draggables = document.querySelectorAll('.draggable');
    const dropzones = document.querySelectorAll('.dropzone');

    draggables.forEach(d => {
        d.addEventListener('dragstart', e => {
            e.dataTransfer.setData('value', d.dataset.value);
            e.dataTransfer.setData('color', d.dataset.color);
            e.dataTransfer.setData('origin-id', d.parentNode.id);
            d.style.opacity = '0.5';
        });
        d.addEventListener('dragend', () => d.style.opacity = '1');
    });

    dropzones.forEach(z => {
        z.addEventListener('dragover', e => e.preventDefault());
        z.addEventListener('drop', e => {
            e.preventDefault();
            const val = e.dataTransfer.getData('value');
            const col = e.dataTransfer.getData('color');

            // Clear zone
            z.innerHTML = '';

            // Create clone
            const el = document.createElement('div');
            el.className = 'draggable';
            el.textContent = val;
            el.dataset.value = val;
            el.dataset.color = col;
            el.style.background = col === 'red' ? '#D00' : 'black';
            el.style.border = col === 'red' ? '2px solid white' : '2px solid var(--accent-avengers)';
            el.draggable = true;
            // recursive drag support for moved items? Simplified: once placed, click to remove?
            el.onclick = () => {
                z.removeChild(el);
                // Return to bank? Or just delete. The bank is static in this version for simplicity, 
                // or we can just let user drag from bank again (unlimited clones?)
                // Let's assume unlimited clones for simplicity or just delete.
            };

            z.appendChild(el);
        });
    });
}

async function validateRB() {
    const result = DSATree.validateRBFromUI();
    if (result.valid) {
        // API Call
        await fetch('/api/rb/complete', { method: 'POST' });
        alert("RB Tree Completed! Points Awarded.");
    } else {
        alert("Invalid RB Tree: " + result.error);
    }
}
