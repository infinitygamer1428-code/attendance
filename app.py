from flask import Flask, render_template, request, redirect, session
import sqlite3
import pandas as pd
import os
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

DB = "database.db"

# ================= ADMIN CREDENTIALS =================
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# ================= DATABASE HELPER =================
def get_db():
    return sqlite3.connect(DB)

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form["role"]
        username = request.form["username"]
        password = request.form["password"]

        # -------- ADMIN LOGIN --------
        if role == "admin":
            if username == ADMIN_USER and password == ADMIN_PASS:
                session.clear()
                session["role"] = "admin"
                return redirect("/admin")
            return render_template("login.html", error="Invalid admin credentials")

        # -------- STUDENT LOGIN --------
        if role == "student":
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "SELECT password FROM users WHERE username=? AND role='student'",
                (username,)
            )
            user = cur.fetchone()
            conn.close()

            if user and check_password_hash(user[0], password):
                session.clear()
                session["role"] = "student"
                session["user"] = username
                return redirect("/student")

            return render_template("login.html", error="Invalid student login")

    return render_template("login.html")

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, 'student')",
                (username, password)
            )
            conn.commit()
            conn.close()
            return redirect("/")
        except:
            return render_template("register.html", error="Username already exists")

    return render_template("register.html")

# ================= ADMIN DASHBOARD =================
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/")
    return render_template("admin_dashboard.html")

# ================= START CAMERA =================
@app.route("/start_camera")
def start_camera():
    if session.get("role") != "admin":
        return redirect("/")
    os.system("python attendance.py")
    return redirect("/admin")

# ================= VIEW & EDIT ATTENDANCE =================
@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    if session.get("role") != "admin":
        return redirect("/")

    today = date.today().isoformat()

    if not os.path.exists("attendance.csv"):
        df = pd.DataFrame(columns=["Name", "Date", "Time"])
        df.to_csv("attendance.csv", index=False)

    if request.method == "POST":
        names = request.form.getlist("name")
        times = request.form.getlist("time")
        deletes = request.form.getlist("delete")

        new_rows = []
        for i in range(len(names)):
            if str(i) not in deletes and names[i].strip() != "":
                new_rows.append([names[i].strip().upper(), today, times[i]])

        df = pd.DataFrame(new_rows, columns=["Name", "Date", "Time"])
        df.to_csv("attendance.csv", index=False)
        df.to_excel("attendance.xlsx", index=False)

    df = pd.read_csv("attendance.csv")

    return render_template(
        "attendance_list.html",
        records=df.to_dict(orient="records"),
        today=today
    )

# ================= STUDENT VIEW =================
@app.route("/student")
def student():
    if session.get("role") != "student":
        return redirect("/")

    if not os.path.exists("attendance.csv"):
        return "attendance.csv not found"

    df = pd.read_csv("attendance.csv")

    # 🔥 NAME NORMALIZATION (FIX)
    login_name = session["user"].strip().split()[0].upper()

    student_df = df[df["Name"] == login_name]

    total_days = df["Date"].nunique()
    present_days = student_df["Date"].nunique()

    percentage = 0
    if total_days > 0:
        percentage = round((present_days / total_days) * 100, 2)

    return render_template(
        "student_attendance.html",
        records=student_df.to_dict(orient="records"),
        name=session["user"],
        percentage=percentage
    )

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
