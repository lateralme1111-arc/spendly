import os
import sqlite3

from werkzeug.security import generate_password_hash

def get_db():
    db_path = os.environ.get(
        "DATABASE",
        os.path.join(os.path.dirname(__file__), '..', 'expense_tracker.db'),
    )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name       TEXT    NOT NULL,
            color      TEXT    NOT NULL DEFAULT '#888888',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            amount      REAL    NOT NULL CHECK(amount > 0),
            description TEXT,
            date        DATE    NOT NULL,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def user_exists(email: str) -> bool:
    db = get_db()
    row = db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
    return row is not None


def create_user(name: str, email: str, password_hash: str) -> int:
    db = get_db()
    cursor = db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    db.commit()
    return cursor.lastrowid


def seed_db():
    conn = get_db()

    existing = conn.execute("SELECT COUNT(*) FROM users WHERE email = 'alice@example.com'").fetchone()[0]
    if existing:
        conn.close()
        return

    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Alice Demo", "alice@example.com", generate_password_hash("password123")),
    )
    user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    categories = [
        ("Food", "#e74c3c"),
        ("Transport", "#3498db"),
        ("Entertainment", "#9b59b6"),
    ]
    for name, color in categories:
        conn.execute(
            "INSERT INTO categories (user_id, name, color) VALUES (?, ?, ?)",
            (user_id, name, color),
        )

    food_id, transport_id, entertainment_id = [
        conn.execute("SELECT id FROM categories WHERE user_id = ? AND name = ?", (user_id, name)).fetchone()[0]
        for name, _ in categories
    ]

    sample_expenses = [
        (user_id, food_id,          12.50, "Lunch at café",        "2026-06-01"),
        (user_id, food_id,           8.75, "Groceries",            "2026-06-03"),
        (user_id, transport_id,      3.20, "Bus fare",             "2026-06-04"),
        (user_id, transport_id,     45.00, "Uber to airport",      "2026-06-07"),
        (user_id, entertainment_id, 15.99, "Netflix subscription", "2026-06-10"),
        (user_id, entertainment_id, 22.00, "Cinema tickets",       "2026-06-12"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, category_id, amount, description, date) VALUES (?, ?, ?, ?, ?)",
        sample_expenses,
    )

    conn.commit()
    conn.close()
