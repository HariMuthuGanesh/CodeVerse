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
    session['phase1_completed'] = False # Explicit Default
    session['phase2_score'] = 0 # Total Phase 2 score (BST + RB + Detective)
    session['phase3_score'] = 0
    
    # Phase 2 Specifics
    session['bst_score'] = 0
    session['bst_status'] = 'locked' 
    session['rb_score'] = 0
    session['rb_completed'] = False
    session['detective_score'] = 0
    session['detective_completed'] = False
    session['phase2_time_remaining'] = 600 # 10 minutes default
    
    # State Persistence for Drag & Drop
    session['bst_state'] = [] # List of {slot: id, value: val}
    session['rb_state'] = [] # List of {slot: id, value: val, color: c}
    session['detective_state'] = [] # List of {slot: id, value: val}

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
                # Check explicit status OR score > 0 (to avoid 0-default bug)
                p1_status = user_data.get('phase1_status')
                p1_score = user_data.get('phase1_score', 0)
                
                # FIX: Trust 'completed' status explicitly, even if score is 0
                if p1_status == 'completed' or (p1_score is not None and p1_score > 0):
                    session['phase1_score'] = p1_score
                    session['phase1_completed'] = True
                else:
                    session['phase1_score'] = 0
                    session['phase1_completed'] = False
                
                # Phase 2
                session['bst_score'] = user_data.get('bst_score', 0)
                session['bst_status'] = user_data.get('bst_status', 'locked')
                session['rb_score'] = user_data.get('rb_score', 0)
                session['rb_completed'] = user_data.get('rb_completed', False)
                session['detective_score'] = user_data.get('detective_score', 0)
                session['detective_completed'] = user_data.get('detective_completed', False)
                session['phase2_time_remaining'] = user_data.get('phase2_time_remaining', 600)
                
                # Restore States (JSON likely)
                session['bst_state'] = user_data.get('bst_state', [])
                session['rb_state'] = user_data.get('rb_state', [])
                session['detective_state'] = user_data.get('detective_state', [])
                
                # Total Phase 2 Score logic:
                p2_total = user_data.get('phase2_score')
                if p2_total is not None:
                    session['phase2_score'] = p2_total
                    session['phase2_completed'] = (session['bst_status'] == 'completed' or session['bst_status'] == 'exited')
                
                # Phase 3
                if user_data.get('phase3_score') is not None:
                    session['phase3_score'] = user_data['phase3_score']
                    session['phase3_completed'] = True
            
            # If no user found, it's a new user, which is fine. session['db_synced'] is True.

        except Exception as e:
            print(f"Login Supabase Error: {e}")
            # CRITICAL: Do NOT continue locally if DB fetch failed.
            # This prevents overwriting cloud data with empty local data later.
            return jsonify({"error": "Database Unavailable. Please try again."}), 503
    else:
        # If Supabase is NOT configured at all on server, we might run in local-only mode
        # But if it WAS expected, this is an issue. taking 'supabase: Client = None' as config missing.
        # Ideally, we should warn. For now, we assume local-dev mode if no keys.
        session['db_synced'] = False 

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
                "status": bst_status,
                "state": session.get('bst_state', [])
            },
            "rb": {
                "score": session.get('rb_score', 0),
                "completed": session.get('rb_completed', False),
                "state": session.get('rb_state', [])
            },
            "detective": {
                "score": session.get('detective_score', 0),
                "completed": session.get('detective_completed', False),
                "state": session.get('detective_state', [])
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
    # Safety Check: Only save if we have a valid synced session OR if supabase was never configured (local mode)
    # But if supabase IS configured, we MUST have db_synced=True to write.
    if session.get('email') and supabase:
        if not session.get('db_synced', False):
            print("Skipping Supabase Write: Session not synced with DB.")
            # We fail silently here to not break the user experience, but we don't overwrite the DB.
            # Ideally, we should warn user.
        else:
            try:
                # Upsert participant data
                user_data = {
                    "name": session.get('username'),
                    "email": session.get('email'),
                    "phase1_score": points,
                    "phase1_status": "completed", # Explicit status
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

@app.route('/api/phase2/sync', methods=['POST'])
def sync_phase2():
    """Syncs Timer and Board State (BST + RB)"""
    data = request.json
    
    # Timer
    if 'time_remaining' in data:
        session['phase2_time_remaining'] = data['time_remaining']
        
    # States
    if 'bst_state' in data:
        session['bst_state'] = data['bst_state']
        
    if 'rb_state' in data:
        session['rb_state'] = data['rb_state']
        
    if 'detective_state' in data:
        session['detective_state'] = data['detective_state']
    
    # Save to DB if requested (e.g., Pause/Leave)
    if data.get('save_to_db'):
        save_phase2_progress()
        return jsonify({"success": True, "saved": True})
        
    return jsonify({"success": True, "saved": False})

@app.route('/api/bst/submit', methods=['POST'])
def submit_bst():
    """Validates and Submits BST Score"""
    
    data = request.json
    correct = data.get('correct', False)
    
    if correct:
        session['bst_score'] = 40 # High weightage (40)
        session['bst_status'] = 'completed'
    else:
        session['bst_score'] = 0
        return jsonify({"success": False, "message": "Invalid BST"})

    # Update Total
    session['phase2_score'] = session.get('bst_score', 0) + session.get('rb_score', 0) + session.get('detective_score', 0)
    save_phase2_progress()
    
    return jsonify({
        "success": True, 
        "bst_score": session['bst_score'],
        "total_phase2_score": session['phase2_score']
    })

@app.route('/api/rb/complete', methods=['POST'])
def complete_rb():
    """Completes Red-Black Tree Challenge"""
    points = 40 # High weightage (40)
    session['rb_score'] = points
    session['rb_completed'] = True
    
    # Update Total Phase 2 Score
    session['phase2_score'] = session.get('bst_score', 0) + session.get('rb_score', 0) + session.get('detective_score', 0)
    
    save_phase2_progress()
    
    return jsonify({
        "success": True,
        "rb_score": points,
        "total_phase2_score": session['phase2_score']
    })

@app.route('/api/detective/submit', methods=['POST'])
def submit_detective():
    """Completes Tree Detective Challenge"""
    data = request.json
    correct = data.get('correct', False)

    if correct:
        session['detective_score'] = 20 # Medium weightage (20)
        session['detective_completed'] = True
    else:
        session['detective_score'] = 0
        return jsonify({"success": False, "message": "Incorrect Fix"})

    # Update Total Phase 2 Score
    session['phase2_score'] = session.get('bst_score', 0) + session.get('rb_score', 0) + session.get('detective_score', 0)
    
    save_phase2_progress()
    
    return jsonify({
        "success": True,
        "detective_score": session['detective_score'],
        "total_phase2_score": session['phase2_score']
    })

@app.route('/api/phase2/exit', methods=['POST'])
def exit_phase2():
    """User chooses to Leave Round (Finish) or Autocomplete"""
    session['bst_status'] = 'exited'
    session['phase2_completed'] = True
    
    # Final save
    save_phase2_progress()
    
    return jsonify({
        "success": True,
        "bst_status": "exited",
        "final_phase2_score": session.get('phase2_score', 0)
    })

def save_phase2_progress():
    """Helper to sync Phase 2 session data to Supabase"""
    if session.get('email') and supabase:
        if not session.get('db_synced', False):
            print("Skipping Phase 2 Save: Session not synced.")
            return

        try:
            current_total = session.get('phase1_score', 0) + session.get('phase2_score', 0) + session.get('phase3_score', 0)
            user_data = {
                "name": session.get('username'),
                "email": session.get('email'),
                "phase2_score": session.get('phase2_score', 0),
                "total_score": current_total,
                "bst_score": session.get('bst_score', 0),
                "bst_status": session.get('bst_status', 'in_progress'),
                "rb_score": session.get('rb_score', 0),
                "rb_completed": session.get('rb_completed', False),
                "detective_score": session.get('detective_score', 0),
                "detective_completed": session.get('detective_completed', False),
                "phase2_time_remaining": session.get('phase2_time_remaining', 600),
                "bst_state": session.get('bst_state', []),
                "rb_state": session.get('rb_state', []),
                "detective_state": session.get('detective_state', [])
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
    phase2_max = 100 # 40 BST + 40 RB + 20 Detective
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
