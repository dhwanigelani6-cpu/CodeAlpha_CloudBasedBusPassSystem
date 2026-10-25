import os
import sqlite3
import secrets
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# Render can provide a persistent disk path through DATABASE_PATH.
DB_PATH = os.environ.get("DATABASE_PATH", "bus_passes.db")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-this-admin-password")

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
    # Ensure the parent directory exists when DATABASE_PATH includes one.
    parent = os.path.dirname(os.path.abspath(DB_PATH))
    os.makedirs(parent, exist_ok=True)
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bus_passes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pass_code TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                route TEXT NOT NULL,
                plan TEXT NOT NULL,
                fare INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL
            )
        """)

init_db()

@app.route("/")
def home():
    return render_template("index.html", fare_plans=FARE_PLANS)

@app.route("/apply", methods=["GET", "POST"])
def apply():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        route = request.form.get("route", "").strip()
        plan = request.form.get("plan", "").strip()

        if not all([full_name, email, phone, route, plan]):
            flash("Please fill in all fields.", "error")
            return render_template("apply.html", fare_plans=FARE_PLANS)

        if plan not in FARE_PLANS:
            flash("Please select a valid pass plan.", "error")
            return render_template("apply.html", fare_plans=FARE_PLANS)

        pass_code = "BUS" + secrets.token_hex(4).upper()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            conn.execute("""
                INSERT INTO bus_passes
                (pass_code, full_name, email, phone, route, plan, fare, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?)
            """, (pass_code, full_name, email, phone, route, plan, FARE_PLANS[plan], created_at))

        return redirect(url_for("success", pass_code=pass_code))

    return render_template("apply.html", fare_plans=FARE_PLANS)

@app.route("/success/<pass_code>")
def success(pass_code):
    with get_db() as conn:
        record = conn.execute("SELECT * FROM bus_passes WHERE pass_code = ?", (pass_code,)).fetchone()
    if record is None:
        return render_template("error.html", message="Bus pass application not found."), 404
    return render_template("success.html", record=record)

@app.route("/track", methods=["GET", "POST"])
def track():
    record = None
    searched = False
    if request.method == "POST":
        searched = True
        pass_code = request.form.get("pass_code", "").strip().upper()
        with get_db() as conn:
            record = conn.execute(
                "SELECT * FROM bus_passes WHERE pass_code = ?", (pass_code,)
            ).fetchone()
        if not record:
            flash("No application found for that pass code.", "error")
    return render_template("track.html", record=record, searched=searched)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if secrets.compare_digest(password, ADMIN_PASSWORD):
            session["is_admin"] = True
            return redirect(url_for("admin"))
        flash("Incorrect admin password.", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        pass_id = request.form.get("pass_id", type=int)
        status = request.form.get("status", "")
        if status in {"Pending", "Approved", "Rejected"} and pass_id:
            with get_db() as conn:
                conn.execute("UPDATE bus_passes SET status = ? WHERE id = ?", (status, pass_id))
            flash("Application status updated.", "success")
        return redirect(url_for("admin"))

    with get_db() as conn:
        records = conn.execute("SELECT * FROM bus_passes ORDER BY id DESC").fetchall()
    return render_template("admin.html", records=records)

@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", message="The page you requested was not found."), 404

@app.errorhandler(500)
def server_error(_error):
    return render_template("error.html", message="Something went wrong. Please try again."), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
    
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

