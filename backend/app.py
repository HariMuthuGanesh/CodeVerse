from flask import Flask, jsonify, request, session, render_template, send_from_directory, Response, redirect
from flask_cors import CORS
from supabase import create_client, Client
from quiz_data import QUIZ_QUESTIONS
import os
import io
import csv
import json
from datetime import datetime, timedelta

# Initialize Flask App
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
TEMPLATE_DIR = os.path.join(PARENT_DIR, 'frontend')
STATIC_DIR = os.path.join(PARENT_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = os.environ.get('SECRET_KEY', 'AVENGERS_ASSEMBLE_SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2) # Keep session alive
CORS(app)

# Supabase Configuration - MANDATORY: Use service_role key only
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

supabase: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        app.logger.info(f"[SUPABASE] Initialized successfully with URL: {SUPABASE_URL}")
    except Exception as e:
        app.logger.error(f"[SUPABASE INIT ERROR] {str(e)}")
else:
    app.logger.warning(f"[SUPABASE] Missing configuration - URL: {bool(SUPABASE_URL)}, KEY: {bool(SUPABASE_SERVICE_KEY)}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/phases.html')
def phases():
    if not session.get('user_email'):
        return redirect('/login.html')
    return render_template('phases.html')

@app.route('/quiz.html')
def quiz_page():
    if not session.get('user_email'): return redirect('/login.html')
    return render_template('quiz.html')

@app.route('/dsa.html')
def dsa_page():
    if not session.get('user_email'): return redirect('/login.html')
    return render_template('dsa.html')

@app.route('/final.html')
def final_page():
    if not session.get('user_email'): return redirect('/login.html')
    return render_template('final.html')

@app.route('/score.html')
def score_page():
    if not session.get('user_email'): return redirect('/login.html')
    return render_template('score.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)

# --- HELPER FUNCTIONS ---

def get_utc_now_iso():
    return datetime.utcnow().isoformat()

def db_upsert_participant(email, data):
    """
    Safe idempotent upsert to Supabase with verification.
    Returns (success: bool, error: str or None)
    """
    if not supabase:
        app.logger.error(f"[DB WRITE] Supabase client not initialized")
        return False, "Supabase not initialized"
    
    try:
        payload = {"email": email}
        payload.update(data)
        payload["updated_at"] = get_utc_now_iso()
        
        app.logger.info(f"[DB WRITE] Attempting upsert for email={email}, data={data}")
        
        res = supabase.table('participants').upsert(payload, on_conflict='email').execute()
        
        # CRITICAL: Verify write success
        if res.data is None or (isinstance(res.data, list) and len(res.data) == 0):
            error_msg = f"Supabase returned no data. Error: {getattr(res, 'error', 'Unknown')}"
            app.logger.error(f"[DB ERROR] {error_msg}")
            return False, error_msg
        
        app.logger.info(f"[DB SUCCESS] Upsert successful for email={email}, returned {len(res.data) if isinstance(res.data, list) else 1} row(s)")
        return True, None
        
    except Exception as e:
        error_msg = f"Supabase Update Failed: {str(e)}"
        app.logger.error(f"[DB ERROR] {error_msg}")
        return False, error_msg

def check_phase2_timer():
    """Returns (is_active, seconds_remaining)."""
    if session.get('phase2_completed'):
        return False, 0
    
    start_str = session.get('phase2_started_at')
    if not start_str:
        return True, 900 # Not started yet formal? Treated as fresh.
        
    try:
        if start_str.endswith('Z'): start_str = start_str[:-1]
        start_time = datetime.fromisoformat(start_str)
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        remaining = max(0, 900 - int(elapsed))
        
        if remaining == 0:
            session['phase2_completed'] = True
            return False, 0
        return True, remaining
    except:
        return True, 900

# --- AUTH & PHASE 1 ---

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    
    app.logger.info(f"[LOGIN] Attempt for email={email}, username={username}")
    
    if not email or not username:
        app.logger.warning(f"[LOGIN] Missing fields - email: {bool(email)}, username: {bool(username)}")
        return jsonify({"error": "Missing fields"}), 400

    session.permanent = True
    session['user_email'] = email
    session['user_name'] = username
    
    # Defaults
    session['phase1_completed'] = False
    session['phase2_completed'] = False
    session['phase3_completed'] = False
    
    # 1. UPSERT SIGNUP - Verify write
    success, error = db_upsert_participant(email, {"name": username})
    if not success:
        app.logger.error(f"[LOGIN] Failed to upsert participant: {error}")
        return jsonify({"success": False, "error": f"Database write failed: {error}"}), 500
    
    # 2. FETCH PARTICIPANT ROW - Derive phase completion from DB only
    phase1_completed = False
    phase2_completed = False
    phase3_completed = False
    
    try:
        if supabase:
            res = supabase.table('participants').select('*').eq('email', email).execute()
            if res.data and len(res.data) > 0:
                row = res.data[0]
                session['phase1_score'] = row.get('phase1_score') or 0
                session['phase2_score'] = row.get('phase2_score') or 0
                session['phase3_score'] = row.get('phase3_score') or 0
                
                # Derive phase completion from DB only (score is not None means completed)
                phase1_completed = row.get('phase1_score') is not None and row.get('phase1_score', 0) > 0
                phase2_completed = row.get('phase2_score') is not None and row.get('phase2_score', 0) > 0
                phase3_completed = row.get('phase3_score') is not None and row.get('phase3_score', 0) > 0
                
                session['phase1_completed'] = phase1_completed
                session['phase2_completed'] = phase2_completed
                session['phase3_completed'] = phase3_completed
                
                app.logger.info(f"[LOGIN] Loaded participant - Phase1: {phase1_completed}, Phase2: {phase2_completed}, Phase3: {phase3_completed}")
            else:
                app.logger.warning(f"[LOGIN] No participant row found after upsert for email={email}")
    except Exception as e:
        app.logger.error(f"[LOGIN] Error fetching participant: {str(e)}")
        return jsonify({"success": False, "error": f"Failed to fetch participant data: {str(e)}"}), 500

    app.logger.info(f"[LOGIN] Success for email={email}")
    
    # MANDATORY: Return phase completion flags
    return jsonify({
        "success": True,
        "phase1_completed": phase1_completed,
        "phase2_completed": phase2_completed,
        "phase3_completed": phase3_completed
    })

@app.route('/api/quiz', methods=['GET'])
def get_quiz():
    return jsonify([
        {"id": q["id"], "question": q["question"], "options": q["options"]} 
        for q in QUIZ_QUESTIONS
    ])

@app.route('/api/submit-quiz', methods=['POST'])
def submit_quiz():
    email = session.get('user_email')
    if not email:
        app.logger.warning(f"[PHASE1] Submit attempt without authentication")
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    data = request.json
    answers = data.get('answers', {})
    score = 0
    
    for q in QUIZ_QUESTIONS:
        if answers.get(str(q['id'])) == q['answer']:
            score += 5
    
    app.logger.info(f"[PHASE1] Submission for email={email}, score={score}")
    
    session['phase1_score'] = score
    session['phase1_completed'] = True
    
    # COMPLETE PHASE 1 - DB UPDATE with verification
    total = score + session.get('phase2_score', 0) + session.get('phase3_score', 0)
    success, error = db_upsert_participant(email, {
        "phase1_score": score,
        "total_score": total
    })
    
    if not success:
        app.logger.error(f"[PHASE1] DB write failed for email={email}: {error}")
        return jsonify({"success": False, "error": f"Database write failed: {error}"}), 500
    
    app.logger.info(f"[PHASE1] Successfully saved score={score} for email={email}")
    
    # MANDATORY: Return completion flags
    total_questions = len(QUIZ_QUESTIONS)
    return jsonify({
        "success": True,
        "score": score // 5,  # Number of correct answers
        "total": total_questions,
        "phase1_completed": True,
        "phase2_completed": False,  # Phase 2 unlocks after Phase 1
        "phase3_completed": session.get('phase3_completed', False)
    })

# --- PHASE 2 CORE ---

@app.route('/api/phase2/sync', methods=['POST'])
def sync_phase2():
    """Main heartbeat: Updates session state, checks timer."""
    if not session.get('user_email'): return jsonify({"error": "Auth required"}), 401
    
    # Auto Start if first time
    if not session.get('phase2_started_at') and not session.get('phase2_completed'):
        session['phase2_started_at'] = get_utc_now_iso()
        session['bst_score'] = 0
        session['rb_score'] = 0
        session['detective_score'] = 0
    
    # Check Timer
    active, remaining = check_phase2_timer()
    
    # Update Session State (Transient)
    client_state = request.json.get('state')
    if active and client_state:
        # Merge state into session
        current = session.get('phase2_state', {})
        current.update(client_state)
        session['phase2_state'] = current

    return jsonify({
        "success": True,
        "started_at": session.get('phase2_started_at'),
        "time_left": remaining,
        "completed": session.get('phase2_completed', False),
        "state": session.get('phase2_state')
    })

# --- PHASE 2 VALIDATION HANDLERS (STRICT SERVER-SIDE) ---

def validate_bst_logic(slots):
    # expect { "1": val, "2": val... }
    # indices 1-7
    try:
        nodes = {int(k): int(v) for k,v in slots.items() if v}
    except:
        return False, "Invalid Data"

    if len(nodes) < 7: return False, "Incomplete Tree"

    def is_bst(idx, min_val, max_val):
        if idx not in nodes: return True
        val = nodes[idx]
        if not (min_val < val < max_val): return False
        return is_bst(2*idx, min_val, val) and is_bst(2*idx+1, val, max_val)

    if is_bst(1, float('-inf'), float('inf')):
        return True, "Valid"
    return False, "BST Property Violated"

def validate_rb_logic(node_list):
    # expect [{'id': 'rb-node-1', 'color': 'red', 'value': 40}, ...]
    # Build tree structure
    
    # Fixed Values in UI: 1=40, 2=20, 3=60, 4=10, 5=30, 6=50, 7=70
    id_map = {1: 40, 2: 20, 3: 60, 4: 10, 5: 30, 6: 50, 7: 70}
    
    colors = {} # id -> 'red'/'black'
    for n in node_list:
        try:
            # Match rb-node-1 -> 1
            if 'rb-node-' in n['id']:
                nid = int(n['id'].replace('rb-node-', ''))
                # frontend sends generic style string often
                c_str = n.get('color', '').lower()
                # If background is black or empty or rgb(0,0,0) -> Black.
                # If red or #AA0000 -> Red.
                is_red = 'red' in c_str or 'aa0000' in c_str
                colors[nid] = 'red' if is_red else 'black'
        except: pass

    # 1. Root Black
    if colors.get(1, 'black') != 'black': return False, "Root must be BLACK"

    # 2. Red-Red Check & Black Height
    def check_rb(nid):
        if nid not in id_map: return True, 1 # Valid, height 1
        
        c = colors.get(nid, 'black')
        
        l_id, r_id = 2*nid, 2*nid+1
        
        l_valid, l_bh = check_rb(l_id)
        r_valid, r_bh = check_rb(r_id)
        
        if not l_valid or not r_valid: return False, 0
        
        # Red-Red
        if c == 'red':
            if colors.get(l_id, 'black') == 'red': return False, 0
            if colors.get(r_id, 'black') == 'red': return False, 0
        
        # Black Height
        if l_bh != r_bh: return False, 0
        
        return True, l_bh + (1 if c == 'black' else 0)

    valid, _ = check_rb(1)
    if valid: return True, "Valid"
    return False, "Violation Detected"

@app.route('/api/bst/submit', methods=['POST'])
def submit_bst():
    active, _ = check_phase2_timer()
    if not active: return jsonify({"success": False, "message": "Locked"})
    
    data = request.json
    slots = data.get('slots', {}) # Map of slot_index -> value
    
    valid, msg = validate_bst_logic(slots)
    
    points = 40 if valid else 0
    session['bst_score'] = points
    
    # Store points in state for persistence
    state = session.get('phase2_state', {})
    state['bst_score'] = points
    session['phase2_state'] = state
    
    return jsonify({"success": True, "valid": valid, "message": msg, "score": points})

@app.route('/api/detective/submit', methods=['POST'])
def submit_detective():
    active, _ = check_phase2_timer()
    if not active: return jsonify({"success": False, "message": "Locked"})
    
    data = request.json
    slots = data.get('slots', {})
    
    valid, msg = validate_bst_logic(slots)
    
    points = 20 if valid else 0
    session['detective_score'] = points
    
    state = session.get('phase2_state', {})
    state['detective_score'] = points
    session['phase2_state'] = state

    return jsonify({"success": True, "valid": valid, "message": msg, "score": points})

@app.route('/api/rb/complete', methods=['POST'])
def complete_rb():
    active, _ = check_phase2_timer()
    if not active: return jsonify({"success": False, "message": "Locked"})
    
    data = request.json
    nodes = data.get('nodes', [])
    
    valid, msg = validate_rb_logic(nodes)
    
    points = 40 if valid else 0
    session['rb_score'] = points
    
    state = session.get('phase2_state', {})
    state['rb_score'] = points
    session['phase2_state'] = state

    return jsonify({"success": True, "valid": valid, "message": msg, "score": points})

@app.route('/api/phase2/exit', methods=['POST'])
def exit_phase2():
    email = session.get('user_email')
    if not email:
        app.logger.warning(f"[PHASE2] Exit attempt without authentication")
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    # COMPLETE PHASE 2
    session['phase2_completed'] = True
    
    p2_score = session.get('bst_score', 0) + session.get('rb_score', 0) + session.get('detective_score', 0)
    session['phase2_score'] = p2_score
    
    app.logger.info(f"[PHASE2] Exit for email={email}, score={p2_score}")
    
    total = session.get('phase1_score', 0) + p2_score + session.get('phase3_score', 0)
    success, error = db_upsert_participant(email, {
        "phase2_score": p2_score,
        "total_score": total
    })
    
    if not success:
        app.logger.error(f"[PHASE2] DB write failed for email={email}: {error}")
        return jsonify({"success": False, "error": f"Database write failed: {error}"}), 500
    
    app.logger.info(f"[PHASE2] Successfully saved score={p2_score} for email={email}")
    
    # MANDATORY: Return completion flags
    return jsonify({
        "success": True,
        "phase2_completed": True,
        "phase3_completed": False,  # Phase 3 unlocks after Phase 2
        "phase1_completed": session.get('phase1_completed', False)
    })

@app.route('/api/complete-phase-2', methods=['POST'])
def complete_phase_2_alt():
    return exit_phase2()

# --- PHASE 3 ---

@app.route('/api/complete-phase-3', methods=['POST'])
def complete_phase_3():
    email = session.get('user_email')
    if not email:
        app.logger.warning(f"[PHASE3] Submit attempt without authentication")
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    data = request.json or {}
    points = data.get('points', 0)
    
    app.logger.info(f"[PHASE3] Submission for email={email}, points={points}")
    
    session['phase3_score'] = points
    session['phase3_completed'] = True
    
    # COMPLETE PHASE 3 - DB UPDATE with verification
    total = session.get('phase1_score', 0) + session.get('phase2_score', 0) + points
    success, error = db_upsert_participant(email, {
        "phase3_score": points,
        "total_score": total
    })
    
    if not success:
        app.logger.error(f"[PHASE3] DB write failed for email={email}: {error}")
        return jsonify({"success": False, "error": f"Database write failed: {error}"}), 500
    
    app.logger.info(f"[PHASE3] Successfully saved points={points} for email={email}")
    
    # MANDATORY: Return completion flags
    return jsonify({
        "success": True,
        "phase3_completed": True,
        "phase1_completed": session.get('phase1_completed', False),
        "phase2_completed": session.get('phase2_completed', False)
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    p2_completed = session.get('phase2_completed', False)
    
    if not p2_completed and session.get('phase2_started_at'):
        active, _ = check_phase2_timer()
        if not active: p2_completed = True
        
    return jsonify({
        "phase1_completed": session.get('phase1_completed', False),
        "phase2_completed": p2_completed,
        "phase3_completed": session.get('phase3_completed', False),
        "phase1_score": session.get('phase1_score', 0),
        "phase2_score": session.get('phase2_score', 0),
        "phase3_score": session.get('phase3_score', 0)
    })
    
@app.route('/api/get-total-score', methods=['GET'])
def get_total_score():
    # Helper to return formatted scores
    p1 = session.get('phase1_score', 0)
    p2 = session.get('phase2_score', 0)
    p3 = session.get('phase3_score', 0)
    total = p1 + p2 + p3
    return jsonify({
        "phase1_score": p1,
        "phase2_score": p2,
        "phase3_score": p3,
        "total_score": total
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
