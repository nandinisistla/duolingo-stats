"""Saves every mistake so patterns can build up over time (the 'history')."""
import os
import sqlite3
from datetime import datetime

DB_PATH = os.getenv("DUO_DB") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "mistakes.db")

# Where a row came from. Only 'screenshot' and 'typed' are real learner data.
REAL_SOURCES = ("screenshot", "typed")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                created_at TEXT NOT NULL,
                question TEXT,
                user_answer TEXT,
                correct_answer TEXT,
                mistake_type TEXT,
                explanation TEXT,
                source TEXT          -- 'screenshot', 'typed' or 'sample'
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS practice (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                created_at TEXT NOT NULL,
                mistake_type TEXT,
                score INTEGER,
                total INTEGER,
                source TEXT
            )"""
        )
        # Added later: the label the AI suggested, so we can see how often users had to fix it.
        cols = [r[1] for r in c.execute("PRAGMA table_info(mistakes)")]
        if "ai_type" not in cols:
            c.execute("ALTER TABLE mistakes ADD COLUMN ai_type TEXT")


def add_mistake(user, m, source, created_at=None, ai_type=None):
    with _conn() as c:
        c.execute(
            """INSERT INTO mistakes
               (user, created_at, question, user_answer, correct_answer, mistake_type, explanation, source, ai_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user,
                created_at or datetime.now().isoformat(timespec="seconds"),
                m.get("question", ""),
                m.get("user_answer", ""),
                m.get("correct_answer", ""),
                m.get("mistake_type", "Other"),
                m.get("explanation", ""),
                source,
                ai_type,
            ),
        )


def get_mistakes(user=None):
    with _conn() as c:
        if user is None:
            rows = c.execute("SELECT * FROM mistakes ORDER BY created_at DESC").fetchall()
        else:
            rows = c.execute("SELECT * FROM mistakes WHERE user = ? ORDER BY created_at DESC", (user,)).fetchall()
    return [dict(r) for r in rows]


def add_practice(user, mistake_type, score, total, source="real", created_at=None):
    with _conn() as c:
        c.execute(
            "INSERT INTO practice (user, created_at, mistake_type, score, total, source) VALUES (?, ?, ?, ?, ?, ?)",
            (user, created_at or datetime.now().isoformat(timespec="seconds"), mistake_type, score, total, source),
        )


def get_practice(user=None):
    with _conn() as c:
        if user is None:
            rows = c.execute("SELECT * FROM practice ORDER BY created_at DESC").fetchall()
        else:
            rows = c.execute("SELECT * FROM practice WHERE user = ? ORDER BY created_at DESC", (user,)).fetchall()
    return [dict(r) for r in rows]


def list_users():
    with _conn() as c:
        rows = c.execute("SELECT DISTINCT user FROM mistakes UNION SELECT DISTINCT user FROM practice").fetchall()
    return sorted(r[0] for r in rows)


def clear_user(user, only_sample=False):
    with _conn() as c:
        if only_sample:
            c.execute("DELETE FROM mistakes WHERE user = ? AND source IN ('sample', 'simulated')", (user,))
            c.execute("DELETE FROM practice WHERE user = ? AND source IN ('sample', 'simulated')", (user,))
        else:
            c.execute("DELETE FROM mistakes WHERE user = ?", (user,))
            c.execute("DELETE FROM practice WHERE user = ?", (user,))


def clear_demo_data():
    """Remove Ramya's demo rows (source='sample'). Real mistakes stay."""
    with _conn() as c:
        c.execute("DELETE FROM mistakes WHERE source = 'sample'")
        c.execute("DELETE FROM practice WHERE source = 'sample'")
