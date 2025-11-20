from flask import Flask, render_template, redirect, url_for, session, request

app = Flask(__name__)
app.secret_key = 'your-secret-key'

subjects = [
    'Malay Language',
    'English',
    'Chinese Language',
    'Mathematics',
    'Science',
    'History'
]

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@app.route('/dashboard')
def dashboard():
    if not session.get('username'):
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/subjects')
def index():
    if not session.get('username'):
        return redirect(url_for('login'))
    return render_template('index.html', subjects=subjects, username=session['username'])

if __name__ == '__main__':
    app.run(debug=True)
