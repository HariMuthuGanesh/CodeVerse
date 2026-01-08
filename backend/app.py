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

def db_upsert_participant(email, name):
    """
    UPSERT for login only - Always sets email + name, never null name.
    Preserves existing name if participant exists, only updates if new.
    Initializes scores as NULL for new participants only.
    Returns (success: bool, error: str or None)
    """
    if not supabase:
        app.logger.error(f"[DB WRITE] Supabase client not initialized")
        return False, "Supabase not initialized"
    
    try:
        # CRITICAL: Never allow null name
        if not name or name.strip() == "":
            app.logger.error(f"[DB WRITE] Attempted to upsert with null/empty name for email={email}")
            return False, "Name cannot be null or empty"
        
        # Check if participant exists first
        check_res = supabase.table('participants').select('email, name').eq('email', email).execute()
        existing_name = None
        if check_res.data and len(check_res.data) > 0:
            existing_name = check_res.data[0].get('name')
        
        payload = {
            "email": email,
            "updated_at": get_utc_now_iso()
        }
        
        # CRITICAL: Never overwrite name with null - preserve existing or use new
        if existing_name and existing_name.strip():
            # Participant exists with name - preserve it
            payload["name"] = existing_name.strip()
            app.logger.info(f"[DB WRITE] Preserving existing name for email={email}: {existing_name}")
        else:
            # New participant or name is null - set new name
            payload["name"] = name.strip()
            app.logger.info(f"[DB WRITE] Setting new name for email={email}: {name}")
        
        # Only initialize scores as NULL if this is a new participant
        if not check_res.data or len(check_res.data) == 0:
            # New participant - initialize scores as NULL
            payload["phase1_score"] = None
            payload["phase2_score"] = None
            payload["phase3_score"] = None
            payload["total_score"] = None
            app.logger.info(f"[DB WRITE] Initializing scores as NULL for new participant")
        
        app.logger.info(f"[DB WRITE] Attempting upsert for email={email}, payload={payload}")
        
        res = supabase.table('participants').upsert(payload, on_conflict='email').execute()
        
        # CRITICAL: Verify write success
        if res.data is None or (isinstance(res.data, list) and len(res.data) == 0):
            error_msg = f"Supabase returned no data. Error: {getattr(res, 'error', 'Unknown')}"
            app.logger.error(f"[DB ERROR] {error_msg}")
            return False, error_msg
        
        app.logger.info(f"[DB SUCCESS] Upsert successful for email={email}, returned {len(res.data) if isinstance(res.data, list) else 1} row(s)")
        return True, None
        
    except Exception as e:
        error_msg = f"Supabase Upsert Failed: {str(e)}"
        app.logger.error(f"[DB ERROR] {error_msg}")
        return False, error_msg

def db_update_participant(email, data):
    """
    UPDATE for phase submissions - NEVER use upsert after login.
    Returns (success: bool, error: str or None)
    """
    if not supabase:
        app.logger.error(f"[DB WRITE] Supabase client not initialized")
        return False, "Supabase not initialized"
    
    try:
        payload = data.copy()
        payload["updated_at"] = get_utc_now_iso()
        
        app.logger.info(f"[DB WRITE] Attempting update for email={email}, payload={payload}")
        
        res = supabase.table('participants').update(payload).eq('email', email).execute()
        
        # CRITICAL: Verify write success
        if res.data is None or (isinstance(res.data, list) and len(res.data) == 0):
            error_msg = f"Supabase returned no data. Error: {getattr(res, 'error', 'Unknown')}"
            app.logger.error(f"[DB ERROR] {error_msg}")
            return False, error_msg
        
        app.logger.info(f"[DB SUCCESS] Update successful for email={email}, returned {len(res.data) if isinstance(res.data, list) else 1} row(s)")
        return True, None
        
    except Exception as e:
        error_msg = f"Supabase Update Failed: {str(e)}"
        app.logger.error(f"[DB ERROR] {error_msg}")
        return False, error_msg

# Timer logic removed - Phase 2 has unlimited time

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
    
    # 1. UPSERT SIGNUP - Always upsert email + name, never null name
    success, error = db_upsert_participant(email, username)
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
                
                # Derive phase completion from DB only (IS NOT NULL means completed)
                phase1_completed = row.get('phase1_score') is not None
                phase2_completed = row.get('phase2_completed', False) or (row.get('phase2_score') is not None)
                phase3_completed = row.get('phase3_score') is not None
                
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
    import random
    # Randomly select ONLY 5 questions from pool of 10
    selected = random.sample(QUIZ_QUESTIONS, min(5, len(QUIZ_QUESTIONS)))
    app.logger.info(f"[PHASE1] Total questions in pool: {len(QUIZ_QUESTIONS)}, Returning {len(selected)} questions (randomized)")
    
    result = [
        {"id": q["id"], "question": q["question"], "options": q["options"]} 
        for q in selected
    ]
    
    app.logger.info(f"[PHASE1] Returning question IDs: {[q['id'] for q in result]}")
    return jsonify(result)

@app.route('/api/submit-quiz', methods=['POST'])
def submit_quiz():
    email = session.get('user_email')
    if not email:
        app.logger.warning(f"[PHASE1] Submit attempt without authentication")
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    data = request.json
    answers = data.get('answers', {})
    score = 0
    
    # Each question = 5 marks, max 5 questions = 25 marks total
    for q in QUIZ_QUESTIONS:
        if answers.get(str(q['id'])) == q['answer']:
            score += 5
    
    app.logger.info(f"[PHASE1] Submission for email={email}, score={score} out of 25")
    
    session['phase1_score'] = score
    session['phase1_completed'] = True
    
    # COMPLETE PHASE 1 - Use UPDATE (never upsert after login)
    # Fetch current scores from DB to calculate total
    try:
        res = supabase.table('participants').select('phase2_score, phase3_score').eq('email', email).execute()
        phase2_score = 0
        phase3_score = 0
        if res.data and len(res.data) > 0:
            phase2_score = res.data[0].get('phase2_score') or 0
            phase3_score = res.data[0].get('phase3_score') or 0
    except Exception as e:
        app.logger.warning(f"[PHASE1] Could not fetch existing scores: {str(e)}")
        phase2_score = 0
        phase3_score = 0
    
    total = score + phase2_score + phase3_score
    success, error = db_update_participant(email, {
        "phase1_score": score,
        "total_score": total
    })
    
    if not success:
        app.logger.error(f"[PHASE1] DB write failed for email={email}: {error}")
        return jsonify({"success": False, "error": f"Database write failed: {error}"}), 500
    
    app.logger.info(f"[PHASE1] Successfully saved score={score} for email={email}")
    
    # MANDATORY: Unlock Phase 2 ONLY if DB write succeeds
    # DO NOT show score to user - score visibility only after Phase 3 completion
    return jsonify({
        "success": True,
        "phase1_completed": True,
        "phase2_completed": False,  # Phase 2 unlocks after Phase 1
        "phase3_completed": session.get('phase3_completed', False),
        "message": "Phase 1 completed. Score will be revealed after completing all phases."
    })

# --- PHASE 2 CORE ---

@app.route('/api/phase2/sync', methods=['POST'])
def sync_phase2():
    """
    Main heartbeat: Updates DB with phase2_state only.
    No timers - unlimited time.
    Persistent across refresh.
    """
    email = session.get('user_email')
    if not email:
        return jsonify({"error": "Auth required"}), 401
    
    # Fetch from DB first to restore state
    try:
        res = supabase.table('participants').select('phase2_state, phase2_completed').eq('email', email).execute()
        if res.data and len(res.data) > 0:
            row = res.data[0]
            db_state = row.get('phase2_state') or {}
            db_completed = row.get('phase2_completed', False)
            
            if db_state:
                session['phase2_state'] = db_state
            
            if db_completed:
                session['phase2_completed'] = True
                return jsonify({
                    "success": True,
                    "completed": True,
                    "state": db_state
                })
    except Exception as e:
        app.logger.warning(f"[PHASE2 SYNC] Error fetching from DB: {str(e)}")
    
    # Initialize scores if first time
    if not session.get('bst_score') is not None and not session.get('phase2_completed'):
        session['bst_score'] = 0
        session['rb_score'] = 0
        session['detective_score'] = 0
    
    # Update Session State and save to DB
    client_state = request.json.get('state') if request.json else None
    if client_state and not session.get('phase2_completed'):
        # Merge state into session
        current = session.get('phase2_state', {})
        current.update(client_state)
        session['phase2_state'] = current
        
        # Save to DB for persistence (only phase2_state, no timer fields)
        db_update_participant(email, {
            "phase2_state": current
        })

    return jsonify({
        "success": True,
        "completed": session.get('phase2_completed', False),
        "state": session.get('phase2_state', {})
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
    # expect [{'id': 'rb-node-1', 'color': 'red' or 'black', 'value': 40}, ...]
    # Build tree structure - now uses drag-and-drop with data-color attribute
    
    # Fixed Values in UI: 1=40, 2=20, 3=60, 4=10, 5=30, 6=50, 7=70
    id_map = {1: 40, 2: 20, 3: 60, 4: 10, 5: 30, 6: 50, 7: 70}
    
    colors = {} # id -> 'red'/'black'
    for n in node_list:
        try:
            # Match rb-node-1 -> 1
            if 'rb-node-' in n['id']:
                nid = int(n['id'].replace('rb-node-', ''))
                # Frontend now sends 'color' as 'red' or 'black' from data-color attribute
                color_str = str(n.get('color', 'black')).lower().strip()
                if color_str == 'red':
                    colors[nid] = 'red'
                else:
                    colors[nid] = 'black'  # Default to black
        except Exception as e:
            app.logger.warning(f"[RB VALIDATION] Error parsing node {n}: {str(e)}")
            pass

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
    # No timer check - unlimited time
    if session.get('phase2_completed'):
        return jsonify({"success": False, "message": "Phase 2 already completed"})
    
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

def validate_detective_logic(slots):
    """
    Tree Detective: Require detecting MULTIPLE DEEP (global) violations.
    The broken tree has MULTIPLE violations:
    - Deep BST violations that are valid locally but invalid globally
    - Multiple nodes in wrong subtrees causing cascade violations
    """
    try:
        nodes = {int(k): int(v) for k, v in slots.items() if v}
    except:
        return False, "Invalid Data", 0

    if len(nodes) < 7:
        return False, "Incomplete Tree. All 7 nodes must be placed.", 0

    # Check if tree is valid BST - if valid, no violations
    def is_bst(idx, min_val, max_val):
        if idx not in nodes:
            return True
        val = nodes[idx]
        if not (min_val < val < max_val):
            return False
        return is_bst(2*idx, min_val, val) and is_bst(2*idx+1, val, max_val)
    
    # First check: Is it a valid BST? If yes, no violations detected
    if is_bst(1, float('-inf'), float('inf')):
        return False, "No violations detected. Tree is valid BST.", 0
    
    # Count DEEP violations by checking global BST property
    # Must find violations that are valid locally but invalid globally
    violations_found = 0
    violations_expected = 2  # Must find at least 2 violations
    
    root_val = nodes.get(1)
    if not root_val:
        return False, "Root node missing", 0
    
    # Check each node against its ancestor constraints
    def check_violation(idx, min_val, max_val, depth=0):
        if idx not in nodes:
            return 0
        val = nodes[idx]
        violations = 0
        
        # Check if node violates global constraint
        if not (min_val < val < max_val):
            violations += 1
        
        # Recursively check children
        violations += check_violation(2*idx, min_val, val, depth+1)
        violations += check_violation(2*idx+1, val, max_val, depth+1)
        return violations
    
    violations_found = check_violation(1, float('-inf'), float('inf'))
    
    # Must detect at least 2 violations
    if violations_found >= violations_expected:
        return True, f"Detected {violations_found} deep violation(s). Tree fixed!", violations_found
    else:
        return False, f"Only detected {violations_found} violation(s). Need to find at least {violations_expected} deep violations.", violations_found

@app.route('/api/detective/submit', methods=['POST'])
def submit_detective():
    # No timer check - unlimited time
    if session.get('phase2_completed'):
        return jsonify({"success": False, "message": "Phase 2 already completed"})
    
    data = request.json
    slots = data.get('slots', {})
    
    valid, msg, violations = validate_detective_logic(slots)
    
    # Score based on violations detected (20 points if all violations found)
    points = 20 if valid else 0
    session['detective_score'] = points
    
    state = session.get('phase2_state', {})
    state['detective_score'] = points
    session['phase2_state'] = state

    app.logger.info(f"[PHASE2 DETECTIVE] Violations detected: {violations}, Valid: {valid}, Score: {points}")
    
    return jsonify({"success": True, "valid": valid, "message": msg, "score": points, "violations": violations})

@app.route('/api/rb/complete', methods=['POST'])
def complete_rb():
    # No timer check - unlimited time
    if session.get('phase2_completed'):
        return jsonify({"success": False, "message": "Phase 2 already completed"})
    
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
    
    # COMPLETE PHASE 2 - Calculate score from state
    p2_score = session.get('bst_score', 0) + session.get('rb_score', 0) + session.get('detective_score', 0)
    session['phase2_score'] = p2_score
    session['phase2_completed'] = True
    
    app.logger.info(f"[PHASE2] Exit for email={email}, score={p2_score}")
    
    # Fetch current scores from DB to calculate total
    try:
        res = supabase.table('participants').select('phase1_score, phase3_score').eq('email', email).execute()
        phase1_score = 0
        phase3_score = 0
        if res.data and len(res.data) > 0:
            phase1_score = res.data[0].get('phase1_score') or 0
            phase3_score = res.data[0].get('phase3_score') or 0
    except Exception as e:
        app.logger.warning(f"[PHASE2] Could not fetch existing scores: {str(e)}")
        phase1_score = 0
        phase3_score = 0
    
    total = phase1_score + p2_score + phase3_score
    
    # Use UPDATE - set phase2_score and phase2_completed = true
    # No timer fields - removed phase2_time_left
    success, error = db_update_participant(email, {
        "phase2_score": p2_score,
        "phase2_completed": True,
        "total_score": total
    })
    
    if not success:
        app.logger.error(f"[PHASE2] DB write failed for email={email}: {error}")
        return jsonify({"success": False, "error": f"Database write failed: {error}"}), 500
    
    app.logger.info(f"[PHASE2] Successfully saved score={p2_score}, phase2_completed=true for email={email}")
    
    # MANDATORY: Unlock Phase 3 ONLY after DB success
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
    
    # Fetch current scores from DB to calculate total
    try:
        res = supabase.table('participants').select('phase1_score, phase2_score').eq('email', email).execute()
        phase1_score = 0
        phase2_score = 0
        if res.data and len(res.data) > 0:
            phase1_score = res.data[0].get('phase1_score') or 0
            phase2_score = res.data[0].get('phase2_score') or 0
    except Exception as e:
        app.logger.warning(f"[PHASE3] Could not fetch existing scores: {str(e)}")
        phase1_score = 0
        phase2_score = 0
    
    total = phase1_score + phase2_score + points
    
    # COMPLETE PHASE 3 - Use UPDATE (never upsert after login)
    success, error = db_update_participant(email, {
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
    """
    Get phase status from Supabase (source of truth).
    Derive phase completion from DB scores.
    """
    email = session.get('user_email')
    if not email:
        return jsonify({
            "phase1_completed": False,
            "phase2_completed": False,
            "phase3_completed": False,
            "phase1_score": 0,
            "phase2_score": 0,
            "phase3_score": 0
        })
    
    # Fetch from Supabase - DB is source of truth
    phase1_completed = False
    phase2_completed = False
    phase3_completed = False
    phase1_score = 0
    phase2_score = 0
    phase3_score = 0
    
    try:
        if supabase:
            res = supabase.table('participants').select('phase1_score, phase2_score, phase3_score, phase2_completed').eq('email', email).execute()
            if res.data and len(res.data) > 0:
                row = res.data[0]
                phase1_score = row.get('phase1_score') or 0
                phase2_score = row.get('phase2_score') or 0
                phase3_score = row.get('phase3_score') or 0
                
                # Derive phase completion from DB only (IS NOT NULL means completed)
                phase1_completed = row.get('phase1_score') is not None
                phase2_completed = row.get('phase2_completed', False) or (row.get('phase2_score') is not None)
                phase3_completed = row.get('phase3_score') is not None
                
                # Update session to keep in sync
                session['phase1_completed'] = phase1_completed
                session['phase2_completed'] = phase2_completed
                session['phase3_completed'] = phase3_completed
                session['phase1_score'] = phase1_score
                session['phase2_score'] = phase2_score
                session['phase3_score'] = phase3_score
                
                app.logger.info(f"[STATUS] Fetched from DB - Phase1: {phase1_completed}, Phase2: {phase2_completed} (DB flag: {row.get('phase2_completed')}), Phase3: {phase3_completed}")
    except Exception as e:
        app.logger.error(f"[STATUS] Error fetching from DB: {str(e)}")
        # Fallback to session
        phase1_completed = session.get('phase1_completed', False)
        phase2_completed = session.get('phase2_completed', False)
        phase3_completed = session.get('phase3_completed', False)
        phase1_score = session.get('phase1_score', 0)
        phase2_score = session.get('phase2_score', 0)
        phase3_score = session.get('phase3_score', 0)
        
    return jsonify({
        "phase1_completed": phase1_completed,
        "phase2_completed": phase2_completed,
        "phase3_completed": phase3_completed,
        "phase1_score": phase1_score,
        "phase2_score": phase2_score,
        "phase3_score": phase3_score
    })
    
@app.route('/api/get-total-score', methods=['GET'])
def get_total_score():
    """
    Get total score from Supabase.
    CRITICAL: Only show scores if phase3_score IS NOT NULL.
    """
    email = session.get('user_email')
    if not email:
        return jsonify({
            "phase1_score": 0,
            "phase2_score": 0,
            "phase3_score": None,
            "total_score": 0,
            "scores_visible": False
        })
    
    # Fetch from Supabase - DB is source of truth
    phase1_score = 0
    phase2_score = 0
    phase3_score = None
    scores_visible = False
    
    try:
        if supabase:
            res = supabase.table('participants').select('phase1_score, phase2_score, phase3_score, total_score').eq('email', email).execute()
            if res.data and len(res.data) > 0:
                row = res.data[0]
                phase1_score = row.get('phase1_score') or 0
                phase2_score = row.get('phase2_score') or 0
                phase3_score = row.get('phase3_score')
                total_score = row.get('total_score') or 0
                
                # CRITICAL RULE: Scores visible ONLY if phase3_score IS NOT NULL
                scores_visible = phase3_score is not None
                
                # Update session
                session['phase1_score'] = phase1_score
                session['phase2_score'] = phase2_score
                session['phase3_score'] = phase3_score
                session['phase3_completed'] = (phase3_score is not None)
                
                app.logger.info(f"[SCORE] Fetched scores for {email} - Phase3: {phase3_score}, Visible: {scores_visible}")
    except Exception as e:
        app.logger.error(f"[SCORE] Error fetching scores: {str(e)}")
        phase1_score = session.get('phase1_score', 0)
        phase2_score = session.get('phase2_score', 0)
        phase3_score = session.get('phase3_score')
        scores_visible = (phase3_score is not None)
    
    total = phase1_score + phase2_score + (phase3_score or 0)
    
    return jsonify({
        "phase1_score": phase1_score,
        "phase2_score": phase2_score,
        "phase3_score": phase3_score,
        "total_score": total,
        "scores_visible": scores_visible
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
