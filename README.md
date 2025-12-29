# CodeVerse - The Avengers Coding War

**CodeVerse** is an immersive, cinematic coding event website inspired by the MCU Multiverse. Participants must conquer three phases to collect the Infinity Stones and prove their coding prowess.

## 🚀 Features

- **Cinematic UI**: Dark mode, Neon glows, Glassmorphism, and Parallax effects.
- **Interactive Phases**:
    1.  **Mind Stone (Quiz)**: Test your logic and coding knowledge.
    2.  **Time Stone (DSA)**: Drag-and-drop Binary Tree construction.
    3.  **Power Stone (Final)**: Redirect to the ultimate HackerRank challenge.
- **Gamification**: Session-based progress tracking, unlocking phases sequentially.
- **Custom Cursor**: Anti-gravity cursor with trailing effects.

## 🛠 Tech Stack

- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript (ES6)
- **Backend**: Python Flask
- **State Management**: Flask Sessions / Client-side Cookies

## 📦 Setup Instructions

1.  **Clone/Open the project** in your terminal.
2.  **Navigate to the project root** (`d:/codeverse`).
3.  **Install dependencies**:
    ```bash
    pip install -r backend/requirements.txt
    ```
4.  **Run the application**:
    ```bash
    python backend/app.py
    ```
5.  **Access the Multiverse**:
    Open `http://localhost:5000` in your browser.

## 📂 Structure

```
codeverse/
├── backend/        # Flask app and data
├── frontend/       # HTML Templates
├── static/         # CSS and JS assets
└── README.md
```

## 🎮 How to Play

1.  Click **"Enter the Multiverse"** on the landing page.
2.  Select **Phase 1** (Mind Stone). Complete the quiz to unlock the next phase.
3.  Enter **Phase 2** (Time Stone). Drag numbers to build a valid Binary Search Tree.
4.  Unlock **Phase 3** (Power Stone) and proceed to the final challenge.

## 👨‍💻 For Developers

**📖 [See DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) for detailed instructions on:**
- Adding quiz questions for Phase 1
- Configuring Phase 2 (DSA Challenge) questions
- Setting up HackerRank links for Phase 3
- Understanding the scoring system
- Testing and troubleshooting

### Quick Reference

- **Quiz Questions**: `backend/quiz_data.py`
- **Phase 2 Config**: `static/js/dsa.js` and `frontend/dsa.html`
- **HackerRank Link**: `frontend/final.html` (line 102-118)
- **Scoring**: Points are calculated automatically (10/50/100 per phase)

---
*Built with ❤️ and Vibranium.*
