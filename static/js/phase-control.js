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

    // CRITICAL: Scores only visible after Phase 3 completion
    const scoresVisible = status.phase3_completed === true;

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
                if (scoresVisible) {
                    btn.textContent = `Completed (${score} pts)`;
                } else {
                    btn.textContent = `Completed`;
                }
                btn.removeAttribute('href'); // Prevent re-entry
            } else {
                // Phase 1 or 3
                if (scoresVisible) {
                    btn.textContent = `Completed (${score} pts)`;
                } else {
                    btn.textContent = `Completed`;
                }
            }
        } else {
            // ACTIVE STATE
            card.classList.add('unlocked');
            btn.textContent = 'Enter Phase';
        }
    };

    // Phase 1: Always unlocked, but hide score until Phase 3 complete
    const phase1Score = scoresVisible ? (status.phase1_score || 0) : 0;
    updateCard('phase-1-card', true, status.phase1_completed, phase1Score, "Phase 1");

    // Phase 2: Unlocked only if Phase 1 completed
    const p2Completed = status.phase2_completed === true;
    const phase2Score = scoresVisible ? (status.phase2_score || 0) : 0;
    updateCard('phase-2-card', status.phase1_completed, p2Completed, phase2Score, "Phase 2");

    // Phase 3: Unlocked ONLY if Phase 2 completed (locked until Phase 2 is done)
    const phase3Unlocked = status.phase2_completed === true;
    const phase3Score = scoresVisible ? (status.phase3_score || 0) : 0;
    updateCard('phase-3-card', phase3Unlocked, status.phase3_completed, phase3Score, "Phase 3");
    
    // Log for debugging
    console.log('[PHASE CONTROL] Phase 2 completed:', status.phase2_completed, 'Phase 3 unlocked:', phase3Unlocked, 'Scores visible:', scoresVisible);

    // Special CSS for Locked Overlay based on class
    document.querySelectorAll('.phase-card.locked').forEach(c => {
        // Ensure visual lock style
    });
}
