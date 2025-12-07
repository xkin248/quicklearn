from flask import Flask
from routes.auth import auth_bp
from routes.main import main_bp
from routes.quiz import quiz_bp
import os
# IMPORT FROM NEW FILE
from database import get_db_connection, return_db_connection

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', '9f3b8d1c2a7e4f6g5h8j9k0l1m2n3o4p')

# ==========================================
#  REGISTER BLUEPRINTS
# ==========================================
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp)
app.register_blueprint(quiz_bp, url_prefix='/quiz')

# ==========================================
#  DATABASE INITIALIZATION
# ==========================================
def init_db():
    print("⏳ Checking Database Schema...")
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Users
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password VARCHAR(256) NOT NULL,
                xp INTEGER DEFAULT 0,
                language VARCHAR(10) DEFAULT 'en',
                streak INTEGER DEFAULT 0
            );
        """)

        # 2. Questions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                subject VARCHAR(50),
                difficulty VARCHAR(20),
                question_text TEXT,
                option_a VARCHAR(200),
                option_b VARCHAR(200),
                option_c VARCHAR(200),
                option_d VARCHAR(200),
                correct_answer VARCHAR(200),
                explanation TEXT,
                video_id VARCHAR(50),
                topic_title VARCHAR(100)
            );
        """)

        # 3. Missions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                id SERIAL PRIMARY KEY,
                title VARCHAR(100),
                title_bm VARCHAR(100),
                description VARCHAR(200),
                description_bm VARCHAR(200),
                target INTEGER,
                xp_reward INTEGER
            );
        """)
        
        # Ensure 'is_daily' column exists
        cur.execute("""
            ALTER TABLE missions 
            ADD COLUMN IF NOT EXISTS is_daily BOOLEAN DEFAULT TRUE;
        """)

        # 4. User Missions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_missions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                mission_id INTEGER REFERENCES missions(id),
                progress INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                date_assigned DATE DEFAULT CURRENT_DATE
            );
        """)

        # 5. Attempts
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                question_id INTEGER REFERENCES questions(id),
                is_correct BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 6. Subject Progress
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subject_progress (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                subject VARCHAR(50),
                mastery_level INTEGER DEFAULT 1,
                total_questions INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                UNIQUE(user_id, subject)
            );
        """)

        conn.commit()

        # --- SEED DATA ---
        from routes.quiz import questions_db
        if len(questions_db) > 0:
            questions_data = [
                (q['id'], q['subject'], q['difficulty'], q['question_text'], 
                 q['option_a'], q['option_b'], q['option_c'], q['option_d'], 
                 q['correct_answer'], q['explanation'], q.get('video_id', ''), q.get('topic_title', ''))
                for q in questions_db
            ]
            
            sql = """
                INSERT INTO questions (id, subject, difficulty, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, video_id, topic_title) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    subject = EXCLUDED.subject,
                    difficulty = EXCLUDED.difficulty,
                    question_text = EXCLUDED.question_text,
                    option_a = EXCLUDED.option_a,
                    option_b = EXCLUDED.option_b,
                    option_c = EXCLUDED.option_c,
                    option_d = EXCLUDED.option_d,
                    correct_answer = EXCLUDED.correct_answer,
                    explanation = EXCLUDED.explanation,
                    video_id = EXCLUDED.video_id,
                    topic_title = EXCLUDED.topic_title;
            """
            cur.executemany(sql, questions_data)

        cur.execute("SELECT COUNT(*) FROM missions")
        if cur.fetchone()[0] == 0:
            print("   - Seeding Missions...")
            missions_sql = """
                INSERT INTO missions (title, title_bm, description, description_bm, target, xp_reward) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            missions_data = [
                ('Daily Scholar', 'Cendekiawan Harian', 'Answer 5 questions correctly today.', 'Jawab 5 soalan dengan betul hari ini.', 5, 50),
                ('Math Whiz', 'Pakar Matematik', 'Complete 10 Math questions.', 'Selesaikan 10 soalan Matematik.', 10, 100)
            ]
            cur.executemany(missions_sql, missions_data)
        
        conn.commit()
        cur.close()
        print("✅ Database initialized & seeded successfully!")
        
    except Exception as e:
        print(f"❌ Database Init Error: {e}")
    finally:
        if conn: return_db_connection(conn)

# Run DB Check on Startup
init_db()

if __name__ == '__main__':
    app.run(debug=True)