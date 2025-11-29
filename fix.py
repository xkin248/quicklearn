from app import app, db
from sqlalchemy import text

def fix_missions():
    with app.app_context():
        with db.engine.connect() as conn:
            print("--- Fixing Mission Data ---")
            # Set NULL progress to 0
            conn.execute(text("UPDATE user_missions SET progress = 0 WHERE progress IS NULL"))
            # Set NULL completed status to False (0)
            conn.execute(text("UPDATE user_missions SET completed = 0 WHERE completed IS NULL"))
            conn.commit()
            print("✅ Success! Fixed 'NoneType' errors in user_missions.")

if __name__ == '__main__':
    fix_missions()