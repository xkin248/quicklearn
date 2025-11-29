from app import app, db
from sqlalchemy import text

def repair():
    with app.app_context():
        with db.engine.connect() as conn:
            print("--- Starting Repair ---")

            # 1. Add 'streak' column if missing
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN streak INTEGER DEFAULT 0"))
                print("✅ Added 'streak' column.")
            except Exception:
                print("ℹ️ 'streak' column likely already exists.")

            # 2. Fix NULL values that cause crashes
            conn.execute(text("UPDATE users SET streak = 0 WHERE streak IS NULL"))
            conn.execute(text("UPDATE subject_progress SET total_questions = 0 WHERE total_questions IS NULL"))
            conn.execute(text("UPDATE subject_progress SET correct_answers = 0 WHERE correct_answers IS NULL"))
            conn.execute(text("UPDATE subject_progress SET mastery_level = 1 WHERE mastery_level IS NULL"))
            
            conn.commit()
            print("✅ Database data repaired.")

if __name__ == '__main__':
    repair()