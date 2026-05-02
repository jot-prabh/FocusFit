from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import (
    init_db, create_user, get_user_by_email,
    add_screen_time, get_screen_time_log, get_today_screen_time,
    add_task, get_tasks, complete_task, delete_task, reschedule_task,
    add_fitness, complete_fitness, get_today_fitness,
    get_last_7_days_screen_time,get_profile_stats,calculate_streak
)

app = Flask(__name__)
app.secret_key = "focusfit_secret_2024"

init_db()

def current_user_id():
    return session.get("user_id")

# ── Pages ──────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name     = request.form["name"].strip()
        email    = request.form["email"].strip().lower()
        password = request.form["password"]
        if not name or not email or not password:
            return render_template("signup.html", error="Please fill in all fields.")
        if len(password) < 6:
            return render_template("signup.html", error="Password must be at least 6 characters")
        hashed_password = generate_password_hash(password)
        if not create_user(name, email, hashed_password):
            return render_template("signup.html", error="Email already registered.")
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email    = request.form["email"].strip().lower()
        password = request.form["password"]
        user     = get_user_by_email(email)
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"]    = user["name"]
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Wrong email or password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", name=session["name"])

# ── Screen Time API ────────────────────────────────────────────────────────

@app.route("/api/screen-time", methods=["GET"])
def api_get_screen_time():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        uid = current_user_id()
        log = get_last_7_days_screen_time(uid)
        today = get_today_screen_time(uid)
        return jsonify({"log": log, "today": today})
    except Exception as e:
        print("ERROR in api_get_screen_time:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/screen-time", methods=["POST"])
def api_add_screen_time():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        uid = current_user_id()
        minutes = int(request.json.get("minutes", 0))

        if minutes <= 0:
            return jsonify({"error": "Enter more than 0 minutes"}), 400

        add_screen_time(uid, minutes)

        log = get_last_7_days_screen_time(uid)
        today = get_today_screen_time(uid)

        return jsonify({"log": log, "today": today})
    except Exception as e:
        print("ERROR in api_add_screen_time:", e)
        return jsonify({"error": str(e)}), 500

# ── Tasks API ──────────────────────────────────────────────────────────────

@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        return jsonify({"tasks": get_tasks(current_user_id())})
    except Exception as e:
        print("ERROR in api_get_tasks:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        subject  = request.json.get("subject", "").strip()
        deadline = request.json.get("deadline", "")
        if not subject or not deadline:
            return jsonify({"error": "Missing fields"}), 400
        add_task(current_user_id(), subject, deadline)
        return jsonify({"tasks": get_tasks(current_user_id())})
    except Exception as e:
        print("ERROR in api_add_task:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/tasks/<int:task_id>/complete", methods=["POST"])
def api_complete_task(task_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        complete_task(task_id, current_user_id())
        return jsonify({"tasks": get_tasks(current_user_id())})
    except Exception as e:
        print("ERROR in api_complete_task:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/tasks/<int:task_id>/delete", methods=["POST"])
def api_delete_task(task_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        delete_task(task_id, current_user_id())
        return jsonify({"tasks": get_tasks(current_user_id())})
    except Exception as e:
        print("ERROR in api_delete_task:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/tasks/<int:task_id>/reschedule", methods=["POST"])
def api_reschedule_task(task_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        new_deadline = request.json.get("deadline", "")
        if not new_deadline:
            return jsonify({"error": "Deadline missing"}), 400

        reschedule_task(task_id, current_user_id(), new_deadline)
        return jsonify({"tasks": get_tasks(current_user_id())})
    except Exception as e:
        print("ERROR in api_reschedule_task:", e)
        return jsonify({"error": str(e)}), 500
# ── Fitness API ────────────────────────────────────────────────────────────

@app.route("/api/fitness", methods=["GET"])
def api_get_fitness():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        return jsonify({"fitness": get_today_fitness(current_user_id())})
    except Exception as e:
        print("ERROR in api_get_fitness:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/fitness", methods=["POST"])
def api_add_fitness():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        exercise = request.json.get("exercise", "").strip()
        if not exercise:
            return jsonify({"error": "No exercise provided"}), 400
        add_fitness(current_user_id(), exercise)
        return jsonify({"fitness": get_today_fitness(current_user_id())})
    except Exception as e:
        print("ERROR in api_add_fitness:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/fitness/<int:fitness_id>/complete", methods=["POST"])
def api_complete_fitness(fitness_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        complete_fitness(fitness_id, current_user_id())
        return jsonify({"fitness": get_today_fitness(current_user_id())})
    except Exception as e:
        print("ERROR in api_complete_fitness:", e)
        return jsonify({"error": str(e)}), 500

# ── Recommendation API ─────────────────────────────────────────────────────

@app.route("/api/recommendation", methods=["GET"])
def api_recommendation():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        uid     = current_user_id()
        today   = get_today_screen_time(uid)
        tasks   = get_tasks(uid)
        fitness = get_today_fitness(uid)

        pending  = sum(1 for t in tasks if t["status"] == "pending")
        missed   = sum(1 for t in tasks if t["status"] == "missed")
        fit_done = any(f["status"] == "completed" for f in fitness)

        if today > 120:
            msg = "🚨 Over 2 hours of screen time! Take a proper walk now."
        elif today > 90:
            msg = "⚠️ Screen time very high. A 10-minute walk will help!"
        elif today > 60:
            msg = "📵 Screen time getting high. Try a 5-min stretch break!"
        elif missed > 2:
            msg = f"📚 You have {missed} missed tasks! Reschedule and catch up."
        elif pending > 3:
            msg = f"📋 {pending} pending tasks. Focus on the nearest deadline first!"
        elif not fit_done:
            msg = "🏃 No fitness done today. Even a 5-min stretch helps!"
        else:
            msg = "🌿 You're doing great! Keep up the good work today."

        return jsonify({"recommendation": msg})
    except Exception as e:
        print("ERROR in api_recommendation:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/streak", methods=["GET"])
def api_streak():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        streak = calculate_streak(current_user_id())
        return jsonify({"streak": streak})
    except Exception as e:
        print("ERROR in api_streak:", e)
        return jsonify({"error": str(e)}), 500
    
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    stats = get_profile_stats(current_user_id())
    streak = calculate_streak(current_user_id())

    return render_template("profile.html", stats=stats, streak=streak)
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)    