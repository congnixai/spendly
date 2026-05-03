import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

# Path to the SQLite database file in the project root
_DB_PATH = Path(__file__).resolve().parents[1] / "spendly.db"


def get_db():
    """Return a SQLite connection with dictionary‑like row access and FK enforcement."""
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the required tables if they do not already exist."""
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def _demo_user_exists(conn):
    cur = conn.execute("SELECT 1 FROM users LIMIT 1")
    return cur.fetchone() is not None


def seed_db():
    """Insert a demo user and a set of sample expenses if the DB is empty."""
    conn = get_db()
    try:
        if _demo_user_exists(conn):
            return  # Data already seeded

        # Insert demo user
        password_hash = generate_password_hash("demo123")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", password_hash),
        )
        user_id = cur.lastrowid

        # Sample expense data
        from datetime import date, timedelta
        today = date.today()
        categories = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]
        expenses = []
        for i in range(8):
            expense_date = (today - timedelta(days=i)).isoformat()
            expenses.append(
                (
                    user_id,
                    round(5 + i * 3.75, 2),  # varied amount
                    categories[i % len(categories)],
                    expense_date,
                    f"Sample expense {i+1}",
                )
            )
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses,
        )
        conn.commit()
    finally:
        conn.close()


def create_user(name, email, password):
    """Create a new user with hashed password and return their ID.
    Raises sqlite3.IntegrityError if email already exists.
    """
    conn = get_db()
    try:
        hashed_password = generate_password_hash(password)
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, hashed_password)
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise
    finally:
        conn.close()