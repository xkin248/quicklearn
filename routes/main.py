from flask import Blueprint, render_template, session, redirect, url_for
import psycopg2
import psycopg2.extras
from helpers import translations 
# Import DB connection from app.py
from database import get_db_connection, return_db_connection

main_bp = Blueprint('main', __name__)

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

        # 2. XP & Level Logic
        current_xp = user['xp']
        level = (current_xp // 100) + 1      
        xp_progress = current_xp % 100       
        xp_percent = (xp_progress / 100) * 100 

        # 3. Get Subject Progress
        cur.execute("SELECT * FROM subject_progress WHERE user_id = %s", (session['user_id'],))
        progress_rows = cur.fetchall()
        user_progress = {row['subject']: row['mastery_level'] for row in progress_rows}

        # --- NEW FIX: ASSIGN MISSIONS IF MISSING ---
        # This SQL inserts missions into user_missions ONLY if they don't exist yet
        cur.execute("""
            INSERT INTO user_missions (user_id, mission_id, progress, completed, date_assigned)
            SELECT %s, id, 0, FALSE, CURRENT_DATE
            FROM missions
            WHERE id NOT IN (
                SELECT mission_id FROM user_missions 
                WHERE user_id = %s
            );
        """, (session['user_id'], session['user_id']))
        conn.commit()
        # -------------------------------------------

        # 4. Fetch User Missions for Display
        cur.execute("""
            SELECT m.title, m.description, m.xp_reward, m.target, 
                   um.progress, um.completed 
            FROM missions m
            JOIN user_missions um ON m.id = um.mission_id
            WHERE um.user_id = %s
            ORDER BY um.completed ASC, m.id ASC
        """, (session['user_id'],))
        missions_data = cur.fetchall()

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
        return "Database Error", 500
    finally:
        if conn: return_db_connection(conn)

@main_bp.route('/subjects')
def subjects_page():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("SELECT * FROM subject_progress WHERE user_id = %s", (session['user_id'],))
        progress_rows = cur.fetchall()
        user_progress = {row['subject']: row['mastery_level'] for row in progress_rows}
        
        subjects = ["Mathematics", "Science", "History", "English"]
        return render_template('subjects.html', 
                               subjects=subjects, 
                               progress=user_progress,
                               t=translations.get(session.get('lang', 'en'), translations['en']))
    finally:
        if conn: return_db_connection(conn)

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