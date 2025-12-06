from flask import Blueprint, render_template, session, redirect, url_for
import psycopg2
import psycopg2.extras
# IMPORT TRANSLATIONS FROM HELPERS.PY
from helpers import translations 

main_bp = Blueprint('main', __name__)

# Database URL (Matches app.py)
DATABASE_URL = 'postgresql://neondb_owner:npg_zsbQNiH92vkl@ep-floral-hill-a1sq9ye6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&connect_timeout=30'

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@main_bp.route('/')
def index():
    if 'user_id' in session: 
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session: 
        return redirect(url_for('auth.login'))

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # 1. Get User Data
        cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        row = cur.fetchone()
        if not row:
            session.clear()
            return redirect(url_for('auth.login'))
        user = dict(row)

        # 2. Level & XP Logic
        current_xp = user['xp']
        level = (current_xp // 100) + 1      
        xp_progress = current_xp % 100       
        xp_percent = (xp_progress / 100) * 100 

        # 3. Get Subject Progress
        cur.execute("SELECT * FROM subject_progress WHERE user_id = %s", (session['user_id'],))
        progress_rows = cur.fetchall()
        user_progress = {row['subject']: row['mastery_level'] for row in progress_rows}

        # 4. Get Daily Missions
        cur.execute("""
            SELECT m.*, 
            CASE WHEN um.user_id IS NOT NULL THEN TRUE ELSE FALSE END as completed
            FROM missions m
            LEFT JOIN user_missions um ON m.id = um.mission_id AND um.user_id = %s
            WHERE m.is_daily = TRUE
        """, (session['user_id'],))
        missions_data = cur.fetchall()

        # 5. Render Template
        # We use translations.get() to safely load the language (defaults to English)
        return render_template('dashboard.html', 
                             user=user, 
                             t=translations.get(session.get('lang', 'en'), translations['en']), 
                             progress=user_progress, 
                             missions=missions_data,
                             level=level,             
                             xp_progress=xp_progress, 
                             xp_percent=xp_percent)   

    except Exception as e:
        print(f"Dashboard Error: {e}")
        return "Database Error (Check terminal for details)", 500
    finally:
        if conn: conn.close()

@main_bp.route('/subjects')
def subjects_page():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get progress to show mastery levels on cards
        cur.execute("SELECT * FROM subject_progress WHERE user_id = %s", (session['user_id'],))
        progress_rows = cur.fetchall()
        user_progress = {row['subject']: row['mastery_level'] for row in progress_rows}
        
        subjects = ["Mathematics", "Science", "History", "English"]
        return render_template('subjects.html', 
                               subjects=subjects, 
                               progress=user_progress,
                               t=translations.get(session.get('lang', 'en'), translations['en']))
    finally:
        if conn: conn.close()

@main_bp.route('/settings')
def settings():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    return render_template('settings.html', 
                           t=translations.get(session.get('lang', 'en'), translations['en']))

@main_bp.route('/set_language/<lang_code>')
def set_language(lang_code):
    if lang_code in ['en', 'bm']:
        session['lang'] = lang_code
    return redirect(url_for('main.settings'))