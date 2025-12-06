from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import psycopg2
import psycopg2.extras
import random
import os
# IMPORT TRANSLATIONS
from helpers import translations

quiz_bp = Blueprint('quiz', __name__)

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://neondb_owner:npg_zsbQNiH92vkl@ep-floral-hill-a1sq9ye6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&connect_timeout=30')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ==========================================
#  VIDEO & TOPIC CONFIGURATION
# ==========================================
subject_videos = {
    "Mathematics":  {"topic_title": "Algebra: Simplifying Expressions", "video_id": "dN3sPEtTZPE", "start_id": 101},
    "Science":      {"topic_title": "States of Matter", "video_id": "wclY8F-UoTE", "start_id": 201},
    "History":      {"topic_title": "Kesultanan Melayu Melaka",         "video_id": "L0EiJZRxQUY", "start_id": 301},
    "English":      {"topic_title": "Grammar: Simple Past Tense",       "video_id": "K8kqQDyZ1ik", "start_id": 401}
}

# FULL QUESTION DATABASE
questions_db = [
    # MATH
    {"id": 101, "subject": "Mathematics", "difficulty": "Easy", "question_text": "In the term 5x, what is '5' called?", "option_a": "Variable", "option_b": "Coefficient", "option_c": "Constant", "option_d": "Power", "correct_answer": "Coefficient", "explanation": "The number multiplied by a variable is called the coefficient.", "video_id": "dN3sPEtTZPE", "topic_title": "Algebra: Simplifying Expressions"},
    {"id": 102, "subject": "Mathematics", "difficulty": "Easy", "question_text": "Which of the following is a 'like term' to 3ab?", "option_a": "3a", "option_b": "4b", "option_c": "-7ab", "option_d": "3ac", "correct_answer": "-7ab", "explanation": "Like terms must have exactly the same variables. 3ab and -7ab both have 'ab'."},
    {"id": 103, "subject": "Mathematics", "difficulty": "Medium", "question_text": "Simplify: 2x + 5x - 3x", "option_a": "4x", "option_b": "5x", "option_c": "10x", "option_d": "3x", "correct_answer": "4x", "explanation": "2x + 5x = 7x. Then 7x - 3x = 4x."},
    {"id": 104, "subject": "Mathematics", "difficulty": "Medium", "question_text": "Value of 2x + 3 when x = 4?", "option_a": "9", "option_b": "10", "option_c": "11", "option_d": "14", "correct_answer": "11", "explanation": "2(4) + 3 = 8 + 3 = 11."},
    {"id": 105, "subject": "Mathematics", "difficulty": "Hard", "question_text": "Simplify: 3(x + 2) + 4", "option_a": "3x + 6", "option_b": "3x + 10", "option_c": "3x + 2", "option_d": "7x + 2", "correct_answer": "3x + 10", "explanation": "3x + 6 + 4 = 3x + 10."},
    {"id": 106, "subject": "Mathematics", "difficulty": "Easy", "question_text": "In 4y - 9, what is the constant?", "option_a": "4", "option_b": "y", "option_c": "9", "option_d": "-9", "correct_answer": "-9", "explanation": "The term without a variable is -9."},
    {"id": 107, "subject": "Mathematics", "difficulty": "Medium", "question_text": "Simplify: 5a - 2b - 3a + 6b", "option_a": "2a + 4b", "option_b": "8a + 8b", "option_c": "2a - 4b", "option_d": "8a - 4b", "correct_answer": "2a + 4b", "explanation": "Combine a's (2a) and b's (4b)."},
    {"id": 108, "subject": "Mathematics", "difficulty": "Medium", "question_text": "Coefficient of x in: x - 5", "option_a": "0", "option_b": "1", "option_c": "5", "option_d": "-5", "correct_answer": "1", "explanation": "x is implicitly 1x."},
    {"id": 109, "subject": "Mathematics", "difficulty": "Hard", "question_text": "'3 less than twice x' is...", "option_a": "3 - 2x", "option_b": "2x - 3", "option_c": "2(x - 3)", "option_d": "x^2 - 3", "correct_answer": "2x - 3", "explanation": "Twice x is 2x, 3 less is -3."},
    {"id": 110, "subject": "Mathematics", "difficulty": "Easy", "question_text": "Letters representing numbers are...", "option_a": "Digits", "option_b": "Variables", "option_c": "Integers", "option_d": "Sums", "correct_answer": "Variables", "explanation": "Letters like x, y are variables."},
    
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
    {"id": 301, "subject": "History", "difficulty": "Easy", "question_text": "Founder of Malacca Sultanate?", "option_a": "Tun Perak", "option_b": "Parameswara", "option_c": "Sultan Muzaffar", "option_d": "Hang Tuah", "correct_answer": "Parameswara", "explanation": "Parameswara founded Melaka around 1400.", "video_id": "L0EiJZRxQUY", "topic_title": "Kesultanan Melayu Melaka"},
    {"id": 302, "subject": "History", "difficulty": "Easy", "question_text": "'Melaka' was named after a...", "option_a": "River", "option_b": "Tree", "option_c": "Stone", "option_d": "Deer", "correct_answer": "Tree", "explanation": "Named after the Melaka tree."},
    {"id": 303, "subject": "History", "difficulty": "Medium", "question_text": "Animal that kicked the hunting dog?", "option_a": "Tiger", "option_b": "White Mousedeer", "option_c": "Elephant", "option_d": "Crocodile", "correct_answer": "White Mousedeer", "explanation": "The Pelanduk Putih showed courage."},
    {"id": 304, "subject": "History", "difficulty": "Medium", "question_text": "Why was Melaka strategic?", "option_a": "Hidden", "option_b": "Trade route", "option_c": "Gold mines", "option_d": "Island", "correct_answer": "Trade route", "explanation": "It controlled the China-India trade route."},
    {"id": 305, "subject": "History", "difficulty": "Medium", "question_text": "Title of Chief Minister?", "option_a": "Laksamana", "option_b": "Temenggung", "option_c": "Bendahara", "option_d": "Syahbandar", "correct_answer": "Bendahara", "explanation": "Bendahara was the chief administrator."},
    {"id": 306, "subject": "History", "difficulty": "Hard", "question_text": "Famous Admiral (Laksamana)?", "option_a": "Hang Jebat", "option_b": "Hang Tuah", "option_c": "Hang Kasturi", "option_d": "Hang Lekir", "correct_answer": "Hang Tuah", "explanation": "Hang Tuah is the legendary warrior."},
    {"id": 307, "subject": "History", "difficulty": "Hard", "question_text": "Religion spread via Melaka?", "option_a": "Hinduism", "option_b": "Buddhism", "option_c": "Islam", "option_d": "Christianity", "correct_answer": "Islam", "explanation": "Melaka was a center for Islamic propagation."},
    {"id": 308, "subject": "History", "difficulty": "Easy", "question_text": "Conquered Melaka in 1511?", "option_a": "Dutch", "option_b": "British", "option_c": "Portuguese", "option_d": "Japanese", "correct_answer": "Portuguese", "explanation": "The Portuguese invaded in 1511."},
    {"id": 309, "subject": "History", "difficulty": "Medium", "question_text": "Parameswara came from...", "option_a": "Majapahit", "option_b": "Palembang", "option_c": "Siam", "option_d": "Pasai", "correct_answer": "Palembang", "explanation": "He was a prince of Palembang."},
    {"id": 310, "subject": "History", "difficulty": "Hard", "question_text": "Melaka laws were in...", "option_a": "Hukum Kanun Melaka", "option_b": "Undang-Undang Laut", "option_c": "Batu Bersurat", "option_d": "Sejarah Melayu", "correct_answer": "Hukum Kanun Melaka", "explanation": "The land laws were codified here."},

    # ENGLISH
    {"id": 401, "subject": "English", "difficulty": "Easy", "question_text": "Yesterday, I _____ to the park.", "option_a": "go", "option_b": "going", "option_c": "went", "option_d": "gone", "correct_answer": "went", "explanation": "Past tense of 'go' is 'went'.", "video_id": "K8kqQDyZ1ik", "topic_title": "Grammar: Simple Past Tense"},
    {"id": 402, "subject": "English", "difficulty": "Easy", "question_text": "Past tense of 'play'?", "option_a": "play", "option_b": "played", "option_c": "plaied", "option_d": "playing", "correct_answer": "played", "explanation": "Add -ed for regular verbs."},
    {"id": 403, "subject": "English", "difficulty": "Medium", "question_text": "She _____ happy last night.", "option_a": "is", "option_b": "were", "option_c": "was", "option_d": "are", "correct_answer": "was", "explanation": "Singular 'She' uses 'was'."},
    {"id": 404, "subject": "English", "difficulty": "Medium", "question_text": "They _____ football yesterday.", "option_a": "didn't played", "option_b": "didn't play", "option_c": "don't played", "option_d": "not play", "correct_answer": "didn't play", "explanation": "After 'didn't', use base verb."},
    {"id": 405, "subject": "English", "difficulty": "Hard", "question_text": "Which is correct?", "option_a": "Did you saw him?", "option_b": "Did you see him?", "option_c": "Did you seen him?", "option_d": "Do you saw him?", "correct_answer": "Did you see him?", "explanation": "Did + base verb (see)."},
    {"id": 406, "subject": "English", "difficulty": "Medium", "question_text": "Past tense of 'eat'?", "option_a": "eated", "option_b": "ate", "option_c": "eaten", "option_d": "eating", "correct_answer": "ate", "explanation": "Irregular: eat -> ate."},
    {"id": 407, "subject": "English", "difficulty": "Medium", "question_text": "We _____ our homework.", "option_a": "finish", "option_b": "finished", "option_c": "finishing", "option_d": "finishes", "correct_answer": "finished", "explanation": "Finished (past action)."},
    {"id": 408, "subject": "English", "difficulty": "Hard", "question_text": "He _____ (buy) a car.", "option_a": "buyed", "option_b": "bought", "option_c": "brought", "option_d": "buying", "correct_answer": "bought", "explanation": "Buy -> Bought."},
    {"id": 409, "subject": "English", "difficulty": "Easy", "question_text": "Word indicating past tense?", "option_a": "Tomorrow", "option_b": "Now", "option_c": "Yesterday", "option_d": "Next week", "correct_answer": "Yesterday", "explanation": "Yesterday = past."},
    {"id": 410, "subject": "English", "difficulty": "Medium", "question_text": "I _____ (sleep) well.", "option_a": "sleeped", "option_b": "slept", "option_c": "sleeping", "option_d": "sleeps", "correct_answer": "slept", "explanation": "Sleep -> Slept."}
]

@quiz_bp.route('/start_subject/<subject_name>')
def start_subject(subject_name):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    # Check if subject exists
    if subject_name not in subject_videos:
        return redirect(url_for('main.subjects_page'))
    
    session['current_subject'] = subject_name
    video_data = subject_videos[subject_name]
    
    # Show the video lecture page first
    return render_template('video.html', 
                           q={"subject": subject_name, **video_data}, 
                           t=translations.get(session.get('lang', 'en'), translations['en']))

@quiz_bp.route('/quiz/<int:id>', methods=['GET'])
def quiz(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Fetch question from DB
        cur.execute("SELECT * FROM questions WHERE id = %s", (id,))
        question = cur.fetchone()
        
        if not question:
            return redirect(url_for('main.dashboard'))
            
        return render_template('quiz.html', 
                               q=dict(question), 
                               t=translations.get(session.get('lang', 'en'), translations['en']))
    finally:
        if conn: conn.close()

@quiz_bp.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    question_id = request.form['question_id']
    selected_option = request.form['option']
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # 1. Get correct answer
        cur.execute("SELECT * FROM questions WHERE id = %s", (question_id,))
        question = cur.fetchone()
        
        is_correct = (selected_option == question['correct_answer'])
        
        # 2. Record Attempt
        cur.execute("""
            INSERT INTO attempts (user_id, question_id, is_correct)
            VALUES (%s, %s, %s)
        """, (session['user_id'], question_id, is_correct))
        
        # 3. Update XP if correct
        if is_correct:
            cur.execute("UPDATE users SET xp = xp + 10 WHERE id = %s", (session['user_id'],))
            
            # Update Subject Progress
            cur.execute("""
                INSERT INTO subject_progress (user_id, subject, correct_answers)
                VALUES (%s, %s, 1)
                ON CONFLICT (user_id, subject) 
                DO UPDATE SET correct_answers = subject_progress.correct_answers + 1;
            """, (session['user_id'], question['subject']))
            
            # Check Missions
            cur.execute("""
                UPDATE user_missions 
                SET progress = progress + 1 
                WHERE user_id = %s AND completed = FALSE
            """, (session['user_id'],))
            
            # Award Mission XP if completed
            cur.execute("""
                UPDATE user_missions um
                SET completed = TRUE
                FROM missions m
                WHERE um.mission_id = m.id AND um.progress >= m.target AND um.completed = FALSE AND um.user_id = %s
                RETURNING m.xp_reward
            """, (session['user_id'],))
            
            # Award extra XP from missions
            completed_missions = cur.fetchall()
            for mission in completed_missions:
                cur.execute("UPDATE users SET xp = xp + %s WHERE id = %s", (mission[0], session['user_id']))

        conn.commit()
        
        return render_template('result.html', 
                               is_correct=is_correct, 
                               explanation=question['explanation'],
                               t=translations.get(session.get('lang', 'en'), translations['en']))

    except Exception as e:
        print(f"Quiz Error: {e}")
        return redirect(url_for('main.dashboard'))
    finally:
        if conn: conn.close()

@quiz_bp.route('/next_question')
def next_question():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    current_subject = session.get('current_subject')
    if not current_subject: return redirect(url_for('main.dashboard'))

    # Filter questions list by subject
    subject_questions = [q for q in questions_db if q['subject'] == current_subject]
    
    if not subject_questions: return redirect(url_for('main.dashboard'))

    # Pick random question
    next_q = random.choice(subject_questions)
    return redirect(url_for('quiz.quiz', id=next_q['id']))

@quiz_bp.route('/history')
def history():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT a.*, q.question_text, q.subject 
            FROM attempts a
            JOIN questions q ON a.question_id = q.id
            WHERE a.user_id = %s
            ORDER BY a.timestamp DESC LIMIT 20
        """, (session['user_id'],))
        
        history_data = cur.fetchall()
        return render_template('history.html', 
                               history=history_data,
                               t=translations.get(session.get('lang', 'en'), translations['en']))
    finally:
        if conn: conn.close()