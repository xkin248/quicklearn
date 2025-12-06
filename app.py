import psycopg2
import psycopg2.extras
from flask import Flask, redirect, url_for, session
from routes.auth import auth_bp
from routes.main import main_bp
from routes.quiz import quiz_bp

app = Flask(__name__)
app.secret_key = '9f3b8d1c2a7e4f6g5h8j9k0l1m2n3o4p'

# ==========================================
#  DATABASE CONFIGURATION
# ==========================================
DATABASE_URL = 'postgresql://neondb_owner:npg_zsbQNiH92vkl@ep-floral-hill-a1sq9ye6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&connect_timeout=30'

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ==========================================
#  TRANSLATIONS
# ==========================================
translations = {
    'en': {
        'explore': 'Explore Learning',
        'choose_subject': 'Choose a subject to start learning',
        'subjects': 'Subjects',
        'back_home': 'Back to Home',
        'submit': 'Submit Answer',
        'correct': 'Correct!',
        'incorrect': 'Incorrect',
        'explanation': 'Explanation',
        'home': 'Home',
        'settings': 'Settings',
        'logout': 'Log Out',
        'start_quiz': 'Start Quiz',
        'next': 'Next',
        'history': 'Learning History',
        'welcome': 'Welcome back',
        'ready_msg': 'Ready to learn something new?',
        'xp': 'Total XP',
        'appearance': 'Appearance',
        'dark_mode': 'Dark Mode',
        'light_mode': 'Light Mode',
        'language': 'Language'
    },
    'bm': {
        'explore': 'Terokai Pembelajaran',
        'choose_subject': 'Pilih subjek untuk mula belajar',
        'subjects': 'Subjek',
        'back_home': 'Kembali ke Utama',
        'submit': 'Hantar Jawapan',
        'correct': 'Betul!',
        'incorrect': 'Salah',
        'explanation': 'Penerangan',
        'home': 'Utama',
        'settings': 'Tetapan',
        'logout': 'Log Keluar',
        'start_quiz': 'Mula Kuiz',
        'next': 'Seterusnya',
        'history': 'Sejarah Pembelajaran',
        'welcome': 'Selamat Kembali',
        'ready_msg': 'Sedia untuk belajar sesuatu yang baru?',
        'xp': 'Jumlah XP',
        'appearance': 'Penampilan',
        'dark_mode': 'Mod Gelap',
        'light_mode': 'Mod Cerah',
        'language': 'Bahasa'
    }
}

@app.context_processor
def inject_translations():
    lang = session.get('lang', 'en')
    if lang not in translations: lang = 'en'
    return dict(t=translations[lang])

# ==========================================
#  REGISTER BLUEPRINTS
# ==========================================
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp)
app.register_blueprint(quiz_bp, url_prefix='/quiz')

@app.route('/')
def root():
    return redirect(url_for('main.index'))

# ==========================================
#  DATABASE INITIALIZATION & SEEDING
# ==========================================
def init_db():
    """Initializes tables and seeds data in the Neon DB."""
    print("⏳ Checking Database Schema...")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Users Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(200) NOT NULL,
                xp INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                last_active DATE,
                language VARCHAR(10) DEFAULT 'en'
            );
        """)
        
        # 2. History Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                subject VARCHAR(50),
                score INTEGER,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. Progress Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                subject VARCHAR(50),
                mastery_level INTEGER DEFAULT 1,
                total_answered INTEGER DEFAULT 0,
                UNIQUE(user_id, subject)
            );
        """)

        # 4. Missions Table (Updated with Malay support)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                id SERIAL PRIMARY KEY,
                title VARCHAR(100),
                title_bm VARCHAR(100),
                description TEXT,
                description_bm TEXT,
                target INTEGER,
                xp_reward INTEGER
            );
        """)

        # 5. Questions Table (Updated with Video/Topic info)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                subject VARCHAR(50),
                difficulty VARCHAR(20),
                question_text TEXT,
                option_a VARCHAR(255),
                option_b VARCHAR(255),
                option_c VARCHAR(255),
                option_d VARCHAR(255),
                correct_answer VARCHAR(255),
                explanation TEXT,
                video_id VARCHAR(50),
                topic_title VARCHAR(255)
            );
        """)
        
        # 6. Create SUBJECT_PROGRESS Table (This was missing!)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subject_progress (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                subject VARCHAR(50),
                mastery_level INTEGER DEFAULT 1,
                total_questions INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0
            );
        """)

        # --- SEED DATA LOGIC ---
        
        # Check if questions exist
        cur.execute("SELECT COUNT(*) FROM questions")
        if cur.fetchone()[0] == 0:
            print("   - Seeding Questions Database...")
            
            # Full dataset from your request
            questions_data = [
                # MATH
                (101, "Mathematics", "Easy", "In the term 5x, what is '5' called?", "Variable", "Coefficient", "Constant", "Power", "Coefficient", "The number multiplied by a variable is called the coefficient.", "dN3sPEtTZPE", "Algebra: Simplifying Expressions"),
                (102, "Mathematics", "Easy", "Which of the following is a 'like term' to 3ab?", "3a", "4b", "-7ab", "3ac", "-7ab", "Like terms must have exactly the same variables. 3ab and -7ab both have 'ab'.", None, None),
                (103, "Mathematics", "Medium", "Simplify: 2x + 5x - 3x", "4x", "5x", "10x", "3x", "4x", "2x + 5x = 7x. Then 7x - 3x = 4x.", None, None),
                (104, "Mathematics", "Medium", "Value of 2x + 3 when x = 4?", "9", "10", "11", "14", "11", "2(4) + 3 = 8 + 3 = 11.", None, None),
                (105, "Mathematics", "Hard", "Simplify: 3(x + 2) + 4", "3x + 6", "3x + 10", "3x + 2", "7x + 2", "3x + 10", "3x + 6 + 4 = 3x + 10.", None, None),
                (106, "Mathematics", "Easy", "In 4y - 9, what is the constant?", "4", "y", "9", "-9", "-9", "The term without a variable is -9.", None, None),
                (107, "Mathematics", "Medium", "Simplify: 5a - 2b - 3a + 6b", "2a + 4b", "8a + 8b", "2a - 4b", "8a - 4b", "2a + 4b", "Combine a's (2a) and b's (4b).", None, None),
                (108, "Mathematics", "Medium", "Coefficient of x in: x - 5", "0", "1", "5", "-5", "1", "x is implicitly 1x.", None, None),
                (109, "Mathematics", "Hard", "'3 less than twice x' is...", "3 - 2x", "2x - 3", "2(x - 3)", "x^2 - 3", "2x - 3", "Twice x is 2x, 3 less is -3.", None, None),
                (110, "Mathematics", "Easy", "Letters representing numbers are...", "Digits", "Variables", "Integers", "Sums", "Variables", "Letters like x, y are variables.", None, None),

                # SCIENCE
                (201, "Science", "Easy", "Process by which plants make food?", "Respiration", "Digestion", "Photosynthesis", "Fermentation", "Photosynthesis", "Plants use sunlight to make food via photosynthesis.", "D1Ymc311XS8", "Biology: Photosynthesis"),
                (202, "Science", "Easy", "Gas absorbed during photosynthesis?", "Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen", "Carbon Dioxide", "Plants take in CO2.", None, None),
                (203, "Science", "Medium", "Green pigment trapping sunlight?", "Chlorophyll", "Chloroplast", "Cytoplasm", "Cellulose", "Chlorophyll", "Chlorophyll absorbs light energy.", None, None),
                (204, "Science", "Medium", "Main products of photosynthesis?", "CO2 & Water", "Glucose & Oxygen", "Water & Oxygen", "Glucose & CO2", "Glucose & Oxygen", "It creates sugar (glucose) and releases oxygen.", None, None),
                (205, "Science", "Easy", "Where does photosynthesis occur?", "Roots", "Stem", "Leaves", "Flowers", "Leaves", "Leaves have the most chloroplasts.", None, None),
                (206, "Science", "Medium", "Tiny pores on leaves?", "Veins", "Stomata", "Chloroplasts", "Pores", "Stomata", "Stomata allow gas exchange.", None, None),
                (207, "Science", "Hard", "Part absorbing water?", "Leaves", "Flowers", "Roots", "Bark", "Roots", "Roots take water from soil.", None, None),
                (208, "Science", "Hard", "Food produced is a type of...", "Protein", "Fat", "Sugar", "Vitamin", "Sugar", "Glucose is a simple sugar.", None, None),
                (209, "Science", "Medium", "Energy form needed?", "Heat", "Light", "Sound", "Kinetic", "Light", "Sunlight powers the reaction.", None, None),
                (210, "Science", "Easy", "Benefit to humans?", "Warms earth", "Produces Oxygen", "Uses Oxygen", "Creates soil", "Produces Oxygen", "We need the oxygen it releases.", None, None),

                # HISTORY
                (301, "History", "Easy", "Founder of Malacca Sultanate?", "Tun Perak", "Parameswara", "Sultan Muzaffar", "Hang Tuah", "Parameswara", "Parameswara founded Melaka around 1400.", "L0EiJZRxQUY", "Kesultanan Melayu Melaka"),
                (302, "History", "Easy", "'Melaka' was named after a...", "River", "Tree", "Stone", "Deer", "Tree", "Named after the Melaka tree.", None, None),
                (303, "History", "Medium", "Animal that kicked the hunting dog?", "Tiger", "White Mousedeer", "Elephant", "Crocodile", "White Mousedeer", "The Pelanduk Putih showed courage.", None, None),
                (304, "History", "Medium", "Why was Melaka strategic?", "Hidden", "Trade route", "Gold mines", "Island", "Trade route", "It controlled the China-India trade route.", None, None),
                (305, "History", "Medium", "Title of Chief Minister?", "Laksamana", "Temenggung", "Bendahara", "Syahbandar", "Bendahara", "Bendahara was the chief administrator.", None, None),
                (306, "History", "Hard", "Famous Admiral (Laksamana)?", "Hang Jebat", "Hang Tuah", "Hang Kasturi", "Hang Lekir", "Hang Tuah", "Hang Tuah is the legendary warrior.", None, None),
                (307, "History", "Hard", "Religion spread via Melaka?", "Hinduism", "Buddhism", "Islam", "Christianity", "Islam", "Melaka was a center for Islamic propagation.", None, None),
                (308, "History", "Easy", "Conquered Melaka in 1511?", "Dutch", "British", "Portuguese", "Japanese", "Portuguese", "The Portuguese invaded in 1511.", None, None),
                (309, "History", "Medium", "Parameswara came from...", "Majapahit", "Palembang", "Siam", "Pasai", "Palembang", "He was a prince of Palembang.", None, None),
                (310, "History", "Hard", "Melaka laws were in...", "Hukum Kanun Melaka", "Undang-Undang Laut", "Batu Bersurat", "Sejarah Melayu", "Hukum Kanun Melaka", "The land laws were codified here.", None, None),

                # ENGLISH
                (401, "English", "Easy", "Yesterday, I _____ to the park.", "go", "going", "went", "gone", "went", "Past tense of 'go' is 'went'.", "K8kqQDyZ1ik", "Grammar: Simple Past Tense"),
                (402, "English", "Easy", "Past tense of 'play'?", "play", "played", "plaied", "playing", "played", "Add -ed for regular verbs.", None, None),
                (403, "English", "Medium", "She _____ happy last night.", "is", "were", "was", "are", "was", "Singular 'She' uses 'was'.", None, None),
                (404, "English", "Medium", "They _____ football yesterday.", "didn't played", "didn't play", "don't played", "not play", "didn't play", "After 'didn't', use base verb.", None, None),
                (405, "English", "Hard", "Which is correct?", "Did you saw him?", "Did you see him?", "Did you seen him?", "Do you saw him?", "Did you see him?", "Did + base verb (see).", None, None),
                (406, "English", "Medium", "Past tense of 'eat'?", "eated", "ate", "eaten", "eating", "ate", "Irregular: eat -> ate.", None, None),
                (407, "English", "Medium", "We _____ our homework.", "finish", "finished", "finishing", "finishes", "finished", "Finished (past action).", None, None),
                (408, "English", "Hard", "He _____ (buy) a car.", "buyed", "bought", "brought", "buying", "bought", "Buy -> Bought.", None, None),
                (409, "English", "Easy", "Word indicating past tense?", "Tomorrow", "Now", "Yesterday", "Next week", "Yesterday", "Yesterday = past.", None, None),
                (410, "English", "Medium", "I _____ (sleep) well.", "sleeped", "slept", "sleeping", "sleeps", "slept", "Sleep -> Slept.", None, None)
            ]
            
            sql = """
                INSERT INTO questions (id, subject, difficulty, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, video_id, topic_title) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
            """
            cur.executemany(sql, questions_data)

        # Check if missions exist
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
        conn.close()
        print("✅ Database initialized & seeded successfully!")
        
    except Exception as e:
        print(f"❌ Database Initialization Error: {e}")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)