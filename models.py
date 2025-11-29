from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    xp = db.Column(db.Integer, default=0)
    language = db.Column(db.String(10), default='en')
    
    # --- NEW: Track current streak ---
    streak = db.Column(db.Integer, default=0) 
    
    attempts = db.relationship('Attempt', backref='student', lazy=True)
    user_missions = db.relationship('UserMission', backref='user', lazy=True)
    subject_progress = db.relationship('SubjectProgress', backref='user', lazy=True)

    def set_password(self, password_input):
        self.password = generate_password_hash(password_input)

    def check_password(self, password_input):
        return check_password_hash(self.password, password_input)

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(50))
    language = db.Column(db.String(10), default='en')
    difficulty = db.Column(db.String(20))
    question_text = db.Column(db.String(500))
    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))
    correct_answer = db.Column(db.String(200))
    hint = db.Column(db.String(200))
    explanation = db.Column(db.String(500))
    topic_title = db.Column(db.String(100))
    video_id = db.Column(db.String(20))
    
    attempts = db.relationship('Attempt', backref='question_attempt', lazy=True)

class Attempt(db.Model):
    __tablename__ = 'attempts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class SubjectProgress(db.Model):
    __tablename__ = 'subject_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    subject = db.Column(db.String(50))
    mastery_level = db.Column(db.Integer, default=1)
    total_questions = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)

    def update_mastery(self):
        self.mastery_level = 1 + (self.correct_answers // 5)

class Mission(db.Model):
    __tablename__ = 'missions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    title_bm = db.Column(db.String(100))
    description = db.Column(db.String(200))
    description_bm = db.Column(db.String(200))
    mission_type = db.Column(db.String(50))
    target_value = db.Column(db.Integer)
    xp_reward = db.Column(db.Integer)
    is_daily = db.Column(db.Boolean, default=True)

class UserMission(db.Model):
    __tablename__ = 'user_missions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    mission_id = db.Column(db.Integer, db.ForeignKey('missions.id'))
    progress = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)