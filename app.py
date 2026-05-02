from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from database import (
    init_db, create_user, get_user_by_email, get_user_profile,
    add_screen_time, get_today_screen_time, get_last_7_days_screen_time,
    add_task, get_tasks, complete_task, delete_task, reschedule_task,
    add_fitness, complete_fitness, get_today_fitness,
    save_checkin, get_today_checkin,
    add_xp, get_total_xp, get_level_from_xp,
    add_focus_session, get_today_focus_minutes,
    get_weekly_report, get_profile_stats, calculate_streak
)

app = Flask(__name__)
app.secret_key = "focusfit_secret_2024"
init_db()


def current_user_id():
    return session.get("user_id")


def format_time(minutes):
    minutes = int(minutes or 0)
    h = minutes // 60
    m = minutes % 60
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


def get_personalized_limits(profile):
    user_type = profile.get("user_type", "general")
    purpose = profile.get("screen_purpose", "mixed")

    safe, high, very_high = 120, 240, 360

    if user_type == "student":
        safe, high, very_high = 240, 360, 480
    elif user_type == "working":
        safe, high, very_high = 300, 420, 540
    elif user_type == "teen":
        safe, high, very_high = 120, 180, 300
    elif user_type == "older_adult":
        safe, high, very_high = 90, 150, 240

    if purpose in ["study", "work"]:
        safe += 60
        high += 60
        very_high += 60
    elif purpose == "entertainment":
        safe -= 30
        high -= 30
        very_high -= 30

    return max(30, safe), max(60, high), max(90, very_high)


def should_show_focus_timer(profile):
    user_type = profile.get("user_type", "general")
    purpose = profile.get("screen_purpose", "mixed")
    return user_type in ["student", "working", "teen"] and purpose in ["study", "work", "mixed"]


def get_break_action(profile, today_minutes, mood=None):
    user_type = profile.get("user_type", "general")
    fitness_level = profile.get("fitness_level", "light")

    if mood == "tired":
        return "Take a calm 3-minute breathing break and rest your eyes."
    if mood == "distracted":
        return "Do a 5-minute reset: water, stretch, then return to one task."
    if user_type == "older_adult":
        return "Do light neck rolls and a slow 3-minute walk."
    if fitness_level == "active":
        return "Do 20 jumping jacks, 10 squats, and drink water."
    if fitness_level == "medium":
        return "Take a 7-minute walk or do 10 squats."
    if today_minutes >= 240:
        return "Move away from the screen for 5 minutes and stretch your shoulders."
    return "Follow the 20-20-20 rule and do a light shoulder stretch."


def build_recommendation(uid):
    profile = get_user_profile(uid) or {
        "age": 18,
        "user_type": "general",
        "screen_purpose": "mixed",
        "fitness_level": "light"
    }

    today = get_today_screen_time(uid)
    tasks = get_tasks(uid)
    fitness = get_today_fitness(uid)
    checkin = get_today_checkin(uid)
    mood = checkin["mood"] if checkin else None

    safe, high, very_high = get_personalized_limits(profile)
    pending = sum(1 for t in tasks if t["status"] == "pending")
    missed = sum(1 for t in tasks if t["status"] == "missed")
    fitness_done = any(f["status"] == "completed" for f in fitness)
    break_action = get_break_action(profile, today, mood)

    tone_prefix = ""
    if mood == "tired":
        tone_prefix = "You seem tired today, so keep it gentle. "
    elif mood == "distracted":
        tone_prefix = "Feeling distracted is okay — let’s make the next step small. "
    elif mood == "focused":
        tone_prefix = "Great focus energy today. "

    if today >= very_high:
        msg = f"{tone_prefix}You’ve been on screen a lot today. Take a real break now 💙 {break_action}"
    elif today >= high:
        msg = f"{tone_prefix}Your screen time is getting high. Pause for a short reset before continuing. {break_action}"
    elif today >= safe:
        msg = f"{tone_prefix}You crossed your personal screen limit. A small break will help you continue better. {break_action}"
    elif missed > 0:
        msg = f"{tone_prefix}You have {missed} missed task(s). Reschedule them first so your planner feels clear again."
    elif pending >= 2:
        msg = f"{tone_prefix}You still have {pending} tasks left today. Start with the nearest deadline 💪"
    elif not checkin:
        msg = "How are you feeling today? Pick a mood below so I can adjust your recommendation 🙂"
    elif not fitness_done:
        msg = f"{tone_prefix}Let’s move a bit today — even 5 minutes helps 💙 {break_action}"
    else:
        msg = f"{tone_prefix}You’re balanced today: screen time, tasks, and wellness are looking good 🌿"

    return {
        "recommendation": msg,
        "smart_break": break_action,
        "today_minutes": today,
        "profile": profile,
        "mood": mood,
        "show_focus_timer": should_show_focus_timer(profile),
        "limits": {"safe": safe, "high": high, "very_high": very_high}
    }


@app.route("/")
def home():
    return redirect(url_for("dashboard" if "user_id" in session else "login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        age = int(request.form.get("age", 18))
        user_type = request.form.get("user_type", "general")
        screen_purpose = request.form.get("screen_purpose", "mixed")
        fitness_level = request.form.get("fitness_level", "light")

        if not name or not email or not password:
            return render_template("signup.html", error="Please fill in all fields.")
        if len(password) < 6:
            return render_template("signup.html", error="Password must be at least 6 characters.")

        created = create_user(name, email, generate_password_hash(password), age, user_type, screen_purpose, fitness_level)
        if not created:
            return render_template("signup.html", error="Email already registered.")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = get_user_by_email(email)
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
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


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))
    uid = current_user_id()
    return render_template(
        "profile.html",
        stats=get_profile_stats(uid),
        streak=calculate_streak(uid),
        xp=get_total_xp(uid),
        level=get_level_from_xp(get_total_xp(uid)),
        profile_data=get_user_profile(uid)
    )


@app.route("/api/dashboard-summary")
def api_dashboard_summary():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    uid = current_user_id()
    report = get_weekly_report(uid)
    checkin = get_today_checkin(uid)
    focus_today = get_today_focus_minutes(uid)
    return jsonify({
        "xp": get_total_xp(uid),
        "level": get_level_from_xp(get_total_xp(uid)),
        "streak": calculate_streak(uid),
        "weekly_report": report,
        "checkin": checkin,
        "focus_today": focus_today
    })


@app.route("/api/screen-time", methods=["GET"])
def api_get_screen_time():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    uid = current_user_id()
    rec = build_recommendation(uid)
    return jsonify({
        "log": get_last_7_days_screen_time(uid),
        "today": get_today_screen_time(uid),
        "limits": rec["limits"]
    })


@app.route("/api/screen-time", methods=["POST"])
def api_add_screen_time():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    minutes = int(request.json.get("minutes", 0))
    if minutes <= 0:
        return jsonify({"error": "Enter more than 0 minutes"}), 400
    if minutes > 1440:
        return jsonify({"error": "You cannot log more than 24 hours."}), 400
    uid = current_user_id()
    add_screen_time(uid, minutes)
    rec = build_recommendation(uid)
    return jsonify({
        "log": get_last_7_days_screen_time(uid),
        "today": get_today_screen_time(uid),
        "limits": rec["limits"]
    })


@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify({"tasks": get_tasks(current_user_id())})


@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    subject = request.json.get("subject", "").strip()
    deadline = request.json.get("deadline", "")
    if not subject or not deadline:
        return jsonify({"error": "Missing fields"}), 400
    uid = current_user_id()
    add_task(uid, subject, deadline)
    return jsonify({"tasks": get_tasks(uid)})


@app.route("/api/tasks/<int:task_id>/complete", methods=["POST"])
def api_complete_task(task_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    uid = current_user_id()
    complete_task(task_id, uid)
    add_xp(uid, 10, "Task completed")
    return jsonify({"tasks": get_tasks(uid)})


@app.route("/api/tasks/<int:task_id>/delete", methods=["POST"])
def api_delete_task(task_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    uid = current_user_id()
    delete_task(task_id, uid)
    return jsonify({"tasks": get_tasks(uid)})


@app.route("/api/tasks/<int:task_id>/reschedule", methods=["POST"])
def api_reschedule_task(task_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    new_deadline = request.json.get("deadline", "")
    if not new_deadline:
        return jsonify({"error": "Deadline missing"}), 400
    uid = current_user_id()
    reschedule_task(task_id, uid, new_deadline)
    return jsonify({"tasks": get_tasks(uid)})


@app.route("/api/fitness", methods=["GET"])
def api_get_fitness():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify({"fitness": get_today_fitness(current_user_id())})


@app.route("/api/fitness", methods=["POST"])
def api_add_fitness():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    exercise = request.json.get("exercise", "").strip()
    if not exercise:
        return jsonify({"error": "No exercise provided"}), 400
    uid = current_user_id()
    add_fitness(uid, exercise)
    add_xp(uid, 15, "Fitness completed")
    return jsonify({"fitness": get_today_fitness(uid)})


@app.route("/api/fitness/<int:fitness_id>/complete", methods=["POST"])
def api_complete_fitness(fitness_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    uid = current_user_id()
    complete_fitness(fitness_id, uid)
    add_xp(uid, 15, "Fitness completed")
    return jsonify({"fitness": get_today_fitness(uid)})


@app.route("/api/checkin", methods=["GET"])
def api_get_checkin():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify({"checkin": get_today_checkin(current_user_id())})


@app.route("/api/checkin", methods=["POST"])
def api_save_checkin():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    mood = request.json.get("mood", "").strip()
    note = request.json.get("note", "").strip()
    if not mood:
        return jsonify({"error": "Mood is required"}), 400
    uid = current_user_id()
    old = get_today_checkin(uid)
    save_checkin(uid, mood, note)
    if not old:
        add_xp(uid, 5, "Mood check-in")
    return jsonify({"checkin": get_today_checkin(uid)})


@app.route("/api/focus-session", methods=["POST"])
def api_focus_session():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    uid = current_user_id()
    profile = get_user_profile(uid) or {}
    if not should_show_focus_timer(profile):
        return jsonify({"error": "Focus timer is not enabled for this profile."}), 403
    minutes = int(request.json.get("minutes", 25))
    add_focus_session(uid, minutes)
    add_xp(uid, 20, "Study focus session completed")
    return jsonify({"message": "Focus session completed", "focus_today": get_today_focus_minutes(uid)})


@app.route("/api/recommendation")
def api_recommendation():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify(build_recommendation(current_user_id()))


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)