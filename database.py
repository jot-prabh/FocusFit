import sqlite3
from datetime import date, timedelta

DATABASE = "focusfit.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            age INTEGER DEFAULT 18,
            user_type TEXT DEFAULT 'general',
            screen_purpose TEXT DEFAULT 'mixed',
            fitness_level TEXT DEFAULT 'light'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screen_time (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            minutes INTEGER NOT NULL,
            logged_on TEXT NOT NULL DEFAULT (DATE('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            deadline TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fitness (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exercise TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'completed',
            logged_on TEXT NOT NULL DEFAULT (DATE('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood TEXT NOT NULL,
            note TEXT DEFAULT '',
            logged_on TEXT NOT NULL DEFAULT (DATE('now')),
            UNIQUE(user_id, logged_on),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xp_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            points INTEGER NOT NULL,
            reason TEXT NOT NULL,
            logged_on TEXT NOT NULL DEFAULT (DATE('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS focus_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            minutes INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'completed',
            logged_on TEXT NOT NULL DEFAULT (DATE('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Safe migration for older local databases that do not have checkins.note
    cols = [row[1] for row in cursor.execute("PRAGMA table_info(checkins)").fetchall()]
    if "note" not in cols:
        cursor.execute("ALTER TABLE checkins ADD COLUMN note TEXT DEFAULT ''")

    conn.commit()
    conn.close()


def create_user(name, email, password, age=18, user_type="general", screen_purpose="mixed", fitness_level="light"):
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO users (name, email, password, age, user_type, screen_purpose, fitness_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, email, password, age, user_type, screen_purpose, fitness_level))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user


def get_user_profile(user_id):
    conn = get_db()
    user = conn.execute("""
        SELECT id, name, email, age, user_type, screen_purpose, fitness_level
        FROM users WHERE id = ?
    """, (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def add_screen_time(user_id, minutes):
    conn = get_db()
    conn.execute("INSERT INTO screen_time (user_id, minutes) VALUES (?, ?)", (user_id, minutes))
    conn.commit()
    conn.close()


def get_today_screen_time(user_id):
    conn = get_db()
    row = conn.execute("""
        SELECT SUM(minutes) as total FROM screen_time
        WHERE user_id = ? AND logged_on = DATE('now')
    """, (user_id,)).fetchone()
    conn.close()
    return row["total"] if row["total"] else 0


def get_last_7_days_screen_time(user_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT logged_on, SUM(minutes) as total FROM screen_time
        WHERE user_id = ? AND logged_on >= DATE('now', '-6 days')
        GROUP BY logged_on ORDER BY logged_on ASC
    """, (user_id,)).fetchall()
    conn.close()

    data = {r["logged_on"]: r["total"] for r in rows}
    today = date.today()
    return [
        {"logged_on": (today - timedelta(days=i)).isoformat(), "minutes": data.get((today - timedelta(days=i)).isoformat(), 0)}
        for i in range(6, -1, -1)
    ]


def add_task(user_id, subject, deadline):
    conn = get_db()
    conn.execute("INSERT INTO tasks (user_id, subject, deadline) VALUES (?, ?, ?)", (user_id, subject, deadline))
    conn.commit()
    conn.close()


def get_tasks(user_id):
    conn = get_db()
    conn.execute("""
        UPDATE tasks SET status = 'missed'
        WHERE user_id = ? AND status = 'pending' AND deadline < DATE('now')
    """, (user_id,))
    conn.commit()
    rows = conn.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY deadline ASC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_task(task_id, user_id):
    conn = get_db()
    conn.execute("UPDATE tasks SET status = 'completed' WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    conn.close()


def delete_task(task_id, user_id):
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    conn.close()


def reschedule_task(task_id, user_id, new_deadline):
    conn = get_db()
    conn.execute("UPDATE tasks SET deadline = ?, status = 'pending' WHERE id = ? AND user_id = ?", (new_deadline, task_id, user_id))
    conn.commit()
    conn.close()


def add_fitness(user_id, exercise):
    conn = get_db()
    conn.execute("INSERT INTO fitness (user_id, exercise, status) VALUES (?, ?, 'completed')", (user_id, exercise))
    conn.commit()
    conn.close()


def complete_fitness(fitness_id, user_id):
    conn = get_db()
    conn.execute("UPDATE fitness SET status = 'completed' WHERE id = ? AND user_id = ?", (fitness_id, user_id))
    conn.commit()
    conn.close()


def get_today_fitness(user_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM fitness
        WHERE user_id = ? AND logged_on = DATE('now')
        ORDER BY id DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_checkin(user_id, mood, note=""):
    conn = get_db()
    conn.execute("""
        INSERT INTO checkins (user_id, mood, note, logged_on)
        VALUES (?, ?, ?, DATE('now'))
        ON CONFLICT(user_id, logged_on)
        DO UPDATE SET mood = excluded.mood, note = excluded.note
    """, (user_id, mood, note))
    conn.commit()
    conn.close()


def get_today_checkin(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM checkins WHERE user_id = ? AND logged_on = DATE('now')", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_xp(user_id, points, reason):
    conn = get_db()
    conn.execute("INSERT INTO xp_events (user_id, points, reason) VALUES (?, ?, ?)", (user_id, points, reason))
    conn.commit()
    conn.close()


def get_total_xp(user_id):
    conn = get_db()
    row = conn.execute("SELECT SUM(points) as total FROM xp_events WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row["total"] if row["total"] else 0


def get_level_from_xp(xp):
    if xp >= 500:
        return "Discipline Master"
    if xp >= 250:
        return "Productivity Pro"
    if xp >= 100:
        return "Focus Learner"
    return "Beginner"


def add_focus_session(user_id, minutes):
    conn = get_db()
    conn.execute("INSERT INTO focus_sessions (user_id, minutes, status) VALUES (?, ?, 'completed')", (user_id, minutes))
    conn.commit()
    conn.close()


def get_today_focus_minutes(user_id):
    conn = get_db()
    row = conn.execute("""
        SELECT SUM(minutes) as total FROM focus_sessions
        WHERE user_id = ? AND logged_on = DATE('now')
    """, (user_id,)).fetchone()
    conn.close()
    return row["total"] if row["total"] else 0


def get_weekly_report(user_id):
    conn = get_db()
    screen_total = conn.execute("""
        SELECT SUM(minutes) as total FROM screen_time
        WHERE user_id = ? AND logged_on >= DATE('now', '-6 days')
    """, (user_id,)).fetchone()["total"] or 0

    tasks_done = conn.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id = ? AND status = 'completed'", (user_id,)).fetchone()["total"] or 0
    fitness_done = conn.execute("""
        SELECT COUNT(*) as total FROM fitness
        WHERE user_id = ? AND logged_on >= DATE('now', '-6 days') AND status = 'completed'
    """, (user_id,)).fetchone()["total"] or 0
    focus_minutes = conn.execute("""
        SELECT SUM(minutes) as total FROM focus_sessions
        WHERE user_id = ? AND logged_on >= DATE('now', '-6 days')
    """, (user_id,)).fetchone()["total"] or 0

    conn.close()
    return {
        "avg_screen_minutes": round(screen_total / 7),
        "tasks_completed": tasks_done,
        "fitness_completed": fitness_done,
        "focus_minutes": focus_minutes
    }


def get_profile_stats(user_id):
    conn = get_db()
    user = conn.execute("SELECT name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    total_screen = conn.execute("SELECT SUM(minutes) as total FROM screen_time WHERE user_id = ?", (user_id,)).fetchone()["total"] or 0
    completed_tasks = conn.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id = ? AND status = 'completed'", (user_id,)).fetchone()["total"] or 0
    completed_fitness = conn.execute("SELECT COUNT(*) as total FROM fitness WHERE user_id = ?", (user_id,)).fetchone()["total"] or 0
    conn.close()
    return {
        "name": user["name"] if user else "User",
        "email": user["email"] if user else "",
        "total_screen": total_screen,
        "completed_tasks": completed_tasks,
        "completed_fitness": completed_fitness
    }


def calculate_streak(user_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT DISTINCT logged_on FROM xp_events
        WHERE user_id = ? ORDER BY logged_on DESC
    """, (user_id,)).fetchall()
    conn.close()

    days = {r["logged_on"] for r in rows}
    streak = 0
    today = date.today()
    while (today - timedelta(days=streak)).isoformat() in days:
        streak += 1
    return streak
