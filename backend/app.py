from flask import Flask, jsonify, request, session, render_template, send_from_directory, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
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

# Database Configuration
# Handle Render's postgres:// vs postgresql:// compatibility
database_url = os.environ.get('DATABASE_URL', 'sqlite:///participants.db')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model
class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    rollno = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phase = db.Column(db.String(50))
    score = db.Column(db.Integer)
    max_score = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'rollno': self.rollno,
            'username': self.username,
            'email': self.email,
            'phase': self.phase,
            'score': self.score,
            'max_score': self.max_score,
            'created_at': self.created_at.isoformat()
        }

# Initialize DB
with app.app_context():
    db.create_all()

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
    
    # Retrieve past scores from DB to restore session state
    try:
        # Get all scores for this user
        scores = Score.query.filter_by(rollno=rollno).all()
        
        # Reset session scores
        session['phase1_score'] = 0
        session['phase2_score'] = 0
        session['phase3_score'] = 0
        
        # Populate based on history
        for s in scores:
            if "Phase 1" in s.phase:
                session['phase1_score'] = max(session.get('phase1_score', 0), s.score)
                session['phase1_completed'] = True
            elif "Phase 2" in s.phase:
                session['phase2_score'] = max(session.get('phase2_score', 0), s.score)
                session['phase2_completed'] = True
            elif "Phase 3" in s.phase:
                session['phase3_score'] = max(session.get('phase3_score', 0), s.score)
                session['phase3_completed'] = True
                
    except Exception as e:
        print(f"Login DB Error: {e}")
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

    # Store in DB
    if session.get('rollno'):
        try:
            new_score = Score(
                rollno=session['rollno'],
                username=session.get('username'),
                email=session.get('email'),
                phase="Phase 1 - Quiz",
                score=points,
                max_score=50
            )
            db.session.add(new_score)
            db.session.commit()
        except Exception as e:
            print(f"DB Error submit-quiz: {e}")

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
    
    if session.get('rollno'):
        try:
            new_score = Score(
                rollno=session['rollno'],
                username=session.get('username'),
                email=session.get('email'),
                phase="Phase 2 - DSA",
                score=points,
                max_score=50
            )
            db.session.add(new_score)
            db.session.commit()
        except Exception as e:
            print(f"DB Error complete-phase-2: {e}")

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
    
    if session.get('rollno'):
        try:
            new_score = Score(
                rollno=session['rollno'],
                username=session.get('username'),
                email=session.get('email'),
                phase="Phase 3 - Final",
                score=points,
                max_score=100
            )
            db.session.add(new_score)
            db.session.commit()
        except Exception as e:
            print(f"DB Error complete-phase-3: {e}")
    
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
        # Aggregate scores by user
        scores = Score.query.all()
        user_map = {}
        
        for s in scores:
            if s.rollno not in user_map:
                user_map[s.rollno] = {
                    'rollno': s.rollno,
                    'username': s.username,
                    'email': s.email,
                    'phase1_score': 0,
                    'phase2_score': 0,
                    'phase3_score': 0,
                    'last_activity': s.created_at
                }
            
            u = user_map[s.rollno]
            # Update latest activity
            if s.created_at > u['last_activity']:
                u['last_activity'] = s.created_at
            
            # Update max score per phase
            if "Phase 1" in s.phase:
                u['phase1_score'] = max(u['phase1_score'], s.score)
            elif "Phase 2" in s.phase:
                u['phase2_score'] = max(u['phase2_score'], s.score)
            elif "Phase 3" in s.phase:
                u['phase3_score'] = max(u['phase3_score'], s.score)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Roll No', 'Username', 'Email', 'Phase 1 Score', 'Phase 2 Score', 'Phase 3 Score', 'Total Score', 'Last Activity'])

        for rollno, u in user_map.items():
            total = u['phase1_score'] + u['phase2_score'] + u['phase3_score']
            writer.writerow([
                u['rollno'],
                u['username'],
                u['email'],
                u['phase1_score'],
                u['phase2_score'],
                u['phase3_score'],
                total,
                u['last_activity'].isoformat()
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
        scores = Score.query.order_by(Score.created_at.desc()).all()
        return jsonify([s.to_dict() for s in scores])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_progress():
    session.clear()
    return jsonify({"success": True, "message": "Timeline Reset."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
