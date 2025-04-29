from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from markupsafe import escape

app = Flask(__name__)
app.secret_key = 'secret-key'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- DB Initialization ---
def init_db():
    conn = sqlite3.connect('site_data.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        location TEXT,
        description TEXT,
        image_path TEXT,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        comment TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    cursor.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (1, 'user1', 'pass1')")
    cursor.execute("INSERT OR IGNORE INTO admin (id, username, password) VALUES (1, 'admin', 'admin123')")
    cursor.execute("INSERT OR IGNORE INTO admin (id, username, password) VALUES (2, 'admin2', 'admin*123')")

    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login_choice', methods=['POST'])
def login_choice():
    role = request.form['role']
    if role == 'user':
        return redirect(url_for('user_login'))
    elif role == 'admin':
        return redirect(url_for('admin_login'))
    else:
        return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = escape(request.form['username'])
        password = request.form['password']
        conn = sqlite3.connect('site_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            return render_template('register.html', message="Username already exists.")

        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('user_login'))

    return render_template('register.html')

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = escape(request.form['username'])
        password = request.form['password']
        conn = sqlite3.connect('site_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('user_dashboard'))
        else:
            return render_template('user_login.html', message='Invalid credentials')
    return render_template('user_login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = escape(request.form['username'])
        password = request.form['password']
        conn = sqlite3.connect('site_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
        admin = cursor.fetchone()
        conn.close()
        if admin:
            session['admin_id'] = admin[0]
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', message='Invalid credentials')
    return render_template('admin_login.html')

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    return render_template('user_dashboard.html')

@app.route('/report', methods=['GET', 'POST'])
# def report():
#     if 'user_id' not in session:
#         return redirect(url_for('user_login'))
#     if request.method == 'POST':
#         location = escape(request.form['location'])
#         description = escape(request.form['description'])
#         file = request.files.get('image')
#         filename = None
#         if file and file.filename:
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(UPLOAD_FOLDER, filename))
#         conn = sqlite3.connect('site_data.db')
#         cursor = conn.cursor()
#         cursor.execute("INSERT INTO issues (user_id, location, description, image_path) VALUES (?, ?, ?, ?)",
#                        (session['user_id'], location, description, filename))
#         conn.commit()
#         conn.close()
#         return redirect(url_for('user_dashboard'))
#     return render_template('report_issue.html')

def report():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    
        
    if request.method == 'POST':

        isPriorityIssue = request.form.get('isPriorityIssue')=='on'

        
        
        location = request.form['location']
        description = request.form['description']
        file = request.files.get('image')
        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
        conn = sqlite3.connect('site_data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO issues (user_id, location, description, image_path) VALUES (?, ?, ?, ?)",
                    (session['user_id'], location, description, filename))
        conn.commit()
        conn.close()

        if isPriorityIssue: 
            return redirect(url_for('pay'))
        
        return redirect(url_for('user_dashboard'))
        

    return render_template('report_issue.html')


@app.route('/my_issues', methods=['GET'])
def my_issues():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    city = request.args.get('city')
    conn = sqlite3.connect('site_data.db')
    cursor = conn.cursor()

    if city:
        cursor.execute("SELECT location, description, image_path, status FROM issues WHERE user_id = ? AND location LIKE ?",
                       (session['user_id'], f"%{escape(city)}%"))
    else:
        cursor.execute("SELECT location, description, image_path, status FROM issues WHERE user_id = ?",
                       (session['user_id'],))
    issues = cursor.fetchall()
    conn.close()
    return render_template('user_issues.html', issues=issues, city=escape(city) if city else None)

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        city = request.form.get('location')
    else:
        city = request.args.get('city')

    conn = sqlite3.connect('site_data.db')
    cursor = conn.cursor()

    if city:
        cursor.execute("""
            SELECT issues.id, users.username, location, description, image_path, status
            FROM issues
            JOIN users ON issues.user_id = users.id
            WHERE location LIKE ?
        """, ('%' + escape(city) + '%',))
    else:
        cursor.execute("""
            SELECT issues.id, users.username, location, description, image_path, status
            FROM issues
            JOIN users ON issues.user_id = users.id
        """)

    issues = cursor.fetchall()

    cursor.execute("""
        SELECT feedback.id, users.username, feedback.comment
        FROM feedback
        JOIN users ON feedback.user_id = users.id
    """)
    feedbacks = cursor.fetchall()

    conn.close()
    return render_template('admin_dashboard.html', issues=issues, feedbacks=feedbacks, city=escape(city) if city else None)

@app.route('/update_status/<int:issue_id>', methods=['POST'])
def update_status(issue_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    new_status = escape(request.form['status'])
    conn = sqlite3.connect('site_data.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE issues SET status = ? WHERE id = ?", (new_status, issue_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        comment = escape(request.form['comment'])
        conn = sqlite3.connect('site_data.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO feedback (user_id, comment) VALUES (?, ?)", (session['user_id'], comment))
            conn.commit()
        except Exception as e:
            print("Feedback Error:", e)
        conn.close()
        return redirect(url_for('user_login'))

    return render_template('feedback.html')

from markupsafe import escape  # ✅ Correct


@app.route('/pay')
def pay():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    conn = sqlite3.connect('site_data.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT location, description, image_path FROM issues
        WHERE user_id = ? ORDER BY id DESC LIMIT 1
    """, (session['user_id'],))
    issue = cursor.fetchone()
    conn.close()
    if issue:
        # Escape each field
        issue = (
            escape(issue[0]),
            escape(issue[1]),
            escape(issue[2])
        )
    return render_template('payment_Page.html', issue=issue)

@app.route('/process_payment', methods=['POST'])
def process_payment():
    # Simulate processing (In real apps, use a secure payment gateway)
    card_number = request.form['card_number']
    name = request.form['name']
    expiry = request.form['expiry']
    cvv = request.form['cvv']

    # Print just for debug (do NOT do this in production!)
    print(f"Received payment details: {card_number}, {name}, {expiry}, {cvv}")
    
    # Redirect to a payment success page
    return redirect(url_for('payment_success'))

@app.route('/payment_success')
def payment_success():
    return render_template('payment_success.html')

@app.route('/delete_feedback/<int:feedback_id>', methods=['POST'])
def delete_feedback(feedback_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('site_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_issue/<int:issue_id>', methods=['POST'])
def delete_issue(issue_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('site_data.db')
    cursor = conn.cursor()
    
    # ✅ Fixed here
    cursor.execute("SELECT image_path FROM issues WHERE id = ?", (issue_id,))
    result = cursor.fetchone()
    if result and result[0]:
        image_path = os.path.join('static', 'uploads', result[0])
        if os.path.exists(image_path):
            os.remove(image_path)
    
    cursor.execute("DELETE FROM issues WHERE id = ?", (issue_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('admin_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
