from flask import Flask, render_template, redirect, url_for, session, request
import random
import os

# Import from our split files
from models import db, User, Question, Attempt
from helpers import translations, subjects

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# --- DATABASE CONFIGURATION ---
# 1. Look for Render's Database URL
# 2. If not found, use your explicit Neon URL (for local testing)
database_url = os.environ.get('DATABASE_URL', 'postgresql://neondb_owner:npg_zsbQNiH92vkl@ep-floral-hill-a1sq9ye6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require')

# Fix for Render's Postgres URL format compatibility
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Connect Database
db.init_app(app)

# --- SEED DATA ---
def seed_questions():
    try:
        # Check if table exists and has data
        if db.session.execute(db.select(Question)).first(): 
            return
    except:
        pass 
    
    questions = [
        {"subject": "Mathematics", "q": "If a triangle has angles of 90° and 45°, what is the third angle?", "opts": ["30°", "45°", "60°", "90°"], "correct": "45°", "hint": "Angles must add up to 180°.", "exp": "180 - (90 + 45) = 45.", "vid": "mLeNaZcy-hE", "topic": "Triangle Angles"},
        {"subject": "Mathematics", "q": "What is 15% of 200?", "opts": ["20", "25", "30", "35"], "correct": "30", "hint": "10% is 20. 5% is 10.", "exp": "20 + 10 = 30.", "vid": "Ty9FPrMhWn4", "topic": "Percentages"},
        {"subject": "Science", "q": "Which planet is the Red Planet?", "opts": ["Venus", "Mars", "Jupiter", "Saturn"], "correct": "Mars", "hint": "Named after Roman god of war.", "exp": "Mars has iron oxide (rust).", "vid": "D8pNmTvqbTE", "topic": "Mars"},
        {"subject": "Science", "q": "What do plants absorb?", "opts": ["Oxygen", "CO2", "Nitrogen", "Hydrogen"], "correct": "CO2", "hint": "Humans breathe it out.", "exp": "Plants need CO2 for photosynthesis.", "vid": "Est pe_k665", "topic": "Photosynthesis"},
        {"subject": "History", "q": "First US President?", "opts": ["Jefferson", "Lincoln", "Washington", "Adams"], "correct": "Washington", "hint": "On the $1 bill.", "exp": "Served 1789-1797.", "vid": "hvE9fb--Dig", "topic": "US Presidents"},
        {"subject": "English", "q": "Which is a verb?", "opts": ["Run", "Blue", "Happy", "Table"], "correct": "Run", "hint": "An action word.", "exp": "Run is an action.", "vid": "MpD69k1c9T8", "topic": "Verbs"}
    ]

    for q in questions:
        new_q = Question(subject=q['subject'], question_text=q['q'], option_a=q['opts'][0], option_b=q['opts'][1], option_c=q['opts'][2], option_d=q['opts'][3], correct_answer=q['correct'], hint=q['hint'], explanation=q['exp'], video_id=q['vid'], topic_title=q['topic'])
        db.session.add(new_q)
    db.session.commit()
    print("Database Initialized!")

# --- HELPER: Language Injector ---
@app.context_processor
def inject_language():
    lang = 'en'
    if 'user_id' in session:
        try:
            user = db.session.get(User, session['user_id'])
            if user: lang = user.language
        except: pass
    elif 'lang' in session:
        lang = session['lang']
    return dict(lang=lang, t=translations)

# --- ROUTES ---

@app.route('/set_language/<lang_code>')
def set_language(lang_code):
    if lang_code in ['en', 'bm']:
        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
            user.language = lang_code
            db.session.commit()
        else:
            session['lang'] = lang_code
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            return render_template('register.html', error="Username taken")
        new_user = User(username=request.form['username'], password=request.form['password'])
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    return render_template('dashboard.html', username=user.username, xp=user.xp, level=(user.xp // 100) + 1, progress=user.xp % 100)

@app.route('/subjects')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('index.html', subjects=subjects)

@app.route('/start_subject/<subject_name>')
def start_subject(subject_name):
    if 'user_id' not in session: return redirect(url_for('login'))
    questions = Question.query.filter_by(subject=subject_name).all()
    if not questions: return "No content yet!"
    return redirect(url_for('lecture', id=random.choice(questions).id))

@app.route('/lecture/<int:id>')
def lecture(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('lecture.html', data=db.get_or_404(Question, id))

@app.route('/quiz/<int:id>')
def quiz(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    q = db.get_or_404(Question, id)
    return render_template('quiz.html', q={'id':q.id, 'subject':q.subject, 'question':q.question_text, 'options':q.get_options(), 'hint':q.hint})

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    q = db.session.get(Question, int(request.form.get('question_id')))
    is_correct = (request.form.get('option') == q.correct_answer)
    db.session.add(Attempt(user_id=user.id, question_id=q.id, is_correct=is_correct))
    if is_correct: user.xp += 20
    db.session.commit()
    return render_template('result.html', is_correct=is_correct, explanation=q.explanation, answer=q.correct_answer)

@app.route('/history')
def history():
    if 'user_id' not in session: return redirect(url_for('login'))
    my_attempts = Attempt.query.filter_by(user_id=session['user_id']).all()
    history_data = []
    for attempt in my_attempts:
        q = db.session.get(Question, attempt.question_id)
        history_data.append({
            'subject': q.subject,
            'topic': q.topic_title,
            'question': q.question_text,
            'is_correct': attempt.is_correct
        })
    history_data.reverse()
    return render_template('history.html', history=history_data)

# --- RUN CONFIG ---
# This block runs when you use 'python app.py' locally.
# Render uses 'gunicorn', so it skips this block.
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_questions()
    app.run(debug=True, host='0.0.0.0')