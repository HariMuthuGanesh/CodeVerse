# Quick Reference Guide - CodeVerse

Quick reference for common developer tasks.

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run server
python backend/app.py

# Access application
http://localhost:5000
```

---

## 📝 Adding a Quiz Question (Phase 1)

**File**: `backend/quiz_data.py`

```python
{
    "id": 6,  # Next sequential number
    "question": "Your question here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Option A"  # Must match exactly
}
```

**Add to**: `QUIZ_QUESTIONS` list

---

## 🌳 Changing Phase 2 Numbers

**File**: `frontend/dsa.html` (line 127-133)

Change the `data-value` and text content:
```html
<div class="draggable" data-value="20">20</div>
```

**Update validation**: `static/js/dsa.js` (line 107-120)

---

## 🔗 Setting HackerRank Link

**File**: `frontend/final.html` (line 104)

```javascript
window.open('https://www.hackerrank.com/challenges/YOUR_CHALLENGE', '_blank');
```

---

## 📊 Changing Points

| Phase | File | Line | Variable |
|-------|------|------|----------|
| Phase 1 | `backend/app.py` | 122 | `points = score * 10` |
| Phase 2 | `static/js/dsa.js` | 104 | `const points = 50;` |
| Phase 3 | `frontend/final.html` | 104 | `const points = 100;` |

---

## 🧪 Testing Endpoints

```bash
# Test quiz API
curl http://localhost:5000/api/quiz

# Test status API
curl http://localhost:5000/api/status

# Test score API
curl http://localhost:5000/api/get-total-score
```

---

## 📁 File Locations

| Component | File Path |
|-----------|-----------|
| Quiz Questions | `backend/quiz_data.py` |
| Phase 2 Logic | `static/js/dsa.js` |
| Phase 2 HTML | `frontend/dsa.html` |
| HackerRank Config | `frontend/final.html` |
| Score Display | `frontend/score.html` |
| Main CSS | `static/css/main.css` |
| Backend Routes | `backend/app.py` |

---

## 🐛 Common Issues

### Questions not showing?
- Check backend is running
- Check browser console (F12)
- Verify `backend/quiz_data.py` syntax

### Phase 2 not validating?
- Check browser console for errors
- Verify BST logic in `dsa.js`
- Ensure all nodes are placed

### HackerRank link not working?
- Verify URL is correct
- Check popup blocker
- Test link manually

---

**For detailed instructions, see [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)**

