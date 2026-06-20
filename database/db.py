import os
import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'expense_tracker.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
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


def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def get_user_by_email(email):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return user


def get_expenses_by_user(user_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT e.id, e.amount, e.description, e.date,
               COALESCE(c.name,  'Uncategorised') AS category,
               COALESCE(c.color, '#888888')        AS category_color
        FROM   expenses e
        LEFT JOIN categories c ON c.id = e.category_id
        WHERE  e.user_id = ?
        ORDER  BY e.date DESC
    """, (user_id,)).fetchall()
    conn.close()
    return rows


def get_spending_by_category(user_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT COALESCE(c.name,  'Uncategorised') AS name,
               COALESCE(c.color, '#888888')        AS color,
               SUM(e.amount)                       AS total
        FROM   expenses e
        LEFT JOIN categories c ON c.id = e.category_id
        WHERE  e.user_id = ?
        GROUP  BY c.id
        ORDER  BY total DESC
    """, (user_id,)).fetchall()
    conn.close()
    return rows


def create_user(name, email, password):
    conn = get_db()
    password_hash = generate_password_hash(password)
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    conn.commit()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return user


def update_user_name(user_id, name):
    conn = get_db()
    conn.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    conn.commit()
    conn.close()


def update_user_password(user_id, password):
    conn = get_db()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(password), user_id),
    )
    conn.commit()
    conn.close()


def get_expense_count(user_id):
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    conn.close()
    return count


def get_category_count(user_id):
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM categories WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    conn.close()
    return count
