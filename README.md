<div align="center">

# 🚀 CodeVerse

### Interactive Coding & DSA Challenge Platform

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

*A multi-phase competitive coding event platform with real-time score tracking, quiz battles, and DSA challenges — themed around the Marvel Avengers universe.*

</div>

---

## 📖 Table of Contents

- [About](#-about)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Running Locally](#running-locally)
- [API Reference](#-api-reference)
- [Deployment](#-deployment-on-render)
- [Database Schema](#-database-schema)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 About

**CodeVerse** is a web-based competitive platform designed to host coding events for students and developers. Participants tackle three progressive phases — a timed MCQ quiz, interactive DSA tree challenges, and an external coding round — while their scores are tracked in real time on a live leaderboard.

The platform is **Marvel Avengers themed**, making the experience engaging and fun for participants.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **Multi-Phase Challenges** | Three distinct rounds of increasing difficulty |
| ⏸️ **Pause & Resume** | Progress is saved to DB — participants can continue anytime |
| 🏆 **Live Leaderboard** | Real-time score visibility after Phase 3 completion |
| 🔐 **Session Management** | Secure server-side sessions with 2-hour lifetime |
| 📊 **Admin Score Export** | Download participant scores as a CSV file |
| 📱 **Responsive UI** | Works on desktop and mobile browsers |
| ☁️ **Cloud Deployed** | Hosted on Render with Supabase as the cloud database |

### Phase Breakdown

```
Phase 1 — MCQ Quiz
   ↓  10 Marvel-themed DSA & OOPs questions
   ↓  Timed, one-attempt per question

Phase 2 — DSA Challenge
   ↓  Interactive Binary Search Tree & Red-Black Tree problems
   ↓  Unlimited time

Phase 3 — Coding Round
   ↓  Redirects to an external platform (e.g., HackerRank)
   ↓  Score submitted manually or via API
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Backend** | Python 3.10+, Flask |
| **Database** | PostgreSQL via [Supabase](https://supabase.com/) |
| **Session** | Flask server-side sessions |
| **Deployment** | [Render](https://render.com/) (Gunicorn WSGI) |
| **Version Control** | Git & GitHub |

---

## 📁 Project Structure

```
CodeVerse/
├── backend/
│   ├── app.py              # Main Flask application & all API routes
│   ├── quiz_data.py        # MCQ question bank
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Landing page
│   ├── login.html          # Participant login
│   ├── phases.html         # Phase selection dashboard
│   ├── quiz.html           # Phase 1 — MCQ quiz
│   ├── dsa.html            # Phase 2 — DSA challenges
│   ├── final.html          # Phase 3 — External coding round
│   └── score.html          # Leaderboard & scores
├── static/
│   ├── css/                # Stylesheets
│   └── js/                 # Client-side scripts
├── .env.example            # Environment variable template
├── .gitignore
├── render.yaml             # Render deployment configuration
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** → [Download](https://www.python.org/downloads/)
- **pip** (comes with Python)
- A **Supabase** project → [Create free account](https://supabase.com/)

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/HariMuthuGanesh/CodeVerse.git
cd CodeVerse
```

**2. Install Python dependencies**

```bash
pip install -r backend/requirements.txt
```

### Environment Variables

**3. Copy the example env file and fill in your values**

```bash
# Linux / Mac
cp .env.example .env

# Windows
copy .env.example .env
```

Open `.env` and set the following:

| Variable | Description | Where to find it |
|---|---|---|
| `SECRET_KEY` | Random secret for Flask sessions | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `SUPABASE_URL` | Your Supabase project URL | Supabase Dashboard → Project Settings → API |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Supabase Dashboard → Project Settings → API → `service_role` |

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

### Running Locally

**4. Start the Flask development server**

```bash
cd backend
python app.py
```

**5. Open in your browser**

```
http://localhost:5000
```

The app runs in **debug mode** locally — the server will auto-reload on file changes.

---

## 📡 API Reference

All API endpoints require an active session (login first via `/api/login`).

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/login` | Authenticate participant (email + username) |
| `GET` | `/api/session-status` | Get current session & phase completion status |
| `GET` | `/api/quiz` | Fetch Phase 1 quiz questions |
| `POST` | `/api/submit-quiz` | Submit Phase 1 answers & get score |
| `GET` | `/api/phase2-status` | Get Phase 2 progress |
| `POST` | `/api/submit-phase2` | Submit Phase 2 score |
| `POST` | `/api/submit-phase3` | Submit Phase 3 completion |
| `GET` | `/api/scores` | Get current participant's scores |
| `GET` | `/api/leaderboard` | Get all participants' scores (leaderboard) |
| `GET` | `/api/export-csv` | Download all scores as CSV (admin) |
| `POST` | `/api/logout` | Clear session |

---

## ☁️ Deployment on Render

This project is pre-configured for [Render](https://render.com/) via `render.yaml`.

**Steps to deploy:**

1. **Fork** this repository to your GitHub account
2. Go to [render.com](https://render.com/) → **New Web Service** → Connect your GitHub repo
3. Render will auto-detect `render.yaml` and configure the service
4. Add your **environment variables** in the Render dashboard:
   - `SECRET_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
5. Click **Deploy** — your app will be live in minutes!

The start command used by Render:
```bash
cd backend && gunicorn app:app
```

---

## 🗄️ Database Schema

The app uses a single `participants` table in Supabase (PostgreSQL):

```sql
CREATE TABLE participants (
    email         TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    phase1_score  INTEGER,
    phase2_score  INTEGER,
    phase3_score  INTEGER,
    total_score   INTEGER,
    updated_at    TIMESTAMP
);
```

> Scores are initialized as `NULL` on first login and updated upon phase submission.

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes and commit: `git commit -m "Add: your feature description"`
4. Push to your branch: `git push origin feature/your-feature-name`
5. Open a **Pull Request** on GitHub

Please make sure to:
- Follow existing code style
- Test your changes locally before submitting
- Never commit `.env` or any secret keys

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ by [HariMuthuGanesh](https://github.com/HariMuthuGanesh)

⭐ Star this repo if you found it useful!

</div>
