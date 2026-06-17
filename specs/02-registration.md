# Step 2 — User Registration

## Goal

Wire up the registration form so that a new user can create an account, get saved to the database, and land on their dashboard.

---

## What already exists

| File | What's there |
|---|---|
| `templates/register.html` | The form (name, email, password) — already POSTs to `/register` |
| `database/db.py` | `get_db()`, `generate_password_hash` already imported |
| `app.py` | A `GET /register` route that renders the form |

You are only adding the `POST /register` handler and a helper function in `db.py`.

---

## Acceptance criteria

- Submitting the form with valid data creates a row in the `users` table and redirects to `/dashboard`.
- The stored `password_hash` is **never** the plain-text password.
- Submitting a duplicate email re-renders the form with the message **"An account with that email already exists."**
- Leaving any field blank re-renders the form with the message **"All fields are required."**
- A password shorter than 8 characters re-renders the form with **"Password must be at least 8 characters."**
- After a successful registration the user is logged in automatically (their `id` is stored in the session).

---

## Implementation plan

### 1 — Add a `create_user` helper in `database/db.py`

```python
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
```

Also add a lookup helper — you'll need it for login in Step 3:

```python
def get_user_by_email(email):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return user
```

### 2 — Configure Flask sessions in `app.py`

Flask sessions require a secret key. Add it right after `app = Flask(__name__)`:

```python
app.secret_key = "change-me-in-production"
```

Import what you'll need at the top of `app.py`:

```python
from flask import Flask, render_template, request, redirect, url_for, session
from database.db import init_db, seed_db, create_user, get_user_by_email
```

### 3 — Replace the GET-only `/register` route with a GET + POST handler

```python
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    # --- POST path ---
    name     = request.form.get("name",     "").strip()
    email    = request.form.get("email",    "").strip().lower()
    password = request.form.get("password", "").strip()

    # Validate
    if not name or not email or not password:
        return render_template("register.html", error="All fields are required.")

    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.")

    if get_user_by_email(email):
        return render_template("register.html", error="An account with that email already exists.")

    # Create user and log them in
    user = create_user(name, email, password)
    session["user_id"] = user["id"]
    return redirect(url_for("dashboard"))
```

### 4 — Add a placeholder `/dashboard` route

You will build the real dashboard in Step 5. For now, add a stub so the redirect works:

```python
@app.route("/dashboard")
def dashboard():
    return "Dashboard — coming in Step 5"
```

---

## Verify it works

1. Run the app: `flask run --port 5001`
2. Go to `http://localhost:5001/register`
3. Fill in a name, email, and password (≥ 8 chars) → should redirect to `/dashboard`
4. Open a new tab and try the same email again → should see the duplicate-email error
5. Submit with an empty field → should see the required-fields error
6. Check the database: `sqlite3 expense_tracker.db "SELECT id, name, email FROM users;"`

---

## Key concepts

| Concept | Why it matters here |
|---|---|
| `werkzeug.security.generate_password_hash` | Stores a one-way bcrypt hash — never the plain password |
| `flask.session` | A signed cookie that keeps the user logged in across requests |
| `request.form.get(...)` | Safely reads a POST field; returns `None` if missing |
| `redirect(url_for(...))` | Sends the browser to a new URL after a successful form submission (Post/Redirect/Get pattern) |
