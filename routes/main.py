from flask import Blueprint, render_template, redirect, url_for, session, request
from datetime import datetime, timezone
from models import db, User, Mission, UserMission
from helpers import subjects

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    if 'user_id' in session: return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/index')
def index():
    return redirect(url_for('main.home'))

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))

    # Calculate Total Answered Questions
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

@main_bp.route('/settings')
def settings():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    user = db.session.get(User, session['user_id'])
    return render_template('settings.html', user=user)

@main_bp.route('/set_language/<lang_code>')
def set_language(lang_code):
    if lang_code in ['en', 'bm'] and 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user:
            user.language = lang_code
            db.session.commit()
    return redirect(request.referrer or url_for('main.dashboard'))

@main_bp.route('/subjects')
def subjects_page():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    user = db.session.get(User, session['user_id'])
    # Get user progress to show levels on the cards
    user_progress = {p.subject: p.mastery_level for p in user.subject_progress}
    
    return render_template('subjects.html', user=user, subjects=subjects, progress=user_progress)