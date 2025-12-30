from flask import Flask, jsonify, request, session, render_template, send_from_directory, Response
from flask_cors import CORS
from quiz_data import QUIZ_QUESTIONS
import os
import requests

# Use the provided Webhook URL as a default if env var is not set
SHEET_WEBHOOK_URL = os.environ.get("SHEET_WEBHOOK_URL", "https://script.google.com/macros/s/AKfycbwVCL3K613GQKKFYjfb7ShGJ2B4cp39_X_OCQfxc-NDVd9jB-j_dAxiDLkTOHlnxfJN/exec")

def send_score_to_sheet(payload):
    if not SHEET_WEBHOOK_URL:
        return
    try:
        requests.post(SHEET_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        print("Google Sheet error:", e)

# Initialize Flask App with explicit folder paths for the requested structure
# codeverse/backend/app.py
# codeverse/frontend/templates (HTML)
# codeverse/static (CSS/JS)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
TEMPLATE_DIR = os.path.join(PARENT_DIR, 'frontend')
STATIC_DIR = os.path.join(PARENT_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = os.environ.get('SECRET_KEY', 'AVENGERS_ASSEMBLE_SECRET_KEY')  # Use env var in production
CORS(app)

# Configuration
PASSING_SCORE = 0  # No minimum - allow all users to proceed

# Database Setup
import sqlite3
import csv
import io
from datetime import datetime

DB_PATH = os.path.join(BASE_DIR, 'participants.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            rollno TEXT PRIMARY KEY,
            username TEXT,
            email TEXT,
            phase1_score INTEGER DEFAULT 0,
            phase2_score INTEGER DEFAULT 0,
            phase3_score INTEGER DEFAULT 0,
            total_score INTEGER DEFAULT 0,
            login_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize DB on start
init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/phases.html')
def phases():
    if not session.get('rollno'):
        return render_template('login.html') # Redirect to login if session expired
    return render_template('phases.html')

@app.route('/quiz.html')
def quiz_page():
    return render_template('quiz.html')

@app.route('/dsa.html')
def dsa_page():
    return render_template('dsa.html')

@app.route('/final.html')
def final_page():
    return render_template('final.html')

@app.route('/score.html')
def score_page():
    return render_template('score.html')

# Add route to serve static files directly (for debugging)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)

# Test endpoint to verify API is working
@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({"status": "ok", "message": "API is working", "questions_count": len(QUIZ_QUESTIONS)})

# API Endpoints

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    rollno = data.get('rollno')
    email = data.get('email')

    if not all([username, rollno, email]):
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if user exists to preserve scores if logging in again
    c.execute('SELECT * FROM users WHERE rollno = ?', (rollno,))
    existing_user = c.fetchone()
    
    if existing_user:
        # Update login time and details if changed
        c.execute('''
            UPDATE users SET username = ?, email = ?, login_time = ?
            WHERE rollno = ?
        ''', (username, email, datetime.now().isoformat(), rollno))
    else:
        # Create new user
        c.execute('''
            INSERT INTO users (rollno, username, email, login_time)
            VALUES (?, ?, ?, ?)
        ''', (rollno, username, email, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

    session['username'] = username
    session['rollno'] = rollno
    session['email'] = email
    
    # Load existing scores into session if returning user
    if existing_user:
        session['phase1_score'] = existing_user['phase1_score']
        session['phase2_score'] = existing_user['phase2_score']
        session['phase3_score'] = existing_user['phase3_score']
        # Check completion based on scores (simple logic for now)
        if existing_user['phase1_score'] > 0: session['phase1_completed'] = True
        if existing_user['phase2_score'] > 0: session['phase2_completed'] = True
        if existing_user['phase3_score'] > 0: session['phase3_completed'] = True

    return jsonify({"success": True})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Returns the current user's progress and unlocked phases."""
    user_status = {
        "phase1_completed": session.get('phase1_completed', False),
        "phase2_completed": session.get('phase2_completed', False),
        "phase3_completed": session.get('phase3_completed', False),
        "phase1_unlocked": True,  # All phases unlocked
        "phase2_unlocked": True,  # All phases unlocked
        "phase3_unlocked": True,  # All phases unlocked
        "phase1_score": session.get('phase1_score', 0),
        "phase2_score": session.get('phase2_score', 0),
        "phase3_score": session.get('phase3_score', 0)
    }
    return jsonify(user_status)

@app.route('/api/quiz', methods=['GET'])
def get_quiz():
    """Returns quiz questions without answers."""
    try:
        # Strip answers for client security
        questions_client = [
            {
                "id": q["id"],
                "question": q["question"],
                "options": q["options"]
            }
            for q in QUIZ_QUESTIONS
        ]
        # print(f"Returning {len(questions_client)} questions")  # Debug log
        # print(f"Questions: {questions_client}")  # Debug log
        response = jsonify(questions_client)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        print(f"Error in get_quiz: {e}")  # Debug log
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/submit-quiz', methods=['POST'])
def submit_quiz():
    """Evaluates quiz answers and updates session."""
    data = request.json
    answers = data.get('answers', {})
    time_up = data.get('timeUp', False)
    questions_attempted = data.get('questionsAttempted', len(answers))
    
    score = 0
    results = []
    
    for q in QUIZ_QUESTIONS:
        qid = q['id']  # Keep as integer for consistency
        user_ans = answers.get(str(qid)) or answers.get(qid)  # Handle both string and int keys
        correct = (user_ans == q['answer']) if user_ans else False
        if correct:
            score += 1
        results.append({
            "id": q['id'],
            "correct": correct,
            "user_answer": user_ans,
            "correct_answer": q['answer'],
            "attempted": user_ans is not None
        })
    
    # Always allow users to proceed regardless of score
    passed = True  # Always true - no restrictions
    points = score * 5  # 5 points per correct answer (50 points max for 10 questions)
    
    # Store score and completion status
    session['phase1_completed'] = True  # Always mark as completed
    session['phase1_score'] = points
    session['phase1_max_score'] = 50  # Fixed at 50 points max
    session['phase1_time_up'] = time_up
    session['phase1_questions_attempted'] = questions_attempted

    if session.get('rollno'):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE users SET phase1_score = ? WHERE rollno = ?', (points, session['rollno']))
        conn.commit()
        conn.close()

        # Send to Google Sheet
        send_score_to_sheet({
            "rollno": session.get("rollno"),
            "username": session.get("username"),
            "email": session.get("email"),
            "phase": "Phase 1 - Quiz",
            "score": points,
            "max_score": 50
        })
    
    return jsonify({
        "score": score,
        "total": len(QUIZ_QUESTIONS),
        "points": points,
        "max_points": 50,  # Fixed at 50 points max
        "passed": passed,
        "results": results
    })

@app.route('/api/complete-phase-2', methods=['POST'])
def complete_phase_2():
    """Endpoint to mark Phase 2 (DSA) as complete."""
    data = request.json or {}
    points = data.get('points', 50)  # Default 50 points for completing DSA
    
    session['phase2_completed'] = True
    session['phase2_score'] = points
    session['phase2_max_score'] = 50
    
    # Update DB
    if session.get('rollno'):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE users SET phase2_score = ? WHERE rollno = ?', (points, session['rollno']))
        conn.commit()
        conn.close()
        
        # Send to Google Sheet
        send_score_to_sheet({
            "rollno": session.get("rollno"),
            "username": session.get("username"),
            "email": session.get("email"),
            "phase": "Phase 2 - DSA",
            "score": points,
            "max_score": 50
        })

    return jsonify({
        "success": True, 
        "message": "Phase 2 Completed. Power Stone Acquired.",
        "points": points
    })

@app.route('/api/complete-phase-3', methods=['POST'])
def complete_phase_3():
    """Endpoint to mark Phase 3 (Final) as complete. Points come from HackerRank performance."""
    data = request.json or {}
    points = data.get('points', 0)  # Points from HackerRank leaderboard (0 by default)
    
    # Mark as started/participated, but points come from HackerRank
    session['phase3_started'] = True
    session['phase3_score'] = points  # Will be updated based on HackerRank results
    session['phase3_max_score'] = 100  # Max possible points
    
    # Update DB
    if session.get('rollno'):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE users SET phase3_score = ? WHERE rollno = ?', (points, session['rollno']))
        conn.commit()
        conn.close()

        # Send to Google Sheet
        send_score_to_sheet({
            "rollno": session.get("rollno"),
            "username": session.get("username"),
            "email": session.get("email"),
            "phase": "Phase 3 - Final",
            "score": points,
            "max_score": 100
        })
    
    return jsonify({
        "success": True,
        "message": "Phase 3 participation recorded. Points will be based on HackerRank performance.",
        "points": points
    })

@app.route('/api/get-total-score', methods=['GET'])
def get_total_score():
    """Returns total score across all phases."""
    phase1_score = session.get('phase1_score', 0)
    phase2_score = session.get('phase2_score', 0)
    phase3_score = session.get('phase3_score', 0)
    
    phase1_max = session.get('phase1_max_score', 50)
    phase2_max = session.get('phase2_max_score', 50)
    phase3_max = session.get('phase3_max_score', 100)
    
    # Phase 3 is optional - only count if user participated
    phase3_started = session.get('phase3_started', False)
    
    total_score = phase1_score + phase2_score + (phase3_score if phase3_started else 0)
    total_max = phase1_max + phase2_max + (phase3_max if phase3_started else 0)
    
    # Update Total in DB
    if session.get('rollno'):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE users SET total_score = ? WHERE rollno = ?', (total_score, session['rollno']))
        conn.commit()
        conn.close()

    return jsonify({
        "phase1_score": phase1_score,
        "phase1_max": phase1_max,
        "phase2_score": phase2_score,
        "phase2_max": phase2_max,
        "phase3_score": phase3_score,
        "phase3_max": phase3_max,
        "phase3_started": phase3_started,
        "total_score": total_score,
        "total_max": total_max,
        "percentage": round((total_score / total_max * 100) if total_max > 0 else 0, 2)
    })

@app.route('/api/admin/export', methods=['GET'])
def export_data():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    users = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Roll No', 'Username', 'Email', 'Phase 1 Score', 'Phase 2 Score', 'Phase 3 Score', 'Total Score', 'Last Login'])
    
    for user in users:
        # Calculate total if not set properly
        total = user['total_score']
        if total == 0:
            total = user['phase1_score'] + user['phase2_score'] + user['phase3_score']
            
        writer.writerow([
            user['rollno'], 
            user['username'], 
            user['email'], 
            user['phase1_score'],
            user['phase2_score'],
            user['phase3_score'],
            total,
            user['login_time']
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=participants_scores.csv"}
    )

@app.route('/api/reset', methods=['POST'])
def reset_progress():
    """Dev tool to reset session."""
    session.clear()
    return jsonify({"success": True, "message": "Timeline Reset."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
