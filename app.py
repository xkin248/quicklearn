from flask import Flask, session
import os
from sqlalchemy import text
from models import db, User, Question, Mission
from helpers import translations

# Import Blueprints
from routes.auth import auth_bp
from routes.main import main_bp
from routes.quiz import quiz_bp

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key-123')

# --- DATABASE SETUP ---
database_url = os.environ.get('DATABASE_URL', 'sqlite:///quicklearn.db') 
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(quiz_bp)

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

# --- AUTO-DEPLOY FUNCTION (Fixes Render DB) ---
def initialize_database():
    with app.app_context():
        # 1. Create Tables
        db.create_all()
        
        # 2. Fix Missing Columns (Streak)
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN streak INTEGER DEFAULT 0"))
                conn.commit()
                print("✅ Added 'streak' column.")
        except Exception:
            pass 

        # 3. Seed Missions
        if not Mission.query.first():
            print("🌱 Seeding Missions...")
            missions_data = [
                {'title': 'Daily Learner', 'title_bm': 'Pelajar Harian', 'description': 'Complete 5 questions', 'description_bm': 'Lengkapkan 5 soalan', 'mission_type': 'daily_questions', 'target_value': 5, 'xp_reward': 50, 'is_daily': True},
                {'title': 'Math Master', 'title_bm': 'Pakar Matematik', 'description': 'Answer 3 Math questions', 'description_bm': 'Jawab 3 soalan Matematik', 'mission_type': 'subject_specific', 'target_value': 3, 'xp_reward': 30, 'is_daily': True}
            ]
            for m in missions_data:
                db.session.add(Mission(**m))
            db.session.commit()

        # 4. Seed Questions
        if not Question.query.first():
            print("🌱 Seeding Questions...")
            questions = [
                # English
                Question(subject='Mathematics', language='en', difficulty='easy', question_text='What is 5 + 7?', option_a='10', option_b='12', option_c='13', option_d='14', correct_answer='12', hint='Count on fingers', explanation='5 + 7 = 12', topic_title='Addition', video_id='AuX7nPBqDts'),
                Question(subject='Science', language='en', difficulty='medium', question_text='Which planet is known as the Red Planet?', option_a='Venus', option_b='Mars', option_c='Jupiter', option_d='Saturn', correct_answer='Mars', hint='God of War', explanation='Iron oxide makes it red.', topic_title='Space', video_id='D8VIjF7jFac'),
                Question(subject='History', language='en', difficulty='medium', question_text='Who was the first Prime Minister of Malaysia?', option_a='Tun Razak', option_b='Tunku Abdul Rahman', option_c='Tun Hussein', option_d='Mahathir', correct_answer='Tunku Abdul Rahman', hint='Merdeka', explanation='Father of Independence.', topic_title='Merdeka', video_id='hKpbANaPh8C'),
                # BM
                Question(subject='Mathematics', language='bm', difficulty='easy', question_text='Berapakah 5 + 7?', option_a='10', option_b='12', option_c='13', option_d='14', correct_answer='12', hint='Kira guna jari', explanation='5 + 7 = 12', topic_title='Tambah', video_id='Fe8u2I3vmHU'),
                Question(subject='Science', language='bm', difficulty='medium', question_text='Planet manakah yang dikenali sebagai Planet Merah?', option_a='Zuhrah', option_b='Marikh', option_c='Musytari', option_d='Zuhal', correct_answer='Marikh', hint='Dewa Perang', explanation='Marikh merah kerana oksida besi.', topic_title='Angkasa', video_id='71qkmfDpW1S'),
                Question(subject='History', language='bm', difficulty='medium', question_text='Siapakah Perdana Menteri Malaysia yang pertama?', option_a='Tun Abdul Razak', option_b='Tunku Abdul Rahman', option_c='Tun Hussein Onn', option_d='Tun Dr. Mahathir', correct_answer='Tunku Abdul Rahman', hint='Beliau dikenali sebagai Bapa Kemerdekaan.', explanation='Tunku Abdul Rahman Putra Al-Haj merupakan Perdana Menteri Malaysia yang pertama.', topic_title='Sejarah Malaysia', video_id='QOIM5knf22p')
            ]
            for q in questions:
                db.session.add(q)
            db.session.commit()

# --- RUN ON STARTUP ---
initialize_database()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')