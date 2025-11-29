from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    xp = db.Column(db.Integer, default=0)
    language = db.Column(db.String(10), default='en')
    attempts = db.relationship('Attempt', backref='student', lazy=True)

    def set_password(self, password_input):
        self.password = generate_password_hash(password_input)

    def check_password(self, password_input):
        return check_password_hash(self.password, password_input)

    # --- NEW FUNCTION: Calculates Streak ---
    def get_current_streak(self):
        # Sort attempts by newest first (reverse order of ID)
        attempts = sorted(self.attempts, key=lambda x: x.id, reverse=True)
        streak = 0
        for attempt in attempts:
            if attempt.is_correct:
                streak += 1
            else:
                break # Stop counting if we find a wrong answer
        return streak

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(50))
    language = db.Column(db.String(10), default='en') # 'en' or 'bm'
    question_text = db.Column(db.String(200))
    option_a = db.Column(db.String(100))
    option_b = db.Column(db.String(100))
    option_c = db.Column(db.String(100))
    option_d = db.Column(db.String(100))
    correct_answer = db.Column(db.String(100))
    hint = db.Column(db.String(200))
    explanation = db.Column(db.String(300))
    video_id = db.Column(db.String(20))
    topic_title = db.Column(db.String(100))

    def get_options(self):
        return [self.option_a, self.option_b, self.option_c, self.option_d]

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)