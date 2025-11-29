from app import app, db
from sqlalchemy import text

def fix_null_values():
    with app.app_context():
        with db.engine.connect() as conn:
            print("Fixing database values...")
            
            # 1. Fix User Streak
            conn.execute(text("UPDATE users SET streak = 0 WHERE streak IS NULL"))
            
            # 2. Fix Subject Progress (The cause of your crash)
            conn.execute(text("UPDATE subject_progress SET total_questions = 0 WHERE total_questions IS NULL"))
            conn.execute(text("UPDATE subject_progress SET correct_answers = 0 WHERE correct_answers IS NULL"))
            conn.execute(text("UPDATE subject_progress SET mastery_level = 1 WHERE mastery_level IS NULL"))
            
            conn.commit()
            print("✅ Success! Database repaired.")

if __name__ == '__main__':
    fix_null_values()