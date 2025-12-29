/**
 * State Manager for CodeVerse Competition
 * Handles persistence of user progress across page reloads using localStorage.
 */

const StateManager = {
    // Key for localStorage
    STORAGE_KEY: 'codeverse_state_v1',

    // Initial state schema
    initialState: {
        phase1: {
            completed: false,
            score: 0
        },
        phase2: {
            timeRemaining: 600, // 10 minutes default
            challenges: {
                avl: {
                    completed: false,
                    score: 0,
                    placements: {} // { "slot-id": "node-value" }
                },
                rb: {
                    completed: false,
                    score: 0,
                    placements: {}
                }
            }
        },
        phase3: {
            unlocked: false,
            completed: false
        }
    },

    /**
     * Load state from localStorage or return default
     */
    getState() {
        try {
            const stored = localStorage.getItem(this.STORAGE_KEY);
            if (stored) {
                // Merge stored state with initial state to ensure schema updates don't break
                // This is a simple shallow merge, meant for robust start
                return { ...this.initialState, ...JSON.parse(stored) };
            }
        } catch (e) {
            console.error("Failed to load state", e);
        }
        return JSON.parse(JSON.stringify(this.initialState));
    },

    /**
     * Save current state to localStorage
     */
    saveState(state) {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(state));
            // Optional: debounce sync to backend here if needed
        } catch (e) {
            console.error("Failed to save state", e);
        }
    },

    /**
     * Update a specific phase 2 drag-and-drop placement
     */
    updatePlacement(challengeType, slotId, value) {
        const state = this.getState();

        // Initialize if missing
        if (!state.phase2.challenges[challengeType]) {
            state.phase2.challenges[challengeType] = { completed: false, score: 0, placements: {} };
        }

        if (value === null) {
            // Remove placement
            delete state.phase2.challenges[challengeType].placements[slotId];
        } else {
            // Add/Update placement
            state.phase2.challenges[challengeType].placements[slotId] = value;
        }

        this.saveState(state);
    },

    /**
     * Update timer for Phase 2
     */
    updateTimer(seconds) {
        const state = this.getState();
        state.phase2.timeRemaining = seconds;
        this.saveState(state);
    },

    /**
     * Mark a challenge as complete
     */
    completeChallenge(challengeType, score) {
        const state = this.getState();
        if (state.phase2.challenges[challengeType]) {
            state.phase2.challenges[challengeType].completed = true;
            state.phase2.challenges[challengeType].score = score;
            this.saveState(state);
        }
    },

    /**
     * Check if Phase 3 should unlock
     * Logic: Unlock if minimum score reached in Phase 2
     */
    checkPhase3Unlock() {
        const state = this.getState();
        const avlScore = state.phase2.challenges.avl?.score || 0;
        const rbScore = state.phase2.challenges.rb?.score || 0;

        // Example threshold: > 0 points to unlock Phase 3 (modify as needed)
        // User req: "Phase 3 unlocks if Minimum Phase 2 score is reached"
        const totalScore = avlScore + rbScore;
        const threshold = 10; // Arbitrary low threshold to encourage progression

        if (totalScore >= threshold && !state.phase3.unlocked) {
            state.phase3.unlocked = true;
            this.saveState(state);
            return true;
        }
        return state.phase3.unlocked;
    },

    /**
     * Reset specific phase (debug helper)
     */
    resetPhase(phaseName) {
        const state = this.getState();
        state[phaseName] = JSON.parse(JSON.stringify(this.initialState[phaseName]));
        this.saveState(state);
        location.reload();
    }
};
