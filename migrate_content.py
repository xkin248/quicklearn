from app import app, db
from models import Question
from sqlalchemy import text

def migrate_and_seed():
    with app.app_context():
        # 1. Add 'language' column if it doesn't exist
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE question ADD COLUMN language VARCHAR(10) DEFAULT 'en'"))
                conn.commit()
                print("Added 'language' column to question table.")
        except Exception as e:
            print(f"Column might already exist or error: {e}")

        # 2. Seed BM Questions (Duplicate existing EN questions and translate them)
        # For demonstration, we'll create a few specific BM questions
        
        # Check if we already have BM questions
        if Question.query.filter_by(language='bm').first():
            print("BM questions already exist. Skipping seed.")
            return

        # Sample BM Questions
        bm_questions = [
            Question(
                subject='Mathematics',
                language='bm',
                question_text='Berapakah 5 + 7?',
                option_a='10', option_b='11', option_c='12', option_d='13',
                correct_answer='12',
                hint='Ia lebih besar daripada 10.',
                explanation='5 tambah 7 bersamaan dengan 12.',
                topic_title='Penambahan Asas'
            ),
            Question(
                subject='Science',
                language='bm',
                question_text='Planet manakah yang dikenali sebagai Planet Merah?',
                option_a='Zuhrah', option_b='Marikh', option_c='Musytari', option_d='Zuhal',
                correct_answer='Marikh',
                hint='Ia dinamakan sempena dewa perang Rom.',
                explanation='Marikh kelihatan merah kerana oksida besi di permukaannya.',
                topic_title='Sistem Suria'
            ),
             Question(
                subject='History',
                language='bm',
                question_text='Siapakah Perdana Menteri Malaysia yang pertama?',
                option_a='Tun Abdul Razak', option_b='Tunku Abdul Rahman', option_c='Tun Hussein Onn', option_d='Tun Dr. Mahathir',
                correct_answer='Tunku Abdul Rahman',
                hint='Beliau dikenali sebagai Bapa Kemerdekaan.',
                explanation='Tunku Abdul Rahman Putra Al-Haj merupakan Perdana Menteri Malaysia yang pertama.',
                topic_title='Sejarah Malaysia'
            )
        ]

        for q in bm_questions:
            db.session.add(q)
        
        db.session.commit()
        print(f"Seeded {len(bm_questions)} BM questions.")

if __name__ == '__main__':
    migrate_and_seed()
