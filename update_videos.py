from app import app, db
from models import Question

def update_videos():
    with app.app_context():
        # --- MATHEMATICS ---
        # English: Basic Addition (Teacher Ira)
        q_math_en = Question.query.filter_by(subject='Mathematics', language='en').first()
        if q_math_en:
            q_math_en.video_id = 'AuX7nPBqDts'
            q_math_en.question_text = 'What is 5 + 7?' # Ensure text matches
            print("Updated Math EN video.")

        # BM: Matematik Tahun 1 Tambah
        q_math_bm = Question.query.filter_by(subject='Mathematics', language='bm').first()
        if q_math_bm:
            q_math_bm.video_id = 'Fe8u2I3vmHU' # Example ID for BM Math
            print("Updated Math BM video.")

        # --- SCIENCE ---
        # English: Mars for Kids (Learn Bright)
        q_sci_en = Question.query.filter_by(subject='Science', language='en').first()
        if q_sci_en:
            q_sci_en.video_id = 'D8VIjF7jFac'
            q_sci_en.question_text = 'Which planet is known as the Red Planet?'
            print("Updated Science EN video.")

        # BM: Planet Marikh
        q_sci_bm = Question.query.filter_by(subject='Science', language='bm').first()
        if q_sci_bm:
            q_sci_bm.video_id = '71qkmfDpW1S' # Example ID for BM Science
            print("Updated Science BM video.")

        # --- HISTORY ---
        # English: Merdeka History
        q_hist_en = Question.query.filter_by(subject='History', language='en').first()
        if q_hist_en:
            q_hist_en.video_id = 'hKpbANaPh8C' 
            q_hist_en.question_text = 'Who was the first Prime Minister of Malaysia?'
            print("Updated History EN video.")

        # BM: Pengisytiharan Kemerdekaan
        q_hist_bm = Question.query.filter_by(subject='History', language='bm').first()
        if q_hist_bm:
            q_hist_bm.video_id = 'QOIM5knf22p'
            print("Updated History BM video.")

        db.session.commit()
        print("All videos updated successfully!")

if __name__ == '__main__':
    update_videos()
