from flask import Flask, render_template, redirect, url_for, session, request, flash
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Import modules
from models import db, User, Question, Attempt
from helpers import translations, subjects

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key-123')

# --- DATABASE SETUP ---
database_url = os.environ.get('DATABASE_URL', 'postgresql://neondb_owner:npg_zsbQNiH92vkl@ep-floral-hill-a1sq9ye6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require')

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- CONTEXT PROCESSOR ---
@app.context_processor
def inject_user_language():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        lang = user.language if user else 'en'
    else:
        lang = 'en'
    return dict(lang=lang, t=translations.get(lang, translations['en']))

# --- ROUTES ---

@app.route('/')
def home():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            return render_template('register.html', error="Username taken")
        
        new_user = User(username=request.form['username'])
        new_user.set_password(request.form['password']) 
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/subjects')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('index.html', subjects=subjects)

@app.route('/settings')
def settings():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    return render_template('settings.html', user=user)

# --- QUIZ LOGIC UPDATED ---

@app.route('/start_subject/<subject_name>')
def start_subject(subject_name):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    lang = user.language if user else 'en'

    # Filter by subject AND language
    questions = Question.query.filter_by(subject=subject_name, language=lang).all()
    
    # Initialize attempts if not set
    current_attempts = session.get('attempts', 0)

    # Ensure we reset if we switched questions unexpectedly
    if session.get('current_q_id') != id:
        session['current_q_id'] = id
        session['attempts'] = 0
        current_attempts = 0

    return render_template('quiz.html', q=q, attempts=current_attempts)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    q = db.session.get(Question, int(request.form.get('question_id')))
    
    # Check Answer
    is_correct = (request.form.get('option') == q.correct_answer)
    
    # --- NEW LOGIC: 3 Strikes Rule ---
    
    if is_correct:
        # 1. Answered Correctly!
        session['attempts'] = 0 # Reset for next time
        db.session.add(Attempt(user_id=user.id, question_id=q.id, is_correct=True))
        user.xp += 20
        db.session.commit()
        return render_template('result.html', is_correct=True, explanation=q.explanation, answer=q.correct_answer, question_id=q.id)
    
    else:
        # 2. Incorrect Answer
        current_attempts = session.get('attempts', 0) + 1
        session['attempts'] = current_attempts
        
        if current_attempts < 3:
            flash(f"Incorrect! {3 - current_attempts} attempts left.", "warning")
            return redirect(url_for('quiz', id=q.id))
        else:
            # 3. Failed (3rd Strike)
            session['attempts'] = 0
            db.session.add(Attempt(user_id=user.id, question_id=q.id, is_correct=False))
            db.session.commit()
            return render_template('result.html', is_correct=False, explanation=q.explanation, answer=q.correct_answer, question_id=q.id)

@app.route('/history')
def history():
    if 'user_id' not in session: return redirect(url_for('login'))
    my_attempts = Attempt.query.filter_by(user_id=session['user_id']).all()
    history_data = []
    for attempt in my_attempts:
        q = db.session.get(Question, attempt.question_id)
        if q:
            history_data.append({'subject': q.subject, 'question': q.question_text, 'is_correct': attempt.is_correct})
    history_data.reverse()
    return render_template('history.html', history=history_data)

@app.route('/set_language/<lang_code>')
def set_language(lang_code):
    if lang_code in ['en', 'bm'] and 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        user.language = lang_code
        db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')