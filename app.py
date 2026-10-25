import os
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-development-secret")

# PostgreSQL is used when DATABASE_URL is configured. SQLite is provided for easy local testing.
DATABASE_URL = os.environ.get("DATABASE_URL", "")
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg
    from psycopg.rows import dict_row
else:
    import sqlite3

DB_PATH = os.environ.get("SQLITE_PATH", "bus_pass.db")


def get_conn():
    if USE_POSTGRES:
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return psycopg.connect(url, row_factory=dict_row)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user')""")
        cur.execute("""CREATE TABLE IF NOT EXISTS routes (
            id SERIAL PRIMARY KEY, origin TEXT NOT NULL, destination TEXT NOT NULL,
            distance_km INTEGER NOT NULL DEFAULT 0, active BOOLEAN NOT NULL DEFAULT TRUE)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY, booking_code TEXT UNIQUE NOT NULL, user_id INTEGER NOT NULL REFERENCES users(id),
            route_id INTEGER NOT NULL REFERENCES routes(id), pass_type TEXT NOT NULL,
            amount NUMERIC(10,2) NOT NULL, status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    else:
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user')""")
        cur.execute("""CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, origin TEXT NOT NULL, destination TEXT NOT NULL,
            distance_km INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, booking_code TEXT UNIQUE NOT NULL, user_id INTEGER NOT NULL,
            route_id INTEGER NOT NULL, pass_type TEXT NOT NULL, amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(route_id) REFERENCES routes(id))""")
    cur.execute("SELECT COUNT(*) AS n FROM routes")
    row = cur.fetchone()
    count = row["n"] if isinstance(row, dict) else row[0]
    if count == 0:
        routes = [
            ("Surat Railway Station", "Sarthana", 12),
            ("Adajan", "Udhna", 14),
            ("Varachha", "Citylight", 10),
            ("Sarthana", "Adajan", 16),
        ]
        for route in routes:
            cur.execute("INSERT INTO routes (origin, destination, distance_km) VALUES (%s, %s, %s)" if USE_POSTGRES else
                        "INSERT INTO routes (origin, destination, distance_km) VALUES (?, ?, ?)", route)
    conn.commit()
    cur.close()
    conn.close()


def query_all(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def query_one(sql, params=()):
    rows = query_all(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    result = getattr(cur, "lastrowid", None)
    cur.close()
    conn.close()
    return result


def placeholder():
    return "%s" if USE_POSTGRES else "?"


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    routes = query_all("SELECT * FROM routes WHERE active = TRUE" if USE_POSTGRES else
                       "SELECT * FROM routes WHERE active = 1")
    return render_template("index.html", routes=routes)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email, and a password of at least 8 characters.", "danger")
            return render_template("register.html")
        try:
            p = placeholder()
            execute(f"INSERT INTO users (name, email, password_hash) VALUES ({p}, {p}, {p})",
                    (name, email, generate_password_hash(password)))
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        except Exception:
            flash("Could not create account. This email may already be registered.", "danger")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        p = placeholder()
        user = query_one(f"SELECT * FROM users WHERE email = {p}", (email,))
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("my_passes"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/apply", methods=["GET", "POST"])
@login_required
def apply():
    routes = query_all("SELECT * FROM routes WHERE active = TRUE" if USE_POSTGRES else
                       "SELECT * FROM routes WHERE active = 1")
    prices = {"Daily": 50, "Monthly": 1200, "Student": 600}
    if request.method == "POST":
        try:
            route_id = int(request.form.get("route_id", "0"))
        except ValueError:
            route_id = 0
        pass_type = request.form.get("pass_type", "")
        if pass_type not in prices:
            flash("Choose a valid pass type.", "danger")
            return render_template("apply.html", routes=routes, prices=prices)
        route = query_one(f"SELECT * FROM routes WHERE id = {placeholder()}", (route_id,))
        if not route:
            flash("Choose a valid route.", "danger")
            return render_template("apply.html", routes=routes, prices=prices)
        amount = prices[pass_type]
        code = "BP-" + secrets.token_hex(4).upper()
        p = placeholder()
        execute(f"INSERT INTO bookings (booking_code, user_id, route_id, pass_type, amount, status) VALUES ({p}, {p}, {p}, {p}, {p}, {p})",
                (code, session["user_id"], route_id, pass_type, amount, "Confirmed"))
        booking = query_one(f"SELECT * FROM bookings WHERE booking_code = {p}", (code,))
        flash("Your demo bus pass booking has been created.", "success")
        return render_template("confirmation.html", booking=booking, route=route, pass_type=pass_type)
    return render_template("apply.html", routes=routes, prices=prices)


@app.route("/my-passes")
@login_required
def my_passes():
    p = placeholder()
    bookings = query_all(
        f"""SELECT b.*, r.origin, r.destination FROM bookings b
        JOIN routes r ON r.id = b.route_id WHERE b.user_id = {p}
        ORDER BY b.id DESC""", (session["user_id"],))
    return render_template("my_passes.html", bookings=bookings)


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if session.get("role") != "admin":
        flash("Admin access only. Create an admin account securely before using this page.", "danger")
        return redirect(url_for("index"))
    if request.method == "POST":
        origin = request.form.get("origin", "").strip()
        destination = request.form.get("destination", "").strip()
        try:
            distance = max(0, int(request.form.get("distance_km", "0")))
        except ValueError:
            distance = 0
        if origin and destination:
            p = placeholder()
            execute(f"INSERT INTO routes (origin, destination, distance_km) VALUES ({p}, {p}, {p})",
                    (origin, destination, distance))
            flash("Route added.", "success")
        return redirect(url_for("admin"))
    routes = query_all("SELECT * FROM routes ORDER BY id DESC")
    bookings = query_all("""SELECT b.*, u.name, u.email, r.origin, r.destination
        FROM bookings b JOIN users u ON u.id=b.user_id JOIN routes r ON r.id=b.route_id
        ORDER BY b.id DESC""")
    return render_template("admin.html", routes=routes, bookings=bookings)


@app.errorhandler(500)
def server_error(error):
    return render_template("error.html"), 500


with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
