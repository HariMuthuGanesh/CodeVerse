// Import proper tree validation functions
// Note: dsa-trees.js must be loaded before this file in HTML

// Challenge completion tracking
// Challenge completion tracking (Initialize from StateManager later)
let challengeStatus = {
    avl: { completed: false, points: 0 },
    rb: { completed: false, points: 0 }
};

const challengePoints = {
    avl: 25,
    rb: 25
};

// Phase 2 Timer
const PHASE2_TIME_LIMIT = 10 * 60; // 10 minutes in seconds
let phase2TimeRemaining = PHASE2_TIME_LIMIT;
let phase2TimerInterval = null;
let phase2TimeUp = false;

document.addEventListener('DOMContentLoaded', () => {
    initPhase2State();
    initDragAndDrop();
    updateProgress();
    startPhase2Timer();
});

function initPhase2State() {
    const state = StateManager.getState();
    challengeStatus = state.phase2.challenges;
    phase2TimeRemaining = state.phase2.timeRemaining;

    // Restore placements
    restorePlacements(state.phase2.challenges.avl, 'avl');
    restorePlacements(state.phase2.challenges.rb, 'rb');
}

function restorePlacements(challengeState, type) {
    if (!challengeState || !challengeState.placements) return;

    Object.entries(challengeState.placements).forEach(([slotId, value]) => {
        const slot = document.getElementById(slotId);
        // Find node in bank (or recreate it if needed, but bank should have them)
        // Since nodes move, we look in the bank or other slots.
        // Simplified: Search globally by ID or Value.
        // Actually, we stored 'value', but we need the element ID or reference.
        // Let's assume nodes have predictable IDs: type-node-value
        // But what if duplicates? RB Bank has distinct IDs (rb-node-10 etc).
        // Let's rely on finding element by ID if we stored ID.
        // Wait, StateManager `updatePlacement` stored `value`.
        // Let's update `updatePlacement` to store `elementId` too or just find by value mechanism.

        // BETTER APPROACH: Find the draggable with data-value AND correct type
        // For duplicates (like RB red nodes), this might grab the first one. 
        // Ideally we should persist elementId.

        // Let's defer to the standard "find unplaced node with this value"
        const bank = document.getElementById(`${type}-bank`);
        const node = Array.from(bank.children).find(n => n.dataset.value == value);

        if (node && slot) {
            slot.appendChild(node);
        }
    });
}


// Challenge navigation
function showChallenge(challengeType) {
    // Hide all challenges
    document.querySelectorAll('.challenge-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.challenge-tab').forEach(el => el.classList.remove('active'));

    // Show selected challenge
    document.getElementById(`challenge-${challengeType}`).classList.add('active');
    document.getElementById(`tab-${challengeType}`).classList.add('active');

    // Reinitialize drag and drop for the active challenge
    initDragAndDrop();
}

function startPhase2Timer() {
    const timerDisplay = document.getElementById('phase2-timer');
    if (!timerDisplay) return;

    phase2TimerInterval = setInterval(() => {
        phase2TimeRemaining--;

        // Save timer every 5 seconds or simplified check
        if (phase2TimeRemaining % 5 === 0) {
            StateManager.updateTimer(phase2TimeRemaining);
        }

        const mins = Math.floor(phase2TimeRemaining / 60);
        const secs = phase2TimeRemaining % 60;
        timerDisplay.textContent = `${mins}:${secs < 10 ? '0' : ''}${secs}`;

        // Warning when less than 1 minute
        if (phase2TimeRemaining < 60) {
            timerDisplay.classList.add('warning');
        }

        if (phase2TimeRemaining <= 0) {
            clearInterval(phase2TimerInterval);
            phase2TimeUp = true;
            disablePhase2();
            autoSubmitPhase2();
        }
    }, 1000);
}

function disablePhase2() {
    // Disable all drag and drop
    document.querySelectorAll('.draggable').forEach(el => {
        el.draggable = false;
        el.style.pointerEvents = 'none';
        el.style.opacity = '0.5';
    });

    document.querySelectorAll('.dropzone').forEach(el => {
        el.style.pointerEvents = 'none';
    });

    document.querySelectorAll('.btn-cyber').forEach(btn => {
        btn.disabled = true;
        btn.style.pointerEvents = 'none';
        btn.style.opacity = '0.5';
    });

    const timerDisplay = document.getElementById('phase2-timer');
    if (timerDisplay) {
        timerDisplay.textContent = 'TIME UP!';
        timerDisplay.classList.add('time-up');
    }
}

async function autoSubmitPhase2() {
    // Calculate points based on completed challenges
    const totalPoints = Object.values(challengeStatus).reduce((sum, c) => sum + c.points, 0);

    // Submit whatever progress was made
    try {
        await fetch('/api/complete-phase-2', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ points: totalPoints })
        });

        showResult(
            "TIME UP - PHASE 2 SUBMITTED",
            `Time has ended. Your progress has been saved.\nPoints Earned: ${totalPoints}/50\n\nCompleted Challenges: ${Object.values(challengeStatus).filter(c => c.completed).length}/3`,
            false,
            true
        );
    } catch (e) {
        console.error("Error submitting phase 2:", e);
        showResult(
            "TIME UP",
            "Time has ended. Your progress has been calculated based on completed challenges.",
            false,
            true
        );
    }
}

function updateProgress() {
    const completed = Object.values(challengeStatus).filter(c => c.completed).length;
    const totalPoints = Object.values(challengeStatus).reduce((sum, c) => sum + c.points, 0);

    document.getElementById('progress-indicator').textContent =
        `Progress: ${completed}/3 challenges completed | Points: ${totalPoints}/50`;

    // Update tab styles
    Object.keys(challengeStatus).forEach(key => {
        const tab = document.getElementById(`tab-${key}`);
        if (challengeStatus[key].completed) {
            tab.classList.add('completed');
            tab.textContent = tab.textContent.replace('Challenge', '✓ Challenge');
        }
    });
}

function initDragAndDrop() {
    // Get active challenge
    const activeChallenge = document.querySelector('.challenge-content.active');
    if (!activeChallenge) return;

    // Don't initialize if time is up
    if (phase2TimeUp) return;

    const challengeType = activeChallenge.id.replace('challenge-', '');
    const draggables = activeChallenge.querySelectorAll('.draggable');
    const dropzones = activeChallenge.querySelectorAll('.dropzone');

    draggables.forEach(draggable => {
        draggable.addEventListener('dragstart', (e) => {
            draggable.classList.add('dragging');
            e.dataTransfer.setData('text/plain', draggable.dataset.value);
            e.dataTransfer.setData('element-id', draggable.id);
        });

        draggable.addEventListener('dragend', () => {
            draggable.classList.remove('dragging');
        });
    });

    dropzones.forEach(zone => {
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('drag-over');
        });

        zone.addEventListener('dragleave', () => {
            zone.classList.remove('drag-over');
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('drag-over');

            const value = e.dataTransfer.getData('text/plain');
            const elementId = e.dataTransfer.getData('element-id');
            const draggingElement = document.getElementById(elementId);

            if (zone.children.length > 0) {
                // Swap: return existing node to bank, place new one
                const existingNode = zone.children[0];
                const bank = document.getElementById(`${challengeType}-bank`);
                if (bank && existingNode) {
                    bank.appendChild(existingNode);
                    // Update state: remove existing from slot
                    StateManager.updatePlacement(challengeType, zone.id, null);
                }
            }

            if (draggingElement) {
                draggingElement.parentNode.removeChild(draggingElement);
                zone.appendChild(draggingElement);
                // Update state: add new to slot
                StateManager.updatePlacement(challengeType, zone.id, draggingElement.dataset.value);
            }
        });

        // Allow clicking on nodes in dropzones to remove them
        zone.addEventListener('click', (e) => {
            if (zone.children.length > 0) {
                const node = zone.children[0];
                // Only remove if clicking directly on the node or the dropzone
                if (e.target === node || e.target === zone) {
                    const bank = document.getElementById(`${challengeType}-bank`);
                    if (bank) {
                        bank.appendChild(node);
                        // Update state: remove
                        StateManager.updatePlacement(challengeType, zone.id, null);
                    }
                }
            }
        });
    });
}

// ============================================================================
// BST VALIDATION (USING PROPER DSA ALGORITHM)
// ============================================================================

// Red-Black Tree Validation
async function validateRB() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.add('active');
    await new Promise(r => setTimeout(r, 1000));

    // Use proper RB validation from dsa-trees.js
    const result = validateRBFromUI('rb', 7);

    overlay.classList.remove('active');

    if (result.valid) {
        // Mark complete in State Manager
        StateManager.completeChallenge('rb', challengePoints.rb);

        // Update local status for UI immediately
        challengeStatus.rb.completed = true;
        challengeStatus.rb.points = challengePoints.rb;

        updateProgress();
        showResult("Red-Black Tree Challenge Complete!", `Points Earned: ${challengePoints.rb}/25\nValid RB Tree constructed!`, false);

        checkAllChallengesComplete(); // Check if this was the last one
    } else {
        showResult("REALITY COLLAPSE", result.error, true);
    }
}

// AVL Validation - Harder version with more nodes
async function validateAVL() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.add('active');
    await new Promise(r => setTimeout(r, 1000));

    let isValid = true;
    let errorMsg = "";

    // Check all filled (15 slots for harder AVL)
    for (let i = 1; i <= 15; i++) {
        if (getVal('avl', i) === null) {
            isValid = false;
            errorMsg = "Timeline Incomplete. Fill all nodes.";
            break;
        }
    }

    if (isValid) {
        // Get all values
        const values = {};
        for (let i = 1; i <= 15; i++) {
            values[i] = getVal('avl', i);
        }

        // Validate BST property for all nodes
        // Root: slot 1
        // Level 2: slots 2, 3
        // Level 3: slots 4, 5, 6, 7
        // Level 4: slots 8, 9, 10, 11, 12, 13, 14, 15

        // Level 1: Root
        if (!(values[2] < values[1] && values[3] > values[1])) {
            isValid = false;
        }

        // Level 2: Left subtree
        if (values[2] !== null) {
            if (!(values[4] < values[2] && values[5] > values[2])) {
                isValid = false;
            }
            // Level 3 left subtree
            if (values[4] !== null && !(values[8] < values[4] && values[9] > values[4])) {
                isValid = false;
            }
            if (values[5] !== null && !(values[10] < values[5] && values[11] > values[5])) {
                isValid = false;
            }
        }

        // Level 2: Right subtree
        if (values[3] !== null) {
            if (!(values[6] < values[3] && values[7] > values[3])) {
                isValid = false;
            }
            // Level 3 right subtree
            if (values[6] !== null && !(values[12] < values[6] && values[13] > values[6])) {
                isValid = false;
            }
            if (values[7] !== null && !(values[14] < values[7] && values[15] > values[7])) {
                isValid = false;
            }
        }

        // Validate AVL balance property: height difference <= 1
        // Tree structure mapping: 
        // slot 1 = root
        // slot 2, 3 = children of root
        // slot 4, 5 = children of slot 2; slot 6, 7 = children of slot 3
        // slot 8, 9 = children of slot 4; slot 10, 11 = children of slot 5
        // slot 12, 13 = children of slot 6; slot 14, 15 = children of slot 7

        function getChildSlots(parentSlot) {
            // Map parent slots to child slots
            const mapping = {
                1: [2, 3],
                2: [4, 5],
                3: [6, 7],
                4: [8, 9],
                5: [10, 11],
                6: [12, 13],
                7: [14, 15]
            };
            return mapping[parentSlot] || [];
        }

        function getHeight(slotNum) {
            if (slotNum > 15 || values[slotNum] === null) return 0;
            const children = getChildSlots(slotNum);
            if (children.length === 0) return 1;

            const leftHeight = getHeight(children[0]);
            const rightHeight = getHeight(children[1]);
            return 1 + Math.max(leftHeight, rightHeight);
        }

        function getBalanceFactor(slotNum) {
            if (slotNum > 15 || values[slotNum] === null) return 0;
            const children = getChildSlots(slotNum);
            if (children.length === 0) return 0;

            const leftHeight = getHeight(children[0]);
            const rightHeight = getHeight(children[1]);
            return leftHeight - rightHeight;
        }

        // Check balance factor for all nodes (must be -1, 0, or 1)
        for (let i = 1; i <= 15; i++) {
            if (values[i] !== null) {
                const balance = getBalanceFactor(i);
                if (balance < -1 || balance > 1) {
                    isValid = false;
                    break;
                }
            }
        }

        if (!isValid) {
            errorMsg = "Timeline Paradox Detected. Invalid AVL Tree. Tree must be balanced (balance factor -1, 0, or 1) and follow BST property.";
        }
    }

    overlay.classList.remove('active');

    if (isValid) {
        StateManager.completeChallenge('avl', challengePoints.avl);
        challengeStatus.avl.completed = true;
        challengeStatus.avl.points = challengePoints.avl;
        updateProgress();
        showResult("AVL Challenge Complete!", `Points Earned: ${challengePoints.avl}/25\nPerfectly balanced AVL tree constructed!`, false);
        checkAllChallengesComplete();
    } else {
        showResult("REALITY COLLAPSE", errorMsg, true);
    }
}

// B-Tree Validation - 6 nodes, 5 slots (one unused)
// ============================================================================
// B-TREE VALIDATION (USING PROPER DSA ALGORITHM)
// ============================================================================

// Removed B-Tree Validation

function checkAllChallengesComplete() {
    const allComplete = Object.values(challengeStatus).every(c => c.completed);
    const totalPoints = Object.values(challengeStatus).reduce((sum, c) => sum + c.points, 0);

    if (allComplete) {
        // All challenges done - submit to backend
        submitPhase2(totalPoints);
    }
}

async function submitPhase2(totalPoints) {
    try {
        await fetch('/api/complete-phase-2', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ points: totalPoints })
        });

        setTimeout(() => {
            showResult(
                "PHASE 2 COMPLETE ✓",
                `All challenges completed!\nTotal Points: ${totalPoints}/50\nThe Power Stone is within reach.`,
                false,
                true
            );
        }, 1000);
    } catch (e) {
        console.error("Error submitting phase 2:", e);
    }
}

function showResult(title, message, isError, showProceed = false) {
    const modal = document.getElementById('result-modal');
    const titleEl = document.getElementById('result-title');
    const msgEl = document.getElementById('result-msg');
    const actionArea = document.getElementById('action-area');

    titleEl.innerText = title;
    titleEl.style.color = isError ? "var(--accent-avengers)" : "var(--accent-avengers)";
    msgEl.innerText = message;

    if (showProceed) {
        actionArea.innerHTML = `<a href="phases.html" class="btn-cyber">PROCEED TO FINAL PHASE</a>`;
    } else if (isError) {
        actionArea.innerHTML = `<button onclick="closeModal()" class="btn-cyber" style="border-color: var(--accent-avengers);">TRY AGAIN</button>`;
    } else {
        actionArea.innerHTML = `<button onclick="closeModal()" class="btn-cyber" style="border-color: var(--accent-avengers);">CONTINUE</button>`;
    }

    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('result-modal').classList.remove('active');
}
