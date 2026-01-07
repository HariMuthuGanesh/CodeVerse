async function checkPhaseStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        return status;
    } catch (error) {
        console.error('Failed to fetch status:', error);
        return null;
    }
}

function updatePhaseUI(status) {
    if (!status) {
        console.warn("Status fetch failed.");
        return;
    }

    // Helper to update card state
    const updateCard = (elementId, isUnlocked, isCompleted, score, label) => {
        const card = document.getElementById(elementId);
        if (!card) return;

        const btn = card.querySelector('.phase-btn');
        let originalHref = btn.getAttribute('data-href');
        if (!originalHref) {
            originalHref = btn.getAttribute('href');
            btn.setAttribute('data-href', originalHref);
        }

        // Reset classes
        card.classList.remove('locked', 'unlocked', 'completed');
        btn.classList.remove('btn-locked');
        btn.removeAttribute('disabled');

        if (isUnlocked && !isCompleted) btn.href = originalHref;

        if (!isUnlocked) {
            // LOCKED STATE
            card.classList.add('locked');
            btn.classList.add('btn-locked');
            btn.setAttribute('disabled', 'true');
            btn.textContent = 'Locked';
            btn.removeAttribute('href');
        } else if (isCompleted) {
            // COMPLETED STATE
            card.classList.add('unlocked', 'completed');

            // STRICT LOCK for Phase 2
            if (label === "Phase 2") {
                btn.classList.add('btn-locked');
                btn.setAttribute('disabled', 'true');
                btn.textContent = `Completed (${score} pts)`;
                btn.removeAttribute('href'); // Prevent re-entry
            } else {
                // Phase 1 or 3
                btn.textContent = `Completed (${score} pts)`;
                // Phase 1 might allow revisit to see score? 
                // Let's keep it open or close based on requirements. 
                // "First phase second round dont get update..." implies partial confusion.
                // Safest to keep completed phases accessible for review unless strictly forbidden.
                // But Phase 2 was explicitly forbidden.
            }
        } else {
            // ACTIVE STATE
            card.classList.add('unlocked');
            btn.textContent = 'Enter Phase';
        }
    };

    // Phase 1
    updateCard('phase-1-card', true, status.phase1_completed, status.phase1_score || 0, "Phase 1");

    // Phase 2: Unlocked only if Phase 1 completed
    const p2Completed = status.phase2_completed || (status.phase2_details && status.phase2_details.bst.status === 'exited');
    updateCard('phase-2-card', status.phase1_completed, p2Completed, status.phase2_score || 0, "Phase 2");

    // Phase 3: Unlocked if Phase 2 completed
    updateCard('phase-3-card', status.phase2_completed, status.phase3_completed, status.phase3_score || 0, "Phase 3");

    // Special CSS for Locked Overlay based on class
    document.querySelectorAll('.phase-card.locked').forEach(c => {
        // Ensure visual lock style
    });
}
