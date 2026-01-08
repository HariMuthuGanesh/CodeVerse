let questions = [];
let currentQuestionIndex = 0;
let userAnswers = {}; // { questionId: answerString }
let timerInterval;
const TIME_LIMIT = 10 * 60; // 10 minutes in seconds (600 seconds)
let timeRemaining = TIME_LIMIT;
let isTimeUp = false;

// Fallback questions if API fails
const FALLBACK_QUESTIONS = [
    {
        "id": 1,
        "question": "Which data structure best represents the multiverse timeline branching?",
        "options": ["Stack", "Queue", "Tree", "Graph"]
    },
    {
        "id": 2,
        "question": "What is the time complexity to find the 'Time Stone' in a sorted array using Binary Search?",
        "options": ["O(n)", "O(log n)", "O(1)", "O(n log n)"]
    },
    {
        "id": 3,
        "question": "If Iron Man's suit OS uses LIFO (Last In First Out), which structure is it using?",
        "options": ["Queue", "Stack", "Array", "Linked List"]
    },
    {
        "id": 4,
        "question": "Which sorting algorithm is inevitably linked to 'Divide and Conquer'?",
        "options": ["Bubble Sort", "Merge Sort", "Insertion Sort", "Selection Sort"]
    },
    {
        "id": 5,
        "question": "In Python, which keyword is used to create an anonymous function (like a stealth mission)?",
        "options": ["def", "lambda", "anon", "func"]
    }
];

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - Quiz.js initialized');
    console.log('Window location:', window.location.href);

    // Test if API is accessible first
    fetch('/api/test')
        .then(res => res.json())
        .then(data => {
            console.log('API test successful:', data);
            fetchQuestions();
        })
        .catch(err => {
            console.warn('API test failed, using fallback questions:', err);
            console.log('Using fallback questions');
            questions = FALLBACK_QUESTIONS;
            renderQuestion();
            updateProgress();
        });

    startTimer();
});

async function fetchQuestions() {
    try {
        console.log('Fetching questions from /api/quiz...');
        console.log('Current URL:', window.location.href);

        // Try to fetch questions
        const res = await fetch('/api/quiz', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            cache: 'no-cache'
        });

        console.log('Response status:', res.status);
        console.log('Response headers:', res.headers);

        if (!res.ok) {
            const errorText = await res.text();
            console.error('Error response:', errorText);
            throw new Error(`HTTP error! status: ${res.status}, body: ${errorText}`);
        }

        const data = await res.json();
        console.log('Received data:', data);
        console.log('Data type:', typeof data);
        console.log('Is array?', Array.isArray(data));

        if (!data) {
            throw new Error("No data received from server");
        }

        if (!Array.isArray(data)) {
            console.error('Data is not an array:', data);
            throw new Error("Invalid response format - expected array");
        }

        questions = data;
        if (questions.length === 0) {
            throw new Error("No questions received - array is empty");
        }

        console.log(`Successfully loaded ${questions.length} questions`);
        console.log('First question:', questions[0]);

        // Render immediately
        renderQuestion();
        updateProgress();

    } catch (e) {
        console.error("Failed to load quiz", e);
        console.error("Error stack:", e.stack);

        const questionBox = document.getElementById('question-box');
        if (questionBox) {
            questionBox.innerHTML = `
                <div style="color: var(--accent-avengers); padding: 2rem; text-align: center;">
                    <h3>Error loading questions</h3>
                    <p>${e.message}</p>
                    <p style="font-size: 0.9rem; margin-top: 1rem;">
                        Please check:<br>
                        1. Backend server is running (python backend/app.py)<br>
                        2. Server is accessible at http://localhost:5000<br>
                        3. Check browser console for more details
                    </p>
                    <button onclick="location.reload()" class="btn-cyber" style="margin-top: 1rem;">REFRESH PAGE</button>
                    <button onclick="fetchQuestions()" class="btn-cyber" style="margin-top: 1rem; margin-left: 1rem;">RETRY</button>
                </div>`;
        } else {
            console.error('question-box element not found for error display');
            alert('Error: question-box element not found. Please check the HTML structure.');
        }
    }
}

function startTimer() {
    const timerDisplay = document.getElementById('timer-display');
    if (!timerDisplay) return;
    
    timerInterval = setInterval(() => {
        timeRemaining--;
        const mins = Math.floor(timeRemaining / 60);
        const secs = timeRemaining % 60;
        timerDisplay.textContent = `${mins}:${secs < 10 ? '0' : ''}${secs}`;

        // Critical color change
        if (timeRemaining < 60) {
            timerDisplay.style.color = 'var(--accent-red-bright)';
            timerDisplay.style.textShadow = '0 0 10px var(--accent-red-bright)';
        }

        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            isTimeUp = true;
            disableQuiz();
            submitQuiz();
        }
    }, 1000);
}

function disableQuiz() {
    // Disable all interactive elements
    document.querySelectorAll('.option-card').forEach(card => {
        card.style.pointerEvents = 'none';
        card.style.opacity = '0.5';
    });
    
    document.querySelectorAll('.btn-cyber').forEach(btn => {
        btn.disabled = true;
        btn.style.pointerEvents = 'none';
        btn.style.opacity = '0.5';
    });
    
    // Show time up message
    const timerDisplay = document.getElementById('timer-display');
    if (timerDisplay) {
        timerDisplay.textContent = 'TIME UP!';
        timerDisplay.style.color = 'var(--accent-red-bright)';
    }
}

function renderQuestion() {
    console.log('renderQuestion called');
    console.log('Current question index:', currentQuestionIndex);
    console.log('Questions array length:', questions.length);
    console.log('Questions:', questions);

    const container = document.getElementById('question-box');
    if (!container) {
        console.error('question-box element not found!');
        alert('Error: question-box element not found in DOM');
        return;
    }
    console.log('Found question-box container');

    const q = questions[currentQuestionIndex];
    console.log('Current question:', q);

    if (!q) {
        if (questions.length === 0) {
            container.innerHTML = '<p style="color: var(--accent-avengers); padding: 2rem;">No questions loaded. Please refresh the page.</p>';
        } else {
            container.innerHTML = `<p style="color: var(--accent-avengers); padding: 2rem;">Question ${currentQuestionIndex + 1} not found. Total questions: ${questions.length}</p>`;
        }
        return;
    }

    // Escape HTML in options to prevent XSS
    const escapeHtml = (text) => {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML;
    };

    // Ensure options exist
    if (!q.options || !Array.isArray(q.options) || q.options.length === 0) {
        container.innerHTML = `<p style="color: var(--accent-avengers); padding: 2rem;">Question has no options. Question ID: ${q.id}</p>`;
        console.error('Question missing options:', q);
        return;
    }

    console.log('Rendering question:', q.question);
    console.log('Options:', q.options);

    container.innerHTML = `
        <h3 class="question-text">${currentQuestionIndex + 1}. ${escapeHtml(q.question)}</h3>
        <div class="options-grid">
            ${q.options.map((opt, idx) => `
                <div class="option-card interactive" data-question-id="${q.id}" data-option-index="${idx}" data-option="${escapeHtml(opt)}">
                    ${escapeHtml(opt)}
                </div>
            `).join('')}
        </div>
    `;

    console.log('Question HTML rendered');

    // Add event listeners to option cards
    const cards = container.querySelectorAll('.option-card');
    console.log('Found option cards:', cards.length);
    cards.forEach(card => {
        card.addEventListener('click', function () {
            const questionId = parseInt(this.getAttribute('data-question-id'));
            const optionIndex = parseInt(this.getAttribute('data-option-index'));
            console.log('Option clicked:', questionId, optionIndex);
            selectOption(questionId, optionIndex, this);
        });
    });

    // Highlight selected if existing
    const existing = userAnswers[q.id];
    if (existing !== undefined) {
        cards.forEach(c => {
            if (c.getAttribute('data-option') === existing) c.classList.add('selected');
        });
    }

    console.log('Question rendering complete');
}

function selectOption(id, optionIndex, cardElement) {
    const q = questions.find(q => q.id === id);
    if (!q) return;

    const selectedOption = q.options[optionIndex];
    userAnswers[id] = selectedOption;

    // UI update
    const allOptions = document.querySelectorAll('.option-card');
    allOptions.forEach(opt => opt.classList.remove('selected'));
    cardElement.classList.add('selected');
}

function nextQuestion() {
    if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex++;
        renderQuestion();
        updateProgress();
    }
}

function prevQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        renderQuestion();
        updateProgress();
    }
}

function updateProgress() {
    if (questions.length === 0) return;

    const progressBar = document.getElementById('progress-bar');
    if (progressBar) {
        const progress = ((currentQuestionIndex + 1) / questions.length) * 100;
        progressBar.style.width = `${progress}%`;
    }

    // Show/Hide buttons
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const finishBtn = document.getElementById('finish-btn');

    if (prevBtn) {
        prevBtn.style.display = currentQuestionIndex === 0 ? 'none' : 'inline-block';
    }

    const isLast = currentQuestionIndex === questions.length - 1;
    if (nextBtn) {
        nextBtn.style.display = isLast ? 'none' : 'inline-block';
    }
    if (finishBtn) {
        finishBtn.style.display = isLast ? 'inline-block' : 'none';
    }
}

async function submitQuiz() {
    if (timerInterval) {
        clearInterval(timerInterval);
    }
    
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('active');
    }

    try {
        const res = await fetch('/api/submit-quiz', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                answers: userAnswers,
                timeUp: isTimeUp,
                questionsAttempted: Object.keys(userAnswers).length,
                totalQuestions: questions.length
            })
        });
        const result = await res.json();

        if (overlay) {
            overlay.classList.remove('active');
        }
        showResult(result);
    } catch (e) {
        console.error("Submission failed", e);
        if (overlay) {
            overlay.classList.remove('active');
        }
        alert("Transmission error. Try again.");
    }
}

function showResult(result) {
    const modal = document.getElementById('result-modal');
    const title = document.getElementById('result-title');
    const msg = document.getElementById('result-msg');
    const actionArea = document.getElementById('action-area');

    modal.classList.add('active');

    const points = result.points || (result.score * 5); // 5 points per correct answer
    const totalPoints = result.max_points || 50; // 50 points max

    // Always allow users to proceed - no restrictions
    const questionsAttempted = Object.keys(userAnswers).length;
    const timeUpMsg = isTimeUp ? "<br><strong style='color: var(--accent-red-bright);'>⏱️ Time ended - Auto-submitted</strong>" : "";
    
    title.innerHTML = "PHASE 1 COMPLETE <span style='color:var(--accent-avengers)'>✓</span>";
    title.style.color = "var(--accent-avengers)";
    msg.innerHTML = `Score: ${result.score}/${result.total} | Points: ${points}/${totalPoints}<br>Questions Attempted: ${questionsAttempted}/${result.total}${timeUpMsg}<br>Phase completed! You can proceed to the next challenge.`;
    actionArea.innerHTML = `<a href="phases.html" class="btn-cyber">PROCEED TO NEXT PHASE</a>`;
    
    // CRITICAL: Unlock Phase 2 immediately based on API response (DB-driven)
    if (result.phase1_completed) {
        // Phase 2 is now unlocked - this comes from Supabase, not localStorage
        console.log('[PHASE1] Phase 1 completed, Phase 2 unlocked from DB');
    }
}
