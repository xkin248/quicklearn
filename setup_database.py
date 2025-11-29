from app import app, db
from models import Question, Mission, User, SubjectProgress
from sqlalchemy import text
from werkzeug.security import generate_password_hash

def setup_database():
    with app.app_context():
        print("--- 1. Resetting Database ---")
        # Drop all tables to start fresh
        with db.engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS user_missions;"))
            conn.execute(text("DROP TABLE IF EXISTS attempts;"))
            conn.execute(text("DROP TABLE IF EXISTS subject_progress;"))
            conn.execute(text("DROP TABLE IF EXISTS questions;"))
            conn.execute(text("DROP TABLE IF EXISTS missions;"))
            conn.execute(text("DROP TABLE IF EXISTS users;"))
            conn.commit()
        
        # Create tables based on current models
        db.create_all()
        print("Tables created successfully.")

        print("\n--- 2. Seeding Missions ---")
        missions_data = [
            {
                'title': 'Daily Learner', 
                'title_bm': 'Pelajar Harian', 
                'description': 'Complete 5 questions', 
                'description_bm': 'Lengkapkan 5 soalan', 
                'mission_type': 'daily_questions', 
                'target_value': 5, 
                'xp_reward': 50, 
                'is_daily': True
            },
            {
                'title': 'Math Master', 
                'title_bm': 'Pakar Matematik', 
                'description': 'Answer 3 Math questions', 
                'description_bm': 'Jawab 3 soalan Matematik', 
                'mission_type': 'subject_specific', 
                'target_value': 3, 
                'xp_reward': 30, 
                'is_daily': True
            }
        ]
        
        for m_data in missions_data:
            db.session.add(Mission(**m_data))
        print(f"Added {len(missions_data)} missions.")

        print("\n--- 3. Seeding Questions (with Videos) ---")
        questions = [
            # --- ENGLISH QUESTIONS ---
            Question(
                subject='Mathematics', language='en', difficulty='easy', 
                question_text='What is 5 + 7?', 
                option_a='10', option_b='12', option_c='13', option_d='14', 
                correct_answer='12', hint='Count on fingers', explanation='5 + 7 = 12', 
                topic_title='Addition', video_id='AuX7nPBqDts'
            ),
            Question(
                subject='Science', language='en', difficulty='medium', 
                question_text='Which planet is known as the Red Planet?', 
                option_a='Venus', option_b='Mars', option_c='Jupiter', option_d='Saturn', 
                correct_answer='Mars', hint='God of War', explanation='Iron oxide makes it red.', 
                topic_title='Space', video_id='D8VIjF7jFac'
            ),
            Question(
                subject='History', language='en', difficulty='medium', 
                question_text='Who was the first Prime Minister of Malaysia?', 
                option_a='Tun Razak', option_b='Tunku Abdul Rahman', option_c='Tun Hussein', option_d='Mahathir', 
                correct_answer='Tunku Abdul Rahman', hint='Merdeka', explanation='Father of Independence.', 
                topic_title='Merdeka', video_id='hKpbANaPh8C'
            ),
            
            # --- BM QUESTIONS ---
            Question(
                subject='Mathematics', language='bm', difficulty='easy', 
                question_text='Berapakah 5 + 7?', 
                option_a='10', option_b='12', option_c='13', option_d='14', 
                correct_answer='12', hint='Kira guna jari', explanation='5 + 7 = 12', 
                topic_title='Tambah', video_id='Fe8u2I3vmHU'
            ),
            Question(
                subject='Science', language='bm', difficulty='medium', 
                question_text='Planet manakah yang dikenali sebagai Planet Merah?', 
                option_a='Zuhrah', option_b='Marikh', option_c='Musytari', option_d='Zuhal', 
                correct_answer='Marikh', hint='Dewa Perang', explanation='Marikh merah kerana oksida besi.', 
                topic_title='Angkasa', video_id='71qkmfDpW1S'
            ),
            Question(
                subject='History', language='bm', difficulty='medium',
                question_text='Siapakah Perdana Menteri Malaysia yang pertama?',
                option_a='Tun Abdul Razak', option_b='Tunku Abdul Rahman', option_c='Tun Hussein Onn', option_d='Tun Dr. Mahathir',
                correct_answer='Tunku Abdul Rahman',
                hint='Beliau dikenali sebagai Bapa Kemerdekaan.',
                explanation='Tunku Abdul Rahman Putra Al-Haj merupakan Perdana Menteri Malaysia yang pertama.',
                topic_title='Sejarah Malaysia', video_id='QOIM5knf22p'
            )
        ]

        for q in questions:
            db.session.add(q)
        print(f"Added {len(questions)} questions.")

        db.session.commit()
        print("\n--- COMPLETE: Database setup finished successfully! ---")

if __name__ == '__main__':
    setup_database()