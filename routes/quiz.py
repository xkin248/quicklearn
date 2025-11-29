from flask import Blueprint, render_template, redirect, url_for, session, request, flash
import random
from datetime import datetime, timezone
from models import db, User, Question, Attempt, SubjectProgress, UserMission, Mission
from helpers import subjects

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/start_subject/<subject_name>')
def start_subject(subject_name):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    user = db.session.get(User, session['user_id'])
    lang = user.language if user else 'en'

    # Fetch questions for the subject
    questions = Question.query.filter_by(subject=subject_name, language=lang).all()
    # Fallback to English if no questions in user's language
    if not questions and lang != 'en':
        questions = Question.query.filter_by(subject=subject_name, language='en').all()

    if not questions: 
        flash("No questions available for this subject yet!", "info")
        return redirect(url_for('main.dashboard'))
    
    # Pick a random question
    next_q = random.choice(questions)
    
    session['attempts'] = 0
    session['current_q_id'] = next_q.id
    
    # Redirect to Video or Quiz
    if next_q.video_id:
        return redirect(url_for('quiz.video_page', id=next_q.id))
    else:
        return redirect(url_for('quiz.quiz', id=next_q.id))

@quiz_bp.route('/start_random')
def start_random():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    chosen_subject = random.choice(subjects)
    return redirect(url_for('quiz.start_subject', subject_name=chosen_subject))

@quiz_bp.route('/video/<int:id>')
def video_page(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    q = db.session.get(Question, id)
    if not q: return redirect(url_for('main.dashboard'))
    return render_template('video.html', q=q)

@quiz_bp.route('/quiz/<int:id>')
def quiz(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    q = db.session.get(Question, id)
    if not q: return redirect(url_for('main.dashboard'))

    current_attempts = session.get('attempts', 0)
    if str(session.get('current_q_id')) != str(id):
        session['current_q_id'] = id
        session['attempts'] = 0
        current_attempts = 0

    return render_template('quiz.html', q=q, attempts=current_attempts)

@quiz_bp.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    user = db.session.get(User, session['user_id'])
    question_id = request.form.get('question_id')
    q = db.session.get(Question, int(question_id))
    
    if not q: return redirect(url_for('main.dashboard'))

    is_correct = (request.form.get('option') == q.correct_answer)
    
    if is_correct:
        # CORRECT ANSWER
        session['attempts'] = 0
        user.streak = (user.streak or 0) + 1
        db.session.add(Attempt(user_id=user.id, question_id=q.id, is_correct=True))
        
        xp_award = {'easy': 10, 'medium': 20, 'hard': 30}.get(q.difficulty, 20)
        user.xp += xp_award
        
        # Update Subject Progress
        subject_prog = SubjectProgress.query.filter_by(user_id=user.id, subject=q.subject).first()
        if not subject_prog:
            subject_prog = SubjectProgress(
                user_id=user.id, subject=q.subject, 
                total_questions=0, correct_answers=0, mastery_level=1
            )
            db.session.add(subject_prog)
        
        # Safety Check for NULLs
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
            return redirect(url_for('quiz.quiz', id=q.id))
        else:
            session['attempts'] = 0
            user.streak = 0
            db.session.add(Attempt(user_id=user.id, question_id=q.id, is_correct=False))
            
            subject_prog = SubjectProgress.query.filter_by(user_id=user.id, subject=q.subject).first()
            if not subject_prog:
                subject_prog = SubjectProgress(
                    user_id=user.id, subject=q.subject, 
                    total_questions=0, correct_answers=0, mastery_level=1
                )
                db.session.add(subject_prog)

            if subject_prog.total_questions is None: subject_prog.total_questions = 0
            
            subject_prog.total_questions += 1
            subject_prog.update_mastery()
            
            db.session.commit()
            return render_template('result.html', is_correct=False, explanation=q.explanation, answer=q.correct_answer, question_id=q.id, q=q)

@quiz_bp.route('/history')
def history():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    my_attempts = Attempt.query.filter_by(user_id=session['user_id']).order_by(Attempt.timestamp.desc()).limit(50).all()
    history_data = []
    for attempt in my_attempts:
        q = db.session.get(Question, attempt.question_id)
        if q:
            history_data.append({'subject': q.subject, 'question': q.question_text, 'is_correct': attempt.is_correct})
    return render_template('history.html', history=history_data)