# Developer Guide - CodeVerse Quiz System

This guide provides clear instructions for developers on how to add quiz questions, configure Phase 2 (DSA Challenge), and set up the HackerRank link for Phase 3.

---

## 📋 Table of Contents

1. [Adding Quiz Questions for Phase 1](#adding-quiz-questions-for-phase-1)
2. [Adding Questions for Phase 2 (DSA Challenge)](#adding-questions-for-phase-2-dsa-challenge)
3. [Configuring HackerRank Link for Phase 3](#configuring-hackerrank-link-for-phase-3)
4. [Scoring System](#scoring-system)
5. [Testing Your Changes](#testing-your-changes)

---

## 🎯 Adding Quiz Questions for Phase 1

### Location
Quiz questions are stored in: `backend/quiz_data.py`

### Format
Each question must follow this structure:

```python
{
    "id": <unique_integer>,           # Unique ID (must be sequential: 1, 2, 3, ...)
    "question": "<question_text>",     # The question text
    "options": [                       # Array of 4 answer options
        "Option A",
        "Option B", 
        "Option C",
        "Option D"
    ],
    "answer": "<correct_option>"       # Must exactly match one of the options
}
```

### Example

```python
{
    "id": 6,
    "question": "What is the time complexity of Quick Sort in the average case?",
    "options": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"],
    "answer": "O(n log n)"
}
```

### Steps to Add a New Question

1. **Open** `backend/quiz_data.py`
2. **Add** your question to the `QUIZ_QUESTIONS` list
3. **Ensure**:
   - The `id` is unique and sequential
   - There are exactly 4 options
   - The `answer` exactly matches one of the options (case-sensitive)
   - All strings are properly quoted

### Complete Example File

```python
QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": "Which data structure best represents the multiverse timeline branching?",
        "options": ["Stack", "Queue", "Tree", "Graph"],
        "answer": "Tree"
    },
    {
        "id": 2,
        "question": "What is the time complexity to find the 'Time Stone' in a sorted array using Binary Search?",
        "options": ["O(n)", "O(log n)", "O(1)", "O(n log n)"],
        "answer": "O(log n)"
    },
    # Add more questions here...
    {
        "id": 6,  # Your new question
        "question": "What is the time complexity of Quick Sort in the average case?",
        "options": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"],
        "answer": "O(n log n)"
    }
]
```

### Important Notes

- ✅ **Do NOT** include the answer in the frontend (it's automatically stripped)
- ✅ Questions are displayed in the order they appear in the list
- ✅ Each question is worth **10 points** (automatically calculated)
- ✅ Users can proceed regardless of their score (no passing requirement)

---

## 🌳 Adding Questions for Phase 2 (DSA Challenge)

### Location
Phase 2 configuration is in: `static/js/dsa.js`

### Current Implementation
Phase 2 uses a **Binary Search Tree (BST)** drag-and-drop challenge. Users must arrange numbers to form a valid BST.

### Configuration Structure

The challenge is configured in `static/js/dsa.js`:

```javascript
const correctStructure = {
    // Slot relationships (Parent -> [Left, Right])
    'slot-1': ['slot-2', 'slot-3'],  // Root -> Left, Right
    'slot-2': ['slot-4', 'slot-5'],  // Left child -> Left, Right
    'slot-3': ['slot-6', 'slot-7']  // Right child -> Left, Right
};
```

### Steps to Add a New DSA Challenge

#### Option 1: Change the Numbers (Easiest)

1. **Open** `frontend/dsa.html`
2. **Find** the draggable nodes section (around line 126-132)
3. **Modify** the numbers:

```html
<div class="bank-container glass-card">
    <!-- Change these values -->
    <div class="draggable interactive" draggable="true" id="node-10" data-value="10">10</div>
    <div class="draggable interactive" draggable="true" id="node-5" data-value="5">5</div>
    <!-- Add more nodes as needed -->
</div>
```

4. **Update** the validation logic in `static/js/dsa.js` (around line 107-120) to match your new numbers

#### Option 2: Create a Different Data Structure Challenge

1. **Modify** `frontend/dsa.html`:
   - Change the tree layout structure
   - Update the dropzones arrangement
   - Modify the instructions text

2. **Update** `static/js/dsa.js`:
   - Modify the `correctStructure` object
   - Update the `validateSolution()` function with your validation logic
   - Adjust the BST property checks

### Example: Adding More Nodes

To add more nodes to the BST challenge:

1. **Add nodes** in `dsa.html`:
```html
<div class="draggable interactive" draggable="true" id="node-20" data-value="20">20</div>
<div class="draggable interactive" draggable="true" id="node-25" data-value="25">25</div>
```

2. **Add dropzones** in the tree layout:
```html
<!-- Level 4 -->
<div class="level">
    <div class="dropzone" id="slot-8"></div>
    <div class="dropzone" id="slot-9"></div>
</div>
```

3. **Update validation** in `dsa.js`:
```javascript
const v8 = getVal('slot-8');
const v9 = getVal('slot-9');
// Add validation logic for new nodes
```

### Scoring

- Phase 2 awards **50 points** upon successful completion
- Points are stored in session: `session['phase2_score'] = 50`
- To change points, modify `static/js/dsa.js` line 104:
```javascript
const points = 50; // Change this value
```

---

## 🔗 Configuring HackerRank Link for Phase 3

### Location
HackerRank link is configured in: `frontend/final.html`

### Current Implementation

The HackerRank link is currently set to redirect to the score page. To add an actual HackerRank challenge:

### Steps to Add HackerRank Link

1. **Open** `frontend/final.html`

2. **Find** the `redirectToHackerRank()` function (around line 102-118)

3. **Replace** the redirect logic:

```javascript
async function redirectToHackerRank() {
    // Mark phase 3 as complete with points
    const points = 100; // 100 points for completing final phase
    try {
        await fetch('/api/complete-phase-3', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ points: points })
        });
        
        // OPTION 1: Redirect to HackerRank challenge
        window.open('https://www.hackerrank.com/challenges/YOUR_CHALLENGE_NAME', '_blank');
        
        // OPTION 2: Redirect to score page after opening HackerRank
        setTimeout(() => {
            window.location.href = "score.html";
        }, 2000);
        
        // OPTION 3: Just redirect to HackerRank (user closes tab to return)
        // window.location.href = 'https://www.hackerrank.com/challenges/YOUR_CHALLENGE_NAME';
        
    } catch (e) {
        console.error("Error completing phase 3:", e);
        // Fallback: still redirect
        window.location.href = "score.html";
    }
}
```

### Option 1: Direct HackerRank Challenge Link

Replace `YOUR_CHALLENGE_NAME` with your actual HackerRank challenge URL:

```javascript
// Example: Binary Tree challenge
window.open('https://www.hackerrank.com/challenges/binary-search-tree-lowest-common-ancestor', '_blank');

// Current Configuration: CodeVerse Contest
window.open('https://www.hackerrank.com/codeverse-1766848205', '_blank');
```

### Option 2: Custom HackerRank Contest

If you're using a custom HackerRank contest:

```javascript
// Example: Custom contest link
window.open('https://www.hackerrank.com/contests/your-contest-name', '_blank');
```

### Option 3: Multiple Challenges

To link to multiple challenges or a contest with multiple problems:

```javascript
async function redirectToHackerRank() {
    const points = 100;
    try {
        await fetch('/api/complete-phase-3', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ points: points })
        });
        
        // Show modal with challenge options
        const challengeChoice = confirm(
            'Choose your challenge:\n' +
            'OK = Challenge 1\n' +
            'Cancel = Challenge 2'
        );
        
        if (challengeChoice) {
            window.open('https://www.hackerrank.com/challenges/challenge-1', '_blank');
        } else {
            window.open('https://www.hackerrank.com/challenges/challenge-2', '_blank');
        }
        
        // Redirect to score after delay
        setTimeout(() => {
            window.location.href = "score.html";
        }, 2000);
        
    } catch (e) {
        console.error("Error:", e);
        window.location.href = "score.html";
    }
}
```

### Updating the Warning Message

You can also update the warning message in `final.html` (around line 76-79):

```html
<p style="margin: 2rem 0; font-size: 1.1rem;">
    You are about to enter the HackerRank Quantum Realm.<br>
    Challenge: <strong>Binary Search Tree - Lowest Common Ancestor</strong><br>
    There is no turning back. Are you prepared?
</p>
```

### Scoring

- Phase 3 awards **100 points** upon completion
- Points are stored in session: `session['phase3_score'] = 100`
- To change points, modify `frontend/final.html` line 104:
```javascript
const points = 100; // Change this value
```

---

## 📊 Scoring System

### Point Distribution

| Phase | Points per Question/Task | Maximum Points |
|-------|--------------------------|----------------|
| Phase 1 (Quiz) | 10 points per correct answer | 50 points (5 questions) |
| Phase 2 (DSA) | 50 points for completion | 50 points |
| Phase 3 (Final) | 100 points for completion | 100 points |
| **Total** | - | **200 points** |

### Modifying Points

#### Phase 1 Points
- Location: `backend/app.py` (line 122)
- Change: `points = score * 10` (10 points per answer)

#### Phase 2 Points
- Location: `static/js/dsa.js` (line 104)
- Change: `const points = 50;`

#### Phase 3 Points
- Location: `frontend/final.html` (line 104)
- Change: `const points = 100;`

### Total Score Calculation

Total score is automatically calculated in:
- Backend: `backend/app.py` → `/api/get-total-score` endpoint
- Frontend: `frontend/score.html` → displays all scores

---

## 🧪 Testing Your Changes

### Testing Phase 1 Questions

1. **Start the server**:
   ```bash
   python backend/app.py
   ```

2. **Navigate to**: `http://localhost:5000/quiz.html`

3. **Check**:
   - Questions appear correctly
   - Options are clickable
   - Answers can be selected
   - Score is calculated correctly

4. **Test API directly**:
   ```bash
   curl http://localhost:5000/api/quiz
   ```

### Testing Phase 2 DSA Challenge

1. **Navigate to**: `http://localhost:5000/dsa.html`

2. **Test**:
   - Drag and drop functionality
   - Validation logic
   - Correct/incorrect solutions
   - Points awarded on completion

3. **Check browser console** for any JavaScript errors

### Testing Phase 3 HackerRank Link

1. **Navigate to**: `http://localhost:5000/final.html`

2. **Click**: "ENTER FINAL CHALLENGE"

3. **Verify**:
   - Modal appears
   - HackerRank link opens (if configured)
   - Points are recorded
   - Redirect to score page works

### Testing Score Page

1. **Complete all phases**

2. **Navigate to**: `http://localhost:5000/score.html`

3. **Verify**:
   - All phase scores display correctly
   - Total score is accurate
   - Percentage is calculated correctly

---

## 🐛 Troubleshooting

### Questions Not Displaying

1. **Check backend is running**: `python backend/app.py`
2. **Check browser console** for errors
3. **Verify API endpoint**: Visit `http://localhost:5000/api/quiz`
4. **Check question format** in `quiz_data.py` (JSON syntax)

### Phase 2 Not Validating

1. **Check browser console** for JavaScript errors
2. **Verify BST logic** in `dsa.js`
3. **Check HTML structure** matches validation logic

### HackerRank Link Not Working

1. **Verify URL** is correct and accessible
2. **Check browser popup blocker** settings
3. **Test link** in a new tab manually
4. **Check console** for JavaScript errors

---

## 📝 Best Practices

1. **Question Formatting**:
   - Keep questions concise and clear
   - Use consistent option formatting
   - Ensure answers are unambiguous

2. **DSA Challenges**:
   - Test validation logic thoroughly
   - Provide clear instructions
   - Consider difficulty progression

3. **HackerRank Integration**:
   - Test links before deployment
   - Provide clear challenge descriptions
   - Consider user experience (new tab vs same tab)

4. **Code Organization**:
   - Keep questions in `quiz_data.py`
   - Keep DSA logic in `dsa.js`
   - Keep HackerRank config in `final.html`

---

## 📞 Support

For issues or questions:
1. Check browser console for errors
2. Check backend terminal for server errors
3. Verify all file paths are correct
4. Ensure Flask server is running

---

**Last Updated**: 2024
**Version**: 1.0

