from flask import Flask, render_template, redirect, url_for, session, request, flash
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

# Import modules
from models import db, User, Question, Attempt, SubjectProgress, UserMission, Mission
from helpers import translations, subjects

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key-123')

# --- DATABASE SETUP ---
database_url = os.environ.get('DATABASE_URL', 'sqlite:///quicklearn.db') 
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
        if not user:
            session.clear()
            return dict(lang='en', t=translations['en'])
        lang = user.language if user else 'en'
    else:
        lang = 'en'
    return dict(lang=lang, t=translations.get(lang, translations['en']))

# --- ROUTES ---

@app.route('/')
def home():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/index')
def index():
    return redirect(url_for('home'))

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
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Username taken")
        
        new_user = User(username=username)
        new_user.set_password(password) 
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', error="An error occurred during registration.")

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    # Calculate Total Answered Questions (Handle None values safely)
    total_answered = sum((p.total_questions or 0) for p in user.subject_progress)

    # Get Subject Progress
    user_progress = {p.subject: p.mastery_level for p in user.subject_progress}
    
    # Get Daily Missions
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    daily_missions_defs = Mission.query.filter_by(is_daily=True).all()
    missions_status = []
    
    for mission_def in daily_missions_defs:
        um = UserMission.query.filter(
            UserMission.user_id == user.id,
            UserMission.mission_id == mission_def.id,
            UserMission.created_at >= today_start
        ).first()
        
        progress = um.progress if um else 0
        completed = um.completed if um else False
            
        missions_status.append({
            'title': mission_def.title_bm if user.language == 'bm' else mission_def.title,
            'description': mission_def.description_bm if user.language == 'bm' else mission_def.description,
            'progress': progress,
            'target': mission_def.target_value,
            'completed': completed,
            'reward': mission_def.xp_reward
        })

    return render_template('dashboard.html', 
                           user=user, 
                           subjects=subjects, 
                           progress=user_progress, 
                           missions=missions_status,
                           total_answered=total_answered)

@app.route('/start_subject/<subject_name>')
def start_subject(subject_name):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    lang = user.language if user else 'en'

    questions = Question.query.filter_by(subject=subject_name, language=lang).all()
    if not questions and lang != 'en':
        questions = Question.query.filter_by(subject=subject_name, language='en').all()

    if not questions: 
        flash("No questions available for this subject yet!", "info")
        return redirect(url_for('dashboard'))
    
    next_q = random.choice(questions)
    
    session['attempts'] = 0
    session['current_q_id'] = next_q.id
    
    if next_q.video_id:
        return redirect(url_for('video_page', id=next_q.id))
    else:
        return redirect(url_for('quiz', id=next_q.id))

@app.route('/start_random')
def start_random():
    if 'user_id' not in session: return redirect(url_for('login'))
    chosen_subject = random.choice(subjects)
    return redirect(url_for('start_subject', subject_name=chosen_subject))

@app.route('/video/<int:id>')
def video_page(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    q = db.session.get(Question, id)
    if not q: return redirect(url_for('dashboard'))
    return render_template('video.html', q=q)

@app.route('/quiz/<int:id>')
def quiz(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    q = db.session.get(Question, id)
    if not q: return redirect(url_for('dashboard'))

    current_attempts = session.get('attempts', 0)
    if str(session.get('current_q_id')) != str(id):
        session['current_q_id'] = id
        session['attempts'] = 0
        current_attempts = 0

    return render_template('quiz.html', q=q, attempts=current_attempts)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    question_id = request.form.get('question_id')
    q = db.session.get(Question, int(question_id))
    
    if not q: return redirect(url_for('dashboard'))

    is_correct = (request.form.get('option') == q.correct_answer)
    
    if is_correct:
        # CORRECT ANSWER
        session['attempts'] = 0
        user.streak = (user.streak or 0) + 1
        db.session.add(Attempt(user_id=user.id, question_id=q.id, is_correct=True))
        
        xp_award = {'easy': 10, 'medium': 20, 'hard': 30}.get(q.difficulty, 20)
        user.xp += xp_award
        
        subject_prog = SubjectProgress.query.filter_by(user_id=user.id, subject=q.subject).first()
        if not subject_prog:
            subject_prog = SubjectProgress(
                user_id=user.id, 
                subject=q.subject, 
                total_questions=0, 
                correct_answers=0, 
                mastery_level=1
            )
            db.session.add(subject_prog)
        
        # FIX: Ensure counters are not None
        if subject_prog.total_questions is None: subject_prog.total_questions = 0
        if subject_prog.correct_answers is None: subject_prog.correct_answers = 0
        
        subject_prog.total_questions += 1
        subject_prog.correct_answers += 1
        subject_prog.update_mastery()
        
        # Mission Logic
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        daily_mission = Mission.query.filter_by(mission_type='daily_questions', is_daily=True).first()
        
        if daily_mission:
            user_mission = UserMission.query.filter(
                UserMission.user_id == user.id,
                UserMission.mission_id == daily_mission.id,
                UserMission.created_at >= today_start
            ).first()
            
            if not user_mission:
                user_mission = UserMission(user_id=user.id, mission_id=daily_mission.id)
                db.session.add(user_mission)
            
            # --- FIX: Ensure progress is not None ---
            if user_mission.progress is None: user_mission.progress = 0
            
            if not user_mission.completed:
                user_mission.progress += 1
                if user_mission.progress >= daily_mission.target_value:
                    user_mission.completed = True
                    user_mission.completed_at = datetime.now(timezone.utc)
                    user.xp += daily_mission.xp_reward
                    flash(f"Mission Complete! +{daily_mission.xp_reward} XP", "success")
        
        db.session.commit()
        return render_template('result.html', is_correct=True, explanation=q.explanation, answer=q.correct_answer, question_id=q.id, q=q)
    
    else:
        # INCORRECT ANSWER
        current_attempts = session.get('attempts', 0) + 1
        session['attempts'] = current_attempts
        
        if current_attempts < 3:
            flash(f"Incorrect! {3 - current_attempts} attempts left.", "warning")
            return redirect(url_for('quiz', id=q.id))
        else:
            session['attempts'] = 0
            user.streak = 0
            db.session.add(Attempt(user_id=user.id, question_id=q.id, is_correct=False))
            
            subject_prog = SubjectProgress.query.filter_by(user_id=user.id, subject=q.subject).first()
            if not subject_prog:
                subject_prog = SubjectProgress(
                    user_id=user.id, 
                    subject=q.subject, 
                    total_questions=0, 
                    correct_answers=0, 
                    mastery_level=1
                )
                db.session.add(subject_prog)

            # FIX: Ensure counters are not None
            if subject_prog.total_questions is None: subject_prog.total_questions = 0
            
            subject_prog.total_questions += 1
            subject_prog.update_mastery()
            
            db.session.commit()
            return render_template('result.html', is_correct=False, explanation=q.explanation, answer=q.correct_answer, question_id=q.id, q=q)

@app.route('/history')
def history():
    if 'user_id' not in session: return redirect(url_for('login'))
    my_attempts = Attempt.query.filter_by(user_id=session['user_id']).order_by(Attempt.timestamp.desc()).limit(50).all()
    history_data = []
    for attempt in my_attempts:
        q = db.session.get(Question, attempt.question_id)
        if q:
            history_data.append({'subject': q.subject, 'question': q.question_text, 'is_correct': attempt.is_correct})
    return render_template('history.html', history=history_data)

@app.route('/set_language/<lang_code>')
def set_language(lang_code):
    if lang_code in ['en', 'bm'] and 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user:
            user.language = lang_code
            db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/settings')
def settings():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    return render_template('settings.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')