from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    xp = db.Column(db.Integer, default=0)
    language = db.Column(db.String(10), default='en')
    attempts = db.relationship('Attempt', backref='student', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(50))
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