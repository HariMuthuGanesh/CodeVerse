from flask import Flask, jsonify, request, session, render_template, send_from_directory, Response
from flask_cors import CORS
from supabase import create_client, Client
from quiz_data import QUIZ_QUESTIONS
import os
import io
import csv
from datetime import datetime

# Initialize Flask App
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
TEMPLATE_DIR = os.path.join(PARENT_DIR, 'frontend')
STATIC_DIR = os.path.join(PARENT_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = os.environ.get('SECRET_KEY', 'AVENGERS_ASSEMBLE_SECRET_KEY')
CORS(app)

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase Init Error: {e}")

# Configuration
PASSING_SCORE = 0

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/phases.html')
def phases():
    if not session.get('rollno'):
        return render_template('login.html')
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

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)

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

    # Store in session
    session['username'] = username
    session['rollno'] = rollno
    session['email'] = email
    
    # Retrieve past scores from Supabase to restore session state
    if supabase:
        try:
            # Check if user exists
            response = supabase.table('participants').select("*").eq('email', email).execute()
            data_rows = response.data
            
            if data_rows:
                user_data = data_rows[0]
                # Reset session scores
                session['phase1_score'] = 0
                session['phase2_score'] = 0
                session['phase3_score'] = 0

                # Populate based on Supabase data
                if user_data.get('phase1_score') is not None:
                    session['phase1_score'] = user_data['phase1_score']
                    session['phase1_completed'] = True
                
                if user_data.get('phase2_score') is not None:
                    session['phase2_score'] = user_data['phase2_score']
                    session['phase2_completed'] = True
                
                if user_data.get('phase3_score') is not None:
                    session['phase3_score'] = user_data['phase3_score']
                    session['phase3_completed'] = True
            
        except Exception as e:
            print(f"Login Supabase Error: {e}")
            # Continue login even if DB fails, treating as new session locally

    return jsonify({"success": True})

@app.route('/api/status', methods=['GET'])
def get_status():
    user_status = {
        "phase1_completed": session.get('phase1_completed', False),
        "phase2_completed": session.get('phase2_completed', False),
        "phase3_completed": session.get('phase3_completed', False),
        "phase1_unlocked": True,
        "phase2_unlocked": True,
        "phase3_unlocked": True,
        "phase1_score": session.get('phase1_score', 0),
        "phase2_score": session.get('phase2_score', 0),
        "phase3_score": session.get('phase3_score', 0)
    }
    return jsonify(user_status)

@app.route('/api/quiz', methods=['GET'])
def get_quiz():
    try:
        questions_client = [
            {
                "id": q["id"],
                "question": q["question"],
                "options": q["options"]
            }
            for q in QUIZ_QUESTIONS
        ]
        response = jsonify(questions_client)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/submit-quiz', methods=['POST'])
def submit_quiz():
    data = request.json
    answers = data.get('answers', {})
    time_up = data.get('timeUp', False)
    questions_attempted = data.get('questionsAttempted', len(answers))
    
    score = 0
    results = []
    
    for q in QUIZ_QUESTIONS:
        qid = q['id']
        user_ans = answers.get(str(qid)) or answers.get(qid)
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
    
    points = score * 5
    
    # Store score and completion status in Session
    session['phase1_completed'] = True
    session['phase1_score'] = points
    session['phase1_max_score'] = 50
    session['phase1_time_up'] = time_up
    session['phase1_questions_attempted'] = questions_attempted

    # Store in Supabase
    if session.get('email') and supabase:
        try:
            # Upsert participant data
            user_data = {
                "name": session.get('username'),
                "email": session.get('email'),
                "phase1_score": points,
                # we don't overwrite total_score here strictly, let's update it
                "total_score": points + session.get('phase2_score', 0) + session.get('phase3_score', 0),
                "created_at": datetime.utcnow().isoformat()
            }
            # We use email as unique key if possible, but upsert usually needs a constraint.
            # Assuming 'participants' table has a unique constraint on email.
            supabase.table('participants').upsert(user_data, on_conflict='email').execute()
        except Exception as e:
            print(f"Supabase Error submit-quiz: {e}")

    return jsonify({
        "score": score,
        "total": len(QUIZ_QUESTIONS),
        "points": points,
        "max_points": 50,
        "passed": True,
        "results": results
    })

@app.route('/api/complete-phase-2', methods=['POST'])
def complete_phase_2():
    data = request.json or {}
    points = data.get('points', 50)
    
    session['phase2_completed'] = True
    session['phase2_score'] = points
    session['phase2_max_score'] = 50
    
    if session.get('email') and supabase:
        try:
            current_total = session.get('phase1_score', 0) + points + session.get('phase3_score', 0)
            user_data = {
                "name": session.get('username'),
                "email": session.get('email'),
                "phase2_score": points,
                "total_score": current_total
            }
            supabase.table('participants').upsert(user_data, on_conflict='email').execute()
        except Exception as e:
            print(f"Supabase Error complete-phase-2: {e}")

    return jsonify({
        "success": True, 
        "message": "Phase 2 Completed. Power Stone Acquired.",
        "points": points
    })

@app.route('/api/complete-phase-3', methods=['POST'])
def complete_phase_3():
    data = request.json or {}
    points = data.get('points', 0)
    
    session['phase3_started'] = True
    session['phase3_score'] = points
    session['phase3_max_score'] = 100
    
    if session.get('email') and supabase:
        try:
            current_total = session.get('phase1_score', 0) + session.get('phase2_score', 0) + points
            user_data = {
                "name": session.get('username'),
                "email": session.get('email'),
                "phase3_score": points,
                "total_score": current_total
            }
            supabase.table('participants').upsert(user_data, on_conflict='email').execute()
        except Exception as e:
            print(f"Supabase Error complete-phase-3: {e}")
    
    return jsonify({
        "success": True,
        "message": "Phase 3 participation recorded.",
        "points": points
    })

@app.route('/api/get-total-score', methods=['GET'])
def get_total_score():
    phase1_score = session.get('phase1_score', 0)
    phase2_score = session.get('phase2_score', 0)
    phase3_score = session.get('phase3_score', 0)
    
    phase1_max = session.get('phase1_max_score', 50)
    phase2_max = session.get('phase2_max_score', 50)
    phase3_max = session.get('phase3_max_score', 100)
    
    phase3_started = session.get('phase3_started', False)
    
    total_score = phase1_score + phase2_score + (phase3_score if phase3_started else 0)
    total_max = phase1_max + phase2_max + (phase3_max if phase3_started else 0)
    
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

    try:
        if not supabase:
             return "Supabase not configured", 500

        # Fetch all scores from Supabase
        response = supabase.table('participants').select("*").execute()
        participants = response.data

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Name', 'Email', 'Phase 1 Score', 'Phase 2 Score', 'Phase 3 Score', 'Total Score', 'Created At'])

        for p in participants:
            writer.writerow([
                p.get('name', ''),
                p.get('email', ''),
                p.get('phase1_score', 0),
                p.get('phase2_score', 0),
                p.get('phase3_score', 0),
                p.get('total_score', 0),
                p.get('created_at', '')
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=participants_scores.csv"}
        )
    except Exception as e:
        return str(e), 500

@app.route('/api/debug/scores', methods=['GET'])
def debug_scores():

    try:
        if not supabase:
             return jsonify({"error": "Supabase not configured"})

        # Fetch top scores
        response = supabase.table('participants').select("*").order('total_score', desc=True).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def reset_progress():
    session.clear()
    return jsonify({"success": True, "message": "Timeline Reset."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
