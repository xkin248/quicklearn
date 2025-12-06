from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import psycopg2
import psycopg2.extras

auth_bp = Blueprint('auth', __name__)

DATABASE_URL = 'postgresql://neondb_owner:npg_zsbQNiH92vkl@ep-floral-hill-a1sq9ye6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&connect_timeout=30'

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()

            if user and user['password'] == password:
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('main.dashboard'))
            else:
                return render_template('login.html', error="Invalid username or password")
        except Exception as e:
            print(f"Login Error: {e}")
            return render_template('login.html', error="Connection Error")
        finally:
            if conn: conn.close()
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return render_template('register.html', error="Username taken")
            
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            return redirect(url_for('auth.login'))
        except Exception:
            return render_template('register.html', error="Registration failed")
        finally:
            if conn: conn.close()
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))