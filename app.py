from flask import Flask, render_template, request, redirect, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret_key"


# -------------------------
#   DATABASE CONNECTION
# -------------------------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  
        database="houseprediction_db"
    )


# -------------------------
#   CREATE USERS TABLE
# -------------------------
def create_users_table():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
    cursor.close()
    db.close()


create_users_table()


# -------------------------
#   HOME PAGE
# -------------------------
@app.route('/')
def home():
    return render_template("home.html")


# -------------------------
#        REGISTER
# -------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('email')
        password = request.form['password']

        if not username:
            return render_template("registration.html", error="Email is required")

        password_hash = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash)
            )
            db.commit()
        except mysql.connector.errors.IntegrityError:
            return render_template("registration.html", error="Username already exists")

        cursor.close()
        db.close()
        return redirect('/login')

    return render_template("registration.html")


# -------------------------
#           LOGIN
# -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('email')
        password = request.form['password']

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username
            return redirect('/dashboard')
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


# -------------------------
#         DASHBOARD
# -------------------------
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template("prediction_input.html", username=session['username'])
    else:
        return redirect('/login')


# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')


# -------------------------
#    INPUT PAGE
# -------------------------
@app.route('/predict_input')
def predict_input():
    if 'username' not in session:
        return redirect('/login')
    return render_template("prediction_input.html")


# -------------------------
#    PREDICT RESULT
# -------------------------
@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return redirect('/login')

    # Read fields from `prediction_input.html` (bedrooms and sqft_living)
    try:
        bedrooms = int(request.form.get('bedrooms', 0))
        sqft_living = float(request.form.get('sqft_living', 0))
    except ValueError:
        return render_template("prediction_input.html", error="Invalid numeric input")

    predicted_price = (bedrooms * 50000) + (sqft_living * 200)

    return render_template("result.html", price=predicted_price)


# -------------------------
if __name__ == '__main__':
    app.run(debug=True)
