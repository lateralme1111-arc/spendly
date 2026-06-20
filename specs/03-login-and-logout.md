# Step 3 — Login and Logout

## Goal

Wire up the login form so that an existing user can authenticate with their email and password, get their session started, and land on the dashboard. Also implement logout so the session is cleared and the user is returned to the landing page.

---

## What already exists

| File | What's there |
|---|---|
| `templates/login.html` | The form (email, password) — already POSTs to `/login`, shows `{{ error }}` block |
| `database/db.py` | `get_user_by_email(email)` helper, `generate_password_hash` already imported |
| `app.py` | A `GET /login` route that renders the form; `GET /logout` stub returning a string |
| `app.py` | `session["user_id"]` already set after registration — same pattern used here |

You are only adding the `POST /login` handler, implementing `/logout`, and one new db helper.

---

## Acceptance criteria

- Submitting valid credentials sets `session["user_id"]` and redirects to `/dashboard`.
- An unrecognised email re-renders the form with **"Invalid email or password."**
- A correct email but wrong password re-renders the form with **"Invalid email or password."** (same message — do not distinguish which field was wrong).
- Leaving either field blank re-renders the form with **"Email and password are required."**
- `GET /logout` clears the session and redirects to `/` (the landing page).
- After logout, visiting `/dashboard` redirects back to `/login`.

---

## Implementation plan

### 1 — Add `check_password_hash` to the import in `database/db.py`

The file already imports `generate_password_hash`. Extend it:

```python
from werkzeug.security import generate_password_hash, check_password_hash
```

### 2 — Add a `get_user_by_id` helper in `database/db.py`

You will need this in Step 4 (profile page), and it is cleaner to add it now alongside the email lookup:

```python
def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return user
```

### 3 — Update the import in `app.py`

Add `check_password_hash` and the new helper to the db imports:

```python
from database.db import init_db, seed_db, create_user, get_user_by_email, get_user_by_id
```

And import `check_password_hash` at the top:

```python
from werkzeug.security import check_password_hash
```

### 4 — Replace the GET-only `/login` route with a GET + POST handler

```python
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    # --- POST path ---
    email    = request.form.get("email",    "").strip().lower()
    password = request.form.get("password", "").strip()

    if not email or not password:
        return render_template("login.html", error="Email and password are required.")

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.")

    session["user_id"] = user["id"]
    return redirect(url_for("dashboard"))
```

### 5 — Implement `/logout`

Replace the stub with:

```python
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
```

---

## Tests to write

Create `tests/test_login_logout.py`. Cover:

| Test | Expected outcome |
|---|---|
| POST `/login` with valid credentials | 302 redirect to `/dashboard`, `session["user_id"]` is set |
| POST `/login` with wrong password | 200, form re-rendered, error message present |
| POST `/login` with unknown email | 200, form re-rendered, error message present |
| POST `/login` with blank fields | 200, form re-rendered, required-fields error |
| GET `/logout` while logged in | 302 redirect to `/`, session cleared |
| GET `/dashboard` after logout | 302 redirect to `/login` |

---

## Verify it works

1. Run the app: `python app.py`
2. Register a new account at `http://localhost:5001/register` (or use a seeded user).
3. Visit `http://localhost:5001/logout` to clear the session.
4. Go to `http://localhost:5001/login`, enter your credentials → should reach the dashboard.
5. Try the wrong password → should see **"Invalid email or password."**
6. Try a non-existent email → same error message.
7. Visit `http://localhost:5001/logout` → should land on the landing page.
8. Try going to `http://localhost:5001/dashboard` → should redirect to `/login`.

---

## Key concepts

| Concept | Why it matters here |
|---|---|
| `check_password_hash(hash, password)` | Compares a plain-text input against the stored bcrypt hash without ever storing the plain text |
| Single error message for bad email/password | Prevents user enumeration — an attacker cannot tell whether the email exists |
| `session.clear()` | Removes all keys at once; safer than `del session["user_id"]` in case other keys are added later |
| Post/Redirect/Get on success | Prevents a browser "re-submit form?" prompt if the user hits refresh after login |
