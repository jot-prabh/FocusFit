import sqlite3
import os

DATABASE = "focusfit.db"

def get_db():
    """Open a connection to the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row   # lets us access columns by name
    return conn

def init_db():
    """Create all tables if they don't exist yet."""
    conn = get_db()
    cursor = conn.cursor()

    # ── Users table ───────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            email    TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL
        )
    """)

    # ── Screen time table ─────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screen_time (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            minutes    INTEGER NOT NULL,
            logged_on  TEXT    NOT NULL DEFAULT (DATE('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Tasks table ───────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            subject    TEXT    NOT NULL,
            deadline   TEXT    NOT NULL,
            status     TEXT    NOT NULL DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Fitness table ─────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fitness (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            exercise   TEXT    NOT NULL,
            status     TEXT    NOT NULL DEFAULT 'not started',
            logged_on  TEXT    NOT NULL DEFAULT (DATE('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database ready — focusfit.db created.")


# ── User helpers ──────────────────────────────────────────────────────────

def create_user(name, email, password):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False          # email already exists
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return user


# ── Screen time helpers ───────────────────────────────────────────────────

def add_screen_time(user_id, minutes):
    conn = get_db()
    conn.execute(
        "INSERT INTO screen_time (user_id, minutes) VALUES (?, ?)",
        (user_id, minutes)
    )
    conn.commit()
    conn.close()

def get_screen_time_log(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT minutes, logged_on FROM screen_time WHERE user_id = ? ORDER BY id ASC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

from datetime import date

def get_today_screen_time(user_id):
    today = date.today().isoformat()

    conn = get_db()
    result = conn.execute(
        "SELECT SUM(minutes) as total FROM screen_time WHERE user_id = ? AND logged_on = ?",
        (user_id, today)
    ).fetchone()

    conn.close()

    return result["total"] if result["total"] else 0


# ── Task helpers ──────────────────────────────────────────────────────────

def add_task(user_id, subject, deadline):
    conn = get_db()
    conn.execute(
        "INSERT INTO tasks (user_id, subject, deadline) VALUES (?, ?, ?)",
        (user_id, subject, deadline)
    )
    conn.commit()
    conn.close()

def get_tasks(user_id):
    """Return tasks and auto-mark overdue ones as missed."""
    conn = get_db()
    # Auto-mark overdue pending tasks as missed
    conn.execute("""
        UPDATE tasks
        SET status = 'missed'
        WHERE user_id = ? AND status = 'pending' AND deadline < DATE('now')
    """, (user_id,))
    conn.commit()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? ORDER BY deadline ASC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def complete_task(task_id, user_id):
    conn = get_db()
    conn.execute(
        "UPDATE tasks SET status = 'completed' WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )
    conn.commit()
    conn.close()


# ── Fitness helpers ───────────────────────────────────────────────────────

def add_fitness(user_id, exercise):
    conn = get_db()
    conn.execute(
        "INSERT INTO fitness (user_id, exercise) VALUES (?, ?)",
        (user_id, exercise)
    )
    conn.commit()
    conn.close()

def complete_fitness(fitness_id, user_id):
    conn = get_db()
    conn.execute(
        "UPDATE fitness SET status = 'completed' WHERE id = ? AND user_id = ?",
        (fitness_id, user_id)
    )
    conn.commit()
    conn.close()

def get_today_fitness(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM fitness WHERE user_id = ? AND logged_on = DATE('now') ORDER BY id DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
def delete_task(task_id, user_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )
    conn.commit()
    conn.close()


def reschedule_task(task_id, user_id, new_deadline):
    conn = get_db()
    conn.execute(
        "UPDATE tasks SET deadline = ?, status = 'pending' WHERE id = ? AND user_id = ?",
        (new_deadline, task_id, user_id)
    )
    conn.commit()
    conn.close()

from datetime import date, timedelta

def get_last_7_days_screen_time(user_id):
    conn = get_db()

    rows = conn.execute("""
        SELECT logged_on, SUM(minutes) as total
        FROM screen_time
        WHERE user_id = ?
          AND logged_on >= DATE('now', '-6 days')
        GROUP BY logged_on
        ORDER BY logged_on ASC
    """, (user_id,)).fetchall()

    conn.close()

    data = {r["logged_on"]: r["total"] for r in rows}

    result = []
    today = date.today()

    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.isoformat()
        result.append({
            "logged_on": d_str,
            "minutes": data.get(d_str, 0)
        })

    return result


def get_profile_stats(user_id):
    conn = get_db()

    user = conn.execute(
        "SELECT id, name, email FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    total_screen = conn.execute(
        "SELECT SUM(minutes) as total FROM screen_time WHERE user_id = ?",
        (user_id,)
    ).fetchone()["total"] or 0

    completed_tasks = conn.execute(
        "SELECT COUNT(*) as total FROM tasks WHERE user_id = ? AND status = 'completed'",
        (user_id,)
    ).fetchone()["total"]

    total_tasks = conn.execute(
        "SELECT COUNT(*) as total FROM tasks WHERE user_id = ?",
        (user_id,)
    ).fetchone()["total"]

    completed_fitness = conn.execute(
        "SELECT COUNT(*) as total FROM fitness WHERE user_id = ? AND status = 'completed'",
        (user_id,)
    ).fetchone()["total"]

    conn.close()

    return {
        "name": user["name"],
        "email": user["email"],
        "total_screen": total_screen,
        "completed_tasks": completed_tasks,
        "total_tasks": total_tasks,
        "completed_fitness": completed_fitness
    }


def calculate_streak(user_id):
    conn = get_db()

    rows = conn.execute("""
        SELECT DISTINCT logged_on
        FROM fitness
        WHERE user_id = ? AND status = 'completed'
        ORDER BY logged_on DESC
    """, (user_id,)).fetchall()

    fitness_days = {r["logged_on"] for r in rows}

    task_rows = conn.execute("""
        SELECT DISTINCT deadline
        FROM tasks
        WHERE user_id = ? AND status = 'completed'
        ORDER BY deadline DESC
    """, (user_id,)).fetchall()

    task_days = {r["deadline"] for r in task_rows}

    conn.close()

    streak = 0
    today = date.today()

    for i in range(0, 365):
        d = today - timedelta(days=i)
        d_str = d.isoformat()

        if d_str in fitness_days and d_str in task_days:
            streak += 1
        else:
            if i == 0:
                continue
            break

    return streak
