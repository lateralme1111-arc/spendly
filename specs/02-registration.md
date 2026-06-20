# Step 2 — User Registration

## Goal

Wire up the registration form so a new user can submit their name, email, and password, have the password hashed, and get stored in the `users` table. On success, redirect to `/login`. On failure, re-render the form with a clear error message.

---

## Scope

This step touches **three files only**:

| File | Change |
|---|---|
| `database/db.py` | Add `user_exists(email)` and `create_user(name, email, password_hash)` |
| `app.py` | Add `POST /register` handler |
| `tests/test_registration.py` | New test file (create it) |

**Do not touch:** templates, CSS, JS, or any other route.

---

## Database helpers (`database/db.py`)

### `user_exists(email: str) -> bool`

```python
def user_exists(email: str) -> bool:
    db = get_db()
    row = db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
    return row is not None
```

### `create_user(name: str, email: str, password_hash: str) -> int`

Returns the new user's `id`.

```python
def create_user(name: str, email: str, password_hash: str) -> int:
    db = get_db()
    cursor = db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    db.commit()
    return cursor.lastrowid
```

---

## Route (`app.py`)

### `POST /register`

Validation order (fail-fast — stop at first error):

1. All three fields (`name`, `email`, `password`) must be non-empty strings after `.strip()`.
2. Email must contain `@` (basic sanity check only — no regex needed).
3. Password must be at least 8 characters.
4. `user_exists(email)` must return `False`.

On any validation failure: re-render `register.html` with `error=<message>` and **HTTP 400**.

On success:
1. Hash password with `werkzeug.security.generate_password_hash`.
2. Call `create_user(name, email, password_hash)`.
3. Redirect to `url_for('login')` with HTTP 302.

```python
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name     = request.form.get("name", "").strip()
    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    if not name or not email or not password:
        return render_template("register.html", error="All fields are required."), 400
    if "@" not in email:
        return render_template("register.html", error="Enter a valid email address."), 400
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters."), 400
    if user_exists(email):
        return render_template("register.html", error="An account with that email already exists."), 400

    password_hash = generate_password_hash(password)
    create_user(name, email, password_hash)
    return redirect(url_for("login"))
```

**Imports to add at top of `app.py`** (only if not already present):
```python
from werkzeug.security import generate_password_hash
from database.db import user_exists, create_user
```

---

## Tests (`tests/test_registration.py`)

Create the `tests/` directory and this file. All tests use Flask's test client.

### Setup

```python
import pytest
from app import app
from database.db import init_db

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
| `test_register_success` | Valid form → 302 redirect to /login |
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
- [ ] Valid POST creates a row in `users` and redirects to `/login`
- [ ] Duplicate email returns 400 with an error message visible in the response body
- [ ] All three fields are required; missing any returns 400
- [ ] Short password (< 8 chars) returns 400
- [ ] Password stored in DB is a hash, never plaintext
- [ ] All 9 tests pass with `pytest tests/test_registration.py`

---

## Constraints

- Use `werkzeug.security.generate_password_hash` — it's already in `requirements.txt` via Werkzeug
- No new pip packages
- No DB logic in `app.py` — only the two helpers from `database/db.py`
- Do not implement session login in this step — that's Step 3
- `generate_password_hash` default method is fine (pbkdf2:sha256) — don't override it
