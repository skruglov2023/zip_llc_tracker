from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os, datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change for production
app.config['UPLOAD_FOLDER'] = 'static/uploads'


# ---------------------------
# Database setup
# ---------------------------
def init_db():
    conn = sqlite3.connect('scooters.db')
    c = conn.cursor()

    # scooters table
    c.execute('''CREATE TABLE IF NOT EXISTS scooters
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     name
                     TEXT,
                     in_use
                     INTEGER
                     DEFAULT
                     0,
                     lat
                     REAL,
                     lon
                     REAL,
                     last_user
                     TEXT,
                     photo
                     TEXT,
                     updated
                     TIMESTAMP
                 )''')

    # users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     name
                     TEXT,
                     phone
                     TEXT
                     UNIQUE
                 )''')

    conn.commit()
    conn.close()


with app.app_context():
    init_db()


# ---------------------------
# Routes
# ---------------------------
@app.route('/')
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect('scooters.db')
    conn.row_factory = sqlite3.Row  # this makes rows behave like dictionaries
    c = conn.cursor()
    c.execute("SELECT * FROM scooters")
    rows = c.fetchall()

    # convert to list of dicts so Jinja can use it
    scooters = [dict(row) for row in rows]
    print(scooters)
    conn.close()

    return render_template("index.html", scooters=scooters, user=session.get('user'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']

        conn = sqlite3.connect('scooters.db')
        c = conn.cursor()
        c.execute("SELECT name, phone FROM users WHERE phone=?", (phone,))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = {"name": user[0], "phone": user[1]}
            return redirect(url_for('index'))
        else:
            return "Access denied. Contact admin to be added.", 403

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/take', methods=['POST'])
def take():
    if "user" not in session:
        return redirect(url_for("login"))

    scooter_id = request.form.get('scooter_id')
    user = session['user']['name']

    conn = sqlite3.connect('scooters.db')
    c = conn.cursor()
    c.execute("UPDATE scooters SET in_use=?, last_user=?, updated=? WHERE id=?",
              (1, user, datetime.datetime.now(), scooter_id))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))


@app.route('/update', methods=['POST'])
def update():
    if "user" not in session:
        return redirect(url_for("login"))

    scooter_id = request.form.get('scooter_id')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    user = session['user']['name']
    photo = None

    if 'photo' in request.files:
        file = request.files['photo']
        if file.filename:
            photo = f"{datetime.datetime.now().timestamp()}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo))

    conn = sqlite3.connect('scooters.db')
    c = conn.cursor()
    c.execute("""UPDATE scooters
                 SET in_use=?,
                     lat=?,
                     lon=?,
                     last_user=?,
                     photo=?,
                     updated=?
                 WHERE id = ?""",
              (0, lat, lon, user, photo, datetime.datetime.now(), scooter_id))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
