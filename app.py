import os
import sqlite3
import secrets
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deployment")
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "bus_passes.db"))

# Demo fare plans. Replace these amounts and validity rules with your transport provider's official rates.
FARE_PLANS = {
    "Daily": 40,
    "Weekly": 200,
    "Monthly": 650,
    "Student Monthly": 400,
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                route TEXT NOT NULL,
                pass_type TEXT NOT NULL,
                fare INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL
            )
        """)

@app.route("/")
def index():
    return render_template("index.html", fare_plans=FARE_PLANS)

@app.route("/apply", methods=["GET", "POST"])
def apply():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        route = request.form.get("route", "").strip()
        pass_type = request.form.get("pass_type", "").strip()

        if not all([full_name, email, phone, route, pass_type]):
            flash("Please complete every field.", "error")
            return render_template("apply.html", fare_plans=FARE_PLANS)
        if pass_type not in FARE_PLANS:
            abort(400)
        if len(phone) < 7 or len(phone) > 20:
            flash("Enter a valid phone number.", "error")
            return render_template("apply.html", fare_plans=FARE_PLANS)

        reference = "BUS-" + secrets.token_hex(4).upper()
        with get_db() as conn:
            conn.execute("""
                INSERT INTO applications
                (reference, full_name, email, phone, route, pass_type, fare, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?)
            """, (reference, full_name, email, phone, route, pass_type,
                  FARE_PLANS[pass_type], datetime.now().strftime("%Y-%m-%d %H:%M")))
        return render_template("success.html", reference=reference, full_name=full_name,
                               pass_type=pass_type, fare=FARE_PLANS[pass_type])
    return render_template("apply.html", fare_plans=FARE_PLANS)

@app.route("/track", methods=["GET", "POST"])
def track():
    application = None
    if request.method == "POST":
        reference = request.form.get("reference", "").strip().upper()
        with get_db() as conn:
            application = conn.execute(
                "SELECT reference, full_name, route, pass_type, fare, status, created_at "
                "FROM applications WHERE reference = ?", (reference,)
            ).fetchone()
        if not application:
            flash("No application found for that reference. Check it and try again.", "error")
    return render_template("track.html", application=application)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        expected = os.environ.get("ADMIN_PASSWORD")
        password = request.form.get("password", "")
        if not expected:
            flash("Admin access is not configured. Set ADMIN_PASSWORD in environment variables.", "error")
        elif secrets.compare_digest(password, expected):
            session["is_admin"] = True
            return redirect(url_for("admin"))
        else:
            flash("Incorrect password.", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("index"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        reference = request.form.get("reference", "").strip().upper()
        status = request.form.get("status", "")
        if status not in {"Pending", "Approved", "Rejected"}:
            abort(400)
        with get_db() as conn:
            conn.execute("UPDATE applications SET status = ? WHERE reference = ?", (status, reference))
        flash("Application status updated.", "success")
        return redirect(url_for("admin"))
    with get_db() as conn:
        applications = conn.execute("SELECT * FROM applications ORDER BY id DESC").fetchall()
    return render_template("admin.html", applications=applications)

@app.errorhandler(400)
def bad_request(_error):
    return render_template("error.html", message="Invalid request. Please check the form and try again."), 400

init_db()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=int(os.environ.get("PORT", 5000)))
