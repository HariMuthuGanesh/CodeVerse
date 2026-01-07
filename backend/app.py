from flask import Flask, jsonify, request, session, render_template, send_from_directory, Response, redirect
from flask_cors import CORS
from supabase import create_client, Client
from quiz_data import QUIZ_QUESTIONS
import os
import io
import csv
import json
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
    # Check if user has completed/locked Phase 2
    if session.get('phase2_completed'):
         # Allow viewing if completed? Or redirect?
         # User request: "If remaining == 0: Lock Phase-2 permanently".
         # Usually best to stay on page but show locked state.
         pass
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
    session['phase1_completed'] = False
    session['phase3_score'] = 0
    
    # Phase 2 Specifics (Option B)
    session['phase2_score'] = 0
    session['phase2_state'] = {}
    session['phase2_started_at'] = None
    session['phase2_completed'] = False
    session['phase2_time_left'] = 900
    
    # Internal component scores (transient in session, persisted in phase2_state)
    session['bst_score'] = 0
    session['rb_score'] = 0
    session['detective_score'] = 0

    # Retrieve past scores from Supabase to restore session state
    if supabase:
        try:
            # Check if user exists
            response = supabase.table('participants').select("*").eq('email', email).execute()
            data_rows = response.data
            
            # SESSION FLAG: Mark this session as having valid DB data
            session['db_synced'] = True
            
            if data_rows:
                user_data = data_rows[0]
                
                # Phase 1 Restoration
                p1_score = user_data.get('phase1_score')
                if p1_score is not None:
                    session['phase1_score'] = p1_score
                    session['phase1_completed'] = True
                else:
                    session['phase1_score'] = 0
                    session['phase1_completed'] = False
                
                # Phase 2 Restoration - STRICT OPTION B
                session['phase2_score'] = user_data.get('phase2_score', 0)
                session['phase2_state'] = user_data.get('phase2_state', {})
                session['phase2_started_at'] = user_data.get('phase2_started_at')
                session['phase2_completed'] = user_data.get('phase2_completed', False)
                session['phase2_time_left'] = user_data.get('phase2_time_left', 900)
                
                # Restore internal scores for calculation
                state = session['phase2_state'] or {}
                session['bst_score'] = state.get('bst_score', 0)
                session['rb_score'] = state.get('rb_score', 0)
                session['detective_score'] = state.get('detective_score', 0)

                # Timer Calculation
                if session['phase2_started_at']:
                    try:
                        start_str = session['phase2_started_at']
                        if start_str.endswith('Z'): start_str = start_str[:-1]
                        
                        # Handle both with and without microseconds
                        try:
                            start_time = datetime.fromisoformat(start_str)
                        except ValueError:
                            # Fallback if format is slightly different
                             start_time = datetime.strptime(start_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")

                        # Valid start time found
                        elapsed = (datetime.utcnow() - start_time).total_seconds()
                        remaining = max(0, 900 - int(elapsed))
                        session['phase2_time_left'] = remaining
                        
                        if remaining == 0 and not session['phase2_completed']:
                             session['phase2_completed'] = True
                             # Logic to sync completion state back to DB later or now?
                             # We'll rely on next sync or exit
                             # But let's set it in session so UI locks immediately
                    except Exception as e:
                        print(f"Timer Parse Error: {e}")
                        session['phase2_time_left'] = 900
                
                # Phase 3
                if user_data.get('phase3_score') is not None:
                    session['phase3_score'] = user_data['phase3_score']
                    session['phase3_completed'] = True
            
        except Exception as e:
            print(f"Login Supabase Error: {e}")
            return jsonify({"error": "Database Unavailable. Please try again."}), 503
    else:
        session['db_synced'] = False 

    return jsonify({"success": True})

@app.route('/api/status', methods=['GET'])
def get_status():
    phase1_completed = session.get('phase1_completed', False)
    phase2_completed = session.get('phase2_completed', False)
    
    # Recalculate Timer if Phase 2 started
    if session.get('phase2_started_at') and not phase2_completed:
        try:
             start_str = session['phase2_started_at']
             if start_str.endswith('Z'): start_str = start_str[:-1]
             start_time = datetime.fromisoformat(start_str)
             elapsed = (datetime.utcnow() - start_time).total_seconds()
             remaining = max(0, 900 - int(elapsed))
             session['phase2_time_left'] = remaining
             if remaining <= 0:
                 session['phase2_completed'] = True
                 phase2_completed = True
        except:
            pass

    user_status = {
        "phase1_completed": phase1_completed,
        "phase2_completed": phase2_completed,
        "phase3_completed": session.get('phase3_completed', False),
        "phase1_unlocked": True,
        "phase2_unlocked": phase1_completed,
        "phase3_unlocked": phase2_completed,
        "phase1_score": session.get('phase1_score', 0),
        "phase2_score": session.get('phase2_score', 0),
        "phase3_score": session.get('phase3_score', 0),
        
        # Detailed Phase 2 Status for Persistence
        "phase2_details": {
             "time_left": session.get('phase2_time_left', 900),
             "started_at": session.get('phase2_started_at'),
             "state": session.get('phase2_state', {}),
             "completed": phase2_completed
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
    
    score = 0
    results = []
    
    for q in QUIZ_QUESTIONS:
        qid = q['id']
        user_ans = answers.get(str(qid)) or answers.get(qid)
        if user_ans == q['answer']:
            score += 1
            
    points = score * 5
    
    session['phase1_completed'] = True
    session['phase1_score'] = points
    
    if session.get('email') and supabase:
        try:
            current_total = points + session.get('phase2_score', 0) + session.get('phase3_score', 0)
            user_data = {
                "name": session.get('username'),
                "email": session.get('email'),
                "phase1_score": points,
                "total_score": current_total,
                "updated_at": datetime.utcnow().isoformat()
            }
            # Remove phase1_status column requirement
            supabase.table('participants').upsert(user_data, on_conflict='email').execute()
        except Exception as e:
            print(f"Supabase Error submit-quiz: {e}")
            
    return jsonify({"success": True, "score": points})

# --- PHASE 2 NEW ENDPOINTS (OPTION B STRICT) ---

@app.route('/api/phase2/sync', methods=['POST'])
def sync_phase2():
    """Syncs Timer, Board State, and Handles Auto-Start"""
    data = request.json
    client_state = data.get('state') 
    
    # 1. Start Phase if not started
    if not session.get('phase2_started_at'):
        start_time = datetime.utcnow().isoformat()
        session['phase2_started_at'] = start_time
        session['phase2_time_left'] = 900
        save_phase2_progress() 

    # 2. Update Timer
    remaining = 900
    try:
        start_str = session['phase2_started_at']
        if start_str.endswith('Z'): start_str = start_str[:-1]
        start_time = datetime.fromisoformat(start_str)
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        remaining = max(0, 900 - int(elapsed))
        session['phase2_time_left'] = remaining
    except Exception as e:
        print(f"Timer check fail: {e}")
        remaining = 900

    # 3. Check Expiry
    if remaining <= 0 or session.get('phase2_completed'):
        session['phase2_completed'] = True
        session['phase2_time_left'] = 0
        save_phase2_progress()
        return jsonify({
            "success": True, 
            "completed": True, 
            "time_left": 0,
            "message": "Time Up"
        })

    # 4. Update State if provided
    if client_state:
        current = session.get('phase2_state') or {}
        if isinstance(client_state, dict):
             current.update(client_state)
             session['phase2_state'] = current
        save_phase2_progress()

    return jsonify({
        "success": True,
        "time_left": remaining,
        "completed": False,
        "started_at": session['phase2_started_at'],
        "state": session.get('phase2_state')
    })

@app.route('/api/bst/submit', methods=['POST'])
def submit_bst():
    if session.get('phase2_completed'): return jsonify({"success": False, "message": "Phase Locked"})
    
    data = request.json
    correct = data.get('correct', False)
    
    state = session.get('phase2_state') or {}
    state['bst_score'] = 40 if correct else 0
    session['phase2_state'] = state # Update session
    session['bst_score'] = 40 if correct else 0 # Update local session for display
    
    calc_phase2_score()
    save_phase2_progress()
    return jsonify({"success": True, "score": state['bst_score']})

@app.route('/api/rb/complete', methods=['POST'])
def complete_rb():
    if session.get('phase2_completed'): return jsonify({"success": False, "message": "Phase Locked"})

    state = session.get('phase2_state') or {}
    state['rb_score'] = 40
    session['phase2_state'] = state
    session['rb_score'] = 40
    
    calc_phase2_score()
    save_phase2_progress()
    return jsonify({"success": True})

@app.route('/api/detective/submit', methods=['POST'])
def submit_detective():
    if session.get('phase2_completed'): return jsonify({"success": False, "message": "Phase Locked"})

    data = request.json
    correct = data.get('correct', False)
    
    state = session.get('phase2_state') or {}
    state['detective_score'] = 20 if correct else 0
    session['phase2_state'] = state
    session['detective_score'] = 20 if correct else 0
    
    calc_phase2_score()
    save_phase2_progress()
    return jsonify({"success": True, "score": state['detective_score']})

def calc_phase2_score():
    state = session.get('phase2_state') or {}
    total = state.get('bst_score', 0) + state.get('rb_score', 0) + state.get('detective_score', 0)
    session['phase2_score'] = total

@app.route('/api/phase2/exit', methods=['POST'])
def exit_phase2():
    session['phase2_completed'] = True
    calc_phase2_score()
    save_phase2_progress()
    return jsonify({"success": True})

def save_phase2_progress():
    if not session.get('email') or not supabase: return

    try:
        user_data = {
            "email": session.get('email'),
            "phase2_score": session.get('phase2_score', 0),
            "phase2_state": session.get('phase2_state', {}),
            "phase2_started_at": session.get('phase2_started_at'),
            "phase2_time_left": session.get('phase2_time_left'),
            "phase2_completed": session.get('phase2_completed', False),
            "total_score": session.get('phase1_score', 0) + session.get('phase2_score', 0) + session.get('phase3_score', 0),
            "updated_at": datetime.utcnow().isoformat()
        }
        if session.get('username'):
            user_data['name'] = session.get('username')
        supabase.table('participants').upsert(user_data, on_conflict='email').execute()
    except Exception as e:
        print(f"Supabase Save Error: {e}")

@app.route('/api/complete-phase-2', methods=['POST'])
def complete_phase_2():
    return exit_phase2()

@app.route('/api/complete-phase-3', methods=['POST'])
def complete_phase_3():
    data = request.json or {}
    points = data.get('points', 0)
    
    session['phase3_started'] = True
    session['phase3_score'] = points
    
    if session.get('email') and supabase:
        try:
            current_total = session.get('phase1_score', 0) + session.get('phase2_score', 0) + points
            user_data = {
                "name": session.get('username'),
                "email": session.get('email'),
                "phase3_score": points,
                "total_score": current_total,
                 "updated_at": datetime.utcnow().isoformat()
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
    phase2_max = 100 
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
