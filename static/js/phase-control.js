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
        // If status fetch fails, unlock all phases by default
        unlockAllPhases();
        return;
    }

    // Helper to update card lock state
    const updateCard = (elementId, unlocked, completed, score = 0) => {
        const card = document.getElementById(elementId);
        if (!card) return;

        const btn = card.querySelector('.phase-btn');
        
        // Always unlock all phases
        card.classList.remove('locked');
        card.classList.add('unlocked');
        if (completed) card.classList.add('completed');

        if (btn) {
            btn.classList.remove('btn-locked');
            btn.removeAttribute('disabled');
            if (completed) {
                btn.textContent = `Completed (${score} pts) - Replay`;
            } else {
                btn.textContent = 'Enter Phase';
            }
        }
    };

    updateCard('phase-1-card', true, status.phase1_completed, status.phase1_score || 0);
    updateCard('phase-2-card', true, status.phase2_completed, status.phase2_score || 0);
    updateCard('phase-3-card', true, status.phase3_completed, status.phase3_score || 0);
}

function unlockAllPhases() {
    ['phase-1-card', 'phase-2-card', 'phase-3-card'].forEach(id => {
        const card = document.getElementById(id);
        if (card) {
            card.classList.remove('locked');
            const btn = card.querySelector('.phase-btn');
            if (btn) {
                btn.classList.remove('btn-locked');
                btn.removeAttribute('disabled');
            }
        }
    });
}

// Global visual effect for phase transition (optional usage)
function unlockAnimation(element) {
    element.animate([
        { transform: 'scale(1)', filter: 'brightness(1)' },
        { transform: 'scale(1.1)', filter: 'brightness(1.5)' },
        { transform: 'scale(1)', filter: 'brightness(1)' }
    ], {
        duration: 500,
        easing: 'ease-in-out'
    });
}
