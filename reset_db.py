from app import app, db
from sqlalchemy import text

with app.app_context():
    print("Resetting database...")
    with db.engine.connect() as conn:
        conn.execute(text('DROP TABLE IF EXISTS attempt CASCADE;'))
        conn.execute(text('DROP TABLE IF EXISTS question CASCADE;'))
        conn.execute(text('DROP TABLE IF EXISTS "user" CASCADE;'))
        conn.commit()
    db.create_all()
    print("Done! Register a new account.")