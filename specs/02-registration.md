# Step 2 — User Registration

## Goal

Wire up the registration form so a new user can submit their name, email, and password, have the password hashed, and get stored in the `users` table. On success the user is automatically logged in (session set) and redirected to `/dashboard`. On failure, re-render the form with a clear error message.

---

## Scope

This step touches **three files only**:

| File | Change |
|---|---|
| `database/db.py` | Add `create_user(name, email, password)` and `get_user_by_email(email)` |
| `app.py` | Add `POST /register` handler, configure `secret_key`, import `session` |
| `tests/test_registration.py` | New test file (create it) |

**Do not touch:** templates, CSS, JS, or any other route.

---

## Database helpers (`database/db.py`)

### `create_user(name, email, password)`

Hashes the plaintext password internally and returns the new user row.

```python
def create_user(name, email, password):
    conn = get_db()
    password_hash = generate_password_hash(password)
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user
```

### `get_user_by_email(email)`

Used for duplicate-email check and login (Step 3).

```python
def get_user_by_email(email):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user
```

---

## Route (`app.py`)

### `POST /register`

Validation order (fail-fast — stop at first error):

1. All three fields (`name`, `email`, `password`) must be non-empty after `.strip()`.
2. Email must contain `@`.
3. Password must be at least 8 characters.
4. `get_user_by_email(email)` must return `None`.

On any validation failure: re-render `register.html` with `error=<message>` and **HTTP 400**.

On success:
1. Call `create_user(name, email, password)` — hashing happens inside.
2. Store `user["id"]` in `session["user_id"]`.
3. Redirect to `url_for('dashboard')` with HTTP 302.

```python
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name     = request.form.get("name",     "").strip()
    email    = request.form.get("email",    "").strip().lower()
    password = request.form.get("password", "").strip()

    if not name or not email or not password:
        return render_template("register.html", error="All fields are required."), 400
    if "@" not in email:
        return render_template("register.html", error="Enter a valid email address."), 400
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters."), 400
    if get_user_by_email(email):
        return render_template("register.html", error="An account with that email already exists."), 400

    user = create_user(name, email, password)
    session["user_id"] = user["id"]
    return redirect(url_for("dashboard"))
```

**Imports required in `app.py`:**
```python
from flask import Flask, render_template, request, redirect, url_for, session
from database.db import init_db, seed_db, create_user, get_user_by_email, ...
```

Flask sessions require a secret key — add after `app = Flask(__name__)`:
```python
app.secret_key = "change-me-in-production"
```

---

## Tests (`tests/test_registration.py`)

### Setup

```python
import pytest
from app import app
from database.db import init_db, get_db

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE", str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client
```

### Test cases (all required)

| Test name | What it checks |
|---|---|
| `test_register_get` | GET /register returns 200 |
| `test_register_success` | Valid form → 302 redirect to /dashboard |
| `test_register_duplicate_email` | Second POST with same email → 400 with error message |
| `test_register_missing_name` | Empty name → 400 |
| `test_register_missing_email` | Empty email → 400 |
| `test_register_missing_password` | Empty password → 400 |
| `test_register_invalid_email` | Email without @ → 400 |
| `test_register_short_password` | Password under 8 chars → 400 |
| `test_password_is_hashed` | After registration, `password_hash` in DB does not equal the plaintext password |

---

## Acceptance criteria

- [ ] `GET /register` still returns 200 (no regression)
- [ ] Valid POST creates a row in `users`, sets session, and redirects to `/dashboard`
- [ ] Duplicate email returns 400 with an error message visible in the response body
- [ ] All three fields are required; missing any returns 400
- [ ] Short password (< 8 chars) returns 400
- [ ] Email without `@` returns 400
- [ ] Password stored in DB is a hash, never plaintext
- [ ] All 9 tests pass with `pytest tests/test_registration.py`

---

## Verify it works

1. Run the app: `python app.py`
2. Go to `http://localhost:5001/register`
3. Fill in a name, email, and password (≥ 8 chars) → should redirect to `/dashboard`
4. Try the same email again → should see the duplicate-email error
5. Submit with an empty field → should see the required-fields error
6. Check the DB: `sqlite3 expense_tracker.db "SELECT id, name, email FROM users;"`

---

## Key concepts

| Concept | Why it matters here |
|---|---|
| `werkzeug.security.generate_password_hash` | Stores a one-way hash — never the plain password |
| `flask.session` | A signed cookie that keeps the user logged in across requests |
| `request.form.get(...)` | Safely reads a POST field; returns `None` if missing |
| `redirect(url_for(...))` | Post/Redirect/Get pattern — prevents double-submit on refresh |
