from flask import Flask, jsonify, request, session, render_template, send_from_directory, Response, redirect
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
    # Check if user has exited Phase 2
    if session.get('bst_status') == 'exited':
         # Redirect or show message? For now let frontend handle it or redirect to phases
         return redirect('/phases.html')
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
    
    # Defaults
    session['phase1_score'] = 0
    session['phase2_score'] = 0 # Total Phase 2 score (BST + RB)
    session['phase3_score'] = 0
    
    # Phase 2 Specifics
    session['bst_score'] = 0
    session['bst_attempted'] = 0
    session['bst_correct'] = 0
    session['bst_status'] = 'locked' 
    session['rb_score'] = 0
    session['rb_completed'] = False
    session['phase2_time_remaining'] = 600 # 10 minutes default

    # Retrieve past scores from Supabase to restore session state
    if supabase:
        try:
            # Check if user exists
            response = supabase.table('participants').select("*").eq('email', email).execute()
            data_rows = response.data
            
            if data_rows:
                user_data = data_rows[0]
                
                # Phase 1
                if user_data.get('phase1_score') is not None:
                    session['phase1_score'] = user_data['phase1_score']
                    session['phase1_completed'] = True
                
                # Phase 2
                # Restore granular BST data if available
                session['bst_score'] = user_data.get('bst_score', 0)
                session['bst_attempted'] = user_data.get('bst_attempted', 0)
                session['bst_correct'] = user_data.get('bst_correct', 0)
                session['bst_status'] = user_data.get('bst_status', 'locked')
                session['rb_score'] = user_data.get('rb_score', 0)
                session['rb_completed'] = user_data.get('rb_completed', False)
                session['phase2_time_remaining'] = user_data.get('phase2_time_remaining', 600)
                
                # Total Phase 2 Score logic:
                # If we rely on stored phase2_score, use it. Or recompute.
                # Let's rely on granular parts if possible, or fallback.
                p2_total = user_data.get('phase2_score')
                if p2_total is not None:
                    session['phase2_score'] = p2_total
                    session['phase2_completed'] = (session['bst_status'] == 'completed' or session['bst_status'] == 'exited')
                
                # Phase 3
                if user_data.get('phase3_score') is not None:
                    session['phase3_score'] = user_data['phase3_score']
                    session['phase3_completed'] = True
            
        except Exception as e:
            print(f"Login Supabase Error: {e}")
            # Continue login even if DB fails, treating as new session locally

    return jsonify({"success": True})

@app.route('/api/status', methods=['GET'])
def get_status():
    bst_status = session.get('bst_status', 'locked')
    phase1_completed = session.get('phase1_completed', False)
    
    # Unlock Phase 2 if Phase 1 is done
    if phase1_completed and bst_status == 'locked':
        bst_status = 'in_progress'
        session['bst_status'] = 'in_progress'

    user_status = {
        "phase1_completed": phase1_completed,
        "phase2_completed": session.get('phase2_completed', False),
        "phase3_completed": session.get('phase3_completed', False),
        "phase1_unlocked": True,
        "phase2_unlocked": phase1_completed,
        "phase3_unlocked": session.get('phase2_completed', False),
        "phase1_score": session.get('phase1_score', 0),
        "phase2_score": session.get('phase2_score', 0),
        "phase3_score": session.get('phase3_score', 0),
        
        # Detailed Phase 2 Status
        "phase2_details": {
            "bst": {
                "score": session.get('bst_score', 0),
                "attempted": session.get('bst_attempted', 0),
                "correct": session.get('bst_correct', 0),
                "status": bst_status
            },
            "rb": {
                "score": session.get('rb_score', 0),
                "completed": session.get('rb_completed', False)
            },
            "time_remaining": session.get('phase2_time_remaining', 600)
        }
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
                "total_score": points + session.get('phase2_score', 0) + session.get('phase3_score', 0),
                "created_at": datetime.utcnow().isoformat()
            }
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

# --- PHASE 2 NEW ENDPOINTS ---

@app.route('/api/bst/update', methods=['POST'])
def update_bst_score():
    """Updates BST score per question"""
    data = request.json
    correct = data.get('correct', False)
    # We just increment, logic is on frontend for which question.
    # But safeguard: just add points if correct.
    
    if correct:
        session['bst_score'] = session.get('bst_score', 0) + 5
        session['bst_correct'] = session.get('bst_correct', 0) + 1
    
    session['bst_attempted'] = session.get('bst_attempted', 0) + 1
    
    # Update Total Phase 2 Score
    session['phase2_score'] = session.get('bst_score', 0) + session.get('rb_score', 0)
    
    save_phase2_progress()
    
    return jsonify({
        "success": True,
        "bst_score": session['bst_score'],
        "total_phase2_score": session['phase2_score']
    })

@app.route('/api/rb/complete', methods=['POST'])
def complete_rb():
    """Completes Red-Black Tree Challenge"""
    points = 25 # Fixed points for RB
    session['rb_score'] = points
    session['rb_completed'] = True
    
    # Update Total Phase 2 Score
    session['phase2_score'] = session.get('bst_score', 0) + session.get('rb_score', 0)
    
    save_phase2_progress()
    
    return jsonify({
        "success": True,
        "rb_score": points,
        "total_phase2_score": session['phase2_score']
    })

@app.route('/api/phase2/timer', methods=['POST'])
def update_phase2_timer():
    """Saves remaining time"""
    data = request.json
    time_remaining = data.get('time_remaining', 600)
    session['phase2_time_remaining'] = time_remaining
    
    # We can optimize and not hit DB every second, but maybe on leave/pause
    # If user just pings this periodically.
    # Let's save to DB heavily? No, maybe just session. 
    # But session is unreliable if server restarts. 
    # Let's try to save to DB if it's a "pause" event or periodically.
    
    if data.get('save_to_db'):
        save_phase2_progress()
        
    return jsonify({"success": True})

@app.route('/api/phase2/exit', methods=['POST'])
def exit_phase2():
    """User chooses to Leave Round (Finish) or Autocomplete"""
    session['bst_status'] = 'exited'
    session['phase2_completed'] = True
    
    save_phase2_progress()
    
    return jsonify({
        "success": True,
        "bst_status": "exited",
        "final_phase2_score": session.get('phase2_score', 0)
    })

def save_phase2_progress():
    """Helper to sync Phase 2 session data to Supabase"""
    if session.get('email') and supabase:
        try:
            current_total = session.get('phase1_score', 0) + session.get('phase2_score', 0) + session.get('phase3_score', 0)
            user_data = {
                "name": session.get('username'),
                "email": session.get('email'),
                "phase2_score": session.get('phase2_score', 0),
                "total_score": current_total,
                "bst_score": session.get('bst_score', 0),
                "bst_attempted": session.get('bst_attempted', 0),
                "bst_correct": session.get('bst_correct', 0),
                "bst_status": session.get('bst_status', 'in_progress'),
                "rb_score": session.get('rb_score', 0),
                "rb_completed": session.get('rb_completed', False),
                "phase2_time_remaining": session.get('phase2_time_remaining', 600)
            }
            supabase.table('participants').upsert(user_data, on_conflict='email').execute()
        except Exception as e:
            print(f"Supabase Error save_phase2: {e}")

# Legacy endpoint redirect or specific handler
@app.route('/api/complete-phase-2', methods=['POST'])
def complete_phase_2():
    # This might be called by old code or as a fallback
    return exit_phase2()

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
    phase2_max = 50 # 25 RB + 25 BST (approx, 5 questions * 5 pts = 25)
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
