from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import psycopg2
import psycopg2.extras
import random

quiz_bp = Blueprint('quiz', __name__)

DATABASE_URL = 'postgresql://neondb_owner:npg_zsbQNiH92vkl@ep-floral-hill-a1sq9ye6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&connect_timeout=30'

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ==========================================
#  DATA CONFIGURATION
# ==========================================
subject_videos = {
    "Mathematics": {"topic_title": "Algebra", "video_id": "dN3sPEtTZPE", "start_id": 101},
    "Science": {"topic_title": "States of Matter", "video_id": "wclY8F-UoTE", "start_id": 201},
    "History": {"topic_title": "Malacca Sultanate", "video_id": "L0EiJZRxQUY", "start_id": 301},
    "English": {"topic_title": "Past Tense", "video_id": "K8kqQDyZ1ik", "start_id": 401}
}

# FULL QUESTION LIST
questions_db = [
    # MATH
    {"id": 101, "subject": "Mathematics", "difficulty": "Easy", "question_text": "In 5x, what is '5'?", "option_a": "Variable", "option_b": "Coefficient", "option_c": "Constant", "option_d": "Power", "correct_answer": "Coefficient", "explanation": "It is the coefficient."},
    {"id": 102, "subject": "Mathematics", "difficulty": "Easy", "question_text": "Simplify 2x + 3x", "option_a": "5x", "option_b": "6x", "option_c": "5x^2", "option_d": "x", "correct_answer": "5x", "explanation": "Add coefficients: 2+3=5."},
    
    # SCIENCE
    # SCIENCE (States of Matter)
    {
        "id": 201, "subject": "Science", "difficulty": "Easy",
        "question_text": "Which state of matter has a definite shape and volume?",
        "option_a": "Liquid", "option_b": "Solid", "option_c": "Gas", "option_d": "Plasma",
        "correct_answer": "Solid",
        "explanation": "Solids keep their shape and volume because their particles are packed tightly together and vibrate in place."
    },
    {
        "id": 202, "subject": "Science", "difficulty": "Medium",
        "question_text": "How do particles in a GAS behave?",
        "option_a": "They are packed tightly in a pattern", 
        "option_b": "They slide past each other slowly", 
        "option_c": "They move freely at high speeds", 
        "option_d": "They do not move at all",
        "correct_answer": "They move freely at high speeds",
        "explanation": "Gas particles have a lot of energy and are spread far apart, moving quickly in all directions."
    },
    {
        "id": 203, "subject": "Science", "difficulty": "Medium",
        "question_text": "What happens when a liquid turns into a solid?",
        "option_a": "Melting", "option_b": "Evaporation", "option_c": "Condensation", "option_d": "Freezing",
        "correct_answer": "Freezing",
        "explanation": "Freezing occurs when a liquid loses heat energy, causing its particles to slow down and lock into a solid structure."
    },
    {
        "id": 204, "subject": "Science", "difficulty": "Hard",
        "question_text": "Why can liquids flow and take the shape of their container?",
        "option_a": "The particles are far apart",
        "option_b": "The particles can slide past one another",
        "option_c": "The particles are locked in place",
        "option_d": "Liquids have no mass",
        "correct_answer": "The particles can slide past one another",
        "explanation": "In a liquid, particles are close together but not held in a fixed position, allowing them to flow."
    },

    # HISTORY
    {"id": 301, "subject": "History", "difficulty": "Easy", "question_text": "Founder of Melaka?", "option_a": "Ali", "option_b": "Parameswara", "option_c": "Abu", "option_d": "Lee", "correct_answer": "Parameswara", "explanation": "Parameswara founded it."},
    
    # ENGLISH
    {"id": 401, "subject": "English", "difficulty": "Easy", "question_text": "Past tense of go?", "option_a": "Went", "option_b": "Goes", "option_c": "Gone", "option_d": "Going", "correct_answer": "Went", "explanation": "Go -> Went."}
]

# ==========================================
#  ROUTES
# ==========================================

@quiz_bp.route('/start_subject/<subject_name>')
def start_subject(subject_name):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    # 1. SAVE THE CURRENT SUBJECT TO SESSION
    session['current_subject'] = subject_name
    
    data = subject_videos.get(subject_name)
    if not data: return redirect(url_for('main.dashboard'))
    
    # Pass data to video template
    return render_template('video.html', q={
        "subject": subject_name, 
        "topic_title": data['topic_title'], 
        "video_id": data['video_id'], 
        "id": data['start_id']
    })

@quiz_bp.route('/question/<int:id>')
def quiz(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))

    question = next((q for q in questions_db if q['id'] == id), None)
    if not question: return "Question not found", 404
    
    # Ensure subject is updated in session just in case they jumped here directly
    session['current_subject'] = question['subject']
    
    attempts = session.get('attempts', 0)
    return render_template('quiz.html', q=question, attempts=attempts)

@quiz_bp.route('/submit', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session: return redirect(url_for('auth.login'))

    q_id = int(request.form.get('question_id'))
    option = request.form.get('option')
    
    question = next((q for q in questions_db if q['id'] == q_id), None)
    if not question: return redirect(url_for('main.dashboard'))
    
    is_correct = (option == question['correct_answer'])
    xp_gain = 10 if is_correct else 0
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Save History
        cur.execute("INSERT INTO history (user_id, subject, score) VALUES (%s, %s, %s)", 
                   (session['user_id'], question['subject'], xp_gain))
        
        if is_correct:
            # Update User Stats
            cur.execute("UPDATE users SET xp = xp + %s, streak = streak + 1 WHERE id = %s", (xp_gain, session['user_id']))
            # Update Progress
            cur.execute("SELECT id FROM progress WHERE user_id = %s AND subject = %s", (session['user_id'], question['subject']))
            if cur.fetchone():
                cur.execute("UPDATE progress SET total_answered = total_answered + 1 WHERE user_id = %s AND subject = %s", (session['user_id'], question['subject']))
            else:
                cur.execute("INSERT INTO progress (user_id, subject, mastery_level, total_answered) VALUES (%s, %s, 1, 1)", (session['user_id'], question['subject']))
        
        conn.commit()
    except Exception as e:
        print(f"Submit Error: {e}")
    finally:
        if conn: conn.close()
    
    return render_template('result.html', is_correct=is_correct, explanation=question['explanation'])

@quiz_bp.route('/next_question')
def next_question():
    """
    Finds a random question from the CURRENT subject only.
    """
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    # 1. Get the current subject from session
    current_subject = session.get('current_subject')
    
    # If no subject is set (e.g. session expired), go back to dashboard
    if not current_subject:
        return redirect(url_for('main.dashboard'))

    # 2. Filter questions list to ONLY show this subject
    subject_questions = [q for q in questions_db if q['subject'] == current_subject]
    
    # If no questions found for this subject
    if not subject_questions:
        return redirect(url_for('main.dashboard'))

    # 3. Pick a random question from the filtered list
    next_q = random.choice(subject_questions)
    
    return redirect(url_for('quiz.quiz', id=next_q['id']))

@quiz_bp.route('/history')
def history():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT subject, score, date FROM history WHERE user_id = %s ORDER BY date DESC LIMIT 50", (session['user_id'],))
        history_data = cur.fetchall()
        return render_template('history.html', history=history_data)
    finally:
        if conn: conn.close()