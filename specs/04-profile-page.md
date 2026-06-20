# Step 4 — Profile Page

## Goal

Replace the `/profile` stub with a real page where a logged-in user can view their account info, update their display name, and change their password. The page follows the existing dashboard visual style and uses the CSS variable system already defined in `style.css`.

---

## What already exists

| File | What's there |
|---|---|
| `app.py` | `GET /profile` stub returning a string; `get_user_by_id` already imported |
| `database/db.py` | `get_user_by_id`, `check_password_hash` already available |
| `static/css/style.css` | Full design system: colours, spacing, form inputs, buttons, alert pattern |
| `templates/base.html` | Shared layout, navbar, footer — all pages extend this |
| `templates/dashboard.html` | Reference for `.dash-page` layout and stat card pattern |

You are adding two new routes, four new db helpers, one new template, and one new stylesheet.

---

## Acceptance criteria

- `GET /profile` requires a session — unauthenticated visitors are redirected to `/login`.
- The page displays the user's name, email, and the month + year they joined (e.g. "June 2025").
- The page shows two stats: total expenses logged and total categories.
- A name-update form lets the user change their display name; the new name is reflected in the navbar on the next page load.
- A password-change form validates current password before allowing a change.
- Submitting the name form with an empty or whitespace-only value re-renders the page with **"Name cannot be empty."**
- Submitting the password form with the wrong current password re-renders with **"Current password is incorrect."**
- Submitting the password form with mismatched new/confirm passwords re-renders with **"Passwords do not match."**
- Submitting the password form with a new password shorter than 8 characters re-renders with **"New password must be at least 8 characters."**
- Submitting the password form with a new password identical to the current one re-renders with **"New password must differ from your current password."**
- On success, both forms use POST → redirect → GET (PRG pattern) with `?updated=name` or `?updated=password` to show a one-time success banner.

---

## Implementation plan

### 1 — Add four helpers to `database/db.py`

```python
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
```

### 2 — Update the import in `app.py`

Add the four new helpers:

```python
from database.db import (
    init_db, seed_db, create_user,
    get_user_by_id, get_user_by_email,
    get_expenses_by_user, get_spending_by_category,
    update_user_name, update_user_password,
    get_expense_count, get_category_count,
)
```

### 3 — Replace the `/profile` stub and add `/profile/password`

```python
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template(
                "profile.html", user=user,
                expense_count=get_expense_count(session["user_id"]),
                category_count=get_category_count(session["user_id"]),
                name_error="Name cannot be empty.",
            )
        update_user_name(session["user_id"], name)
        return redirect(url_for("profile", updated="name"))

    return render_template(
        "profile.html",
        user=user,
        expense_count=get_expense_count(session["user_id"]),
        category_count=get_category_count(session["user_id"]),
    )


@app.route("/profile/password", methods=["POST"])
def profile_password():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user            = get_user_by_id(session["user_id"])
    current_pw      = request.form.get("current_password", "")
    new_pw          = request.form.get("new_password", "")
    confirm_pw      = request.form.get("confirm_password", "")

    def rerender(error):
        return render_template(
            "profile.html", user=user,
            expense_count=get_expense_count(session["user_id"]),
            category_count=get_category_count(session["user_id"]),
            pw_error=error,
        )

    if not check_password_hash(user["password_hash"], current_pw):
        return rerender("Current password is incorrect.")
    if len(new_pw) < 8:
        return rerender("New password must be at least 8 characters.")
    if new_pw != confirm_pw:
        return rerender("Passwords do not match.")
    if check_password_hash(user["password_hash"], new_pw):
        return rerender("New password must differ from your current password.")

    update_user_password(session["user_id"], new_pw)
    return redirect(url_for("profile", updated="password"))
```

### 4 — Create `templates/profile.html`

```html
{% extends "base.html" %}
{% block title %}Profile — Spendly{% endblock %}

{% block head %}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/profile.css') }}">
{% endblock %}

{% block content %}
<div class="profile-page">

  <div class="profile-header">
    <div class="profile-avatar">{{ user.name[0]|upper }}</div>
    <div class="profile-meta">
      <h1 class="profile-name">{{ user.name }}</h1>
      <p class="profile-email">{{ user.email }}</p>
      <p class="profile-since">Member since {{ user.created_at[:7] }}</p>
    </div>
  </div>

  <div class="profile-stats">
    <div class="profile-stat">
      <span class="profile-stat-value">{{ expense_count }}</span>
      <span class="profile-stat-label">Expenses logged</span>
    </div>
    <div class="profile-stat">
      <span class="profile-stat-value">{{ category_count }}</span>
      <span class="profile-stat-label">Categories</span>
    </div>
  </div>

  {% if request.args.get('updated') == 'name' %}
    <div class="profile-success">Name updated successfully.</div>
  {% elif request.args.get('updated') == 'password' %}
    <div class="profile-success">Password updated successfully.</div>
  {% endif %}

  <div class="profile-section">
    <h2 class="profile-section-title">Display name</h2>
    {% if name_error %}
      <div class="alert">{{ name_error }}</div>
    {% endif %}
    <form method="POST" action="{{ url_for('profile') }}">
      <div class="form-group">
        <label for="name">Name</label>
        <input id="name" class="form-input" type="text" name="name"
               value="{{ user.name }}" required maxlength="80">
      </div>
      <button class="btn-submit" type="submit">Save changes</button>
    </form>
  </div>

  <div class="profile-section">
    <h2 class="profile-section-title">Change password</h2>
    {% if pw_error %}
      <div class="alert">{{ pw_error }}</div>
    {% endif %}
    <form method="POST" action="{{ url_for('profile_password') }}">
      <div class="form-group">
        <label for="current_password">Current password</label>
        <input id="current_password" class="form-input" type="password"
               name="current_password" required>
      </div>
      <div class="form-group">
        <label for="new_password">New password</label>
        <input id="new_password" class="form-input" type="password"
               name="new_password" required minlength="8">
      </div>
      <div class="form-group">
        <label for="confirm_password">Confirm new password</label>
        <input id="confirm_password" class="form-input" type="password"
               name="confirm_password" required>
      </div>
      <button class="btn-submit" type="submit">Update password</button>
    </form>
  </div>

</div>
{% endblock %}
```

### 5 — Create `static/css/profile.css`

```css
.profile-page {
  max-width: 680px;
  margin: 0 auto;
  padding: 48px 24px 80px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ── Header: avatar + name block ── */
.profile-header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.profile-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  font-family: 'DM Serif Display', serif;
  font-size: 1.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.profile-name {
  font-family: 'DM Serif Display', serif;
  font-size: 1.4rem;
  color: var(--ink);
  margin: 0 0 2px;
}

.profile-email {
  font-size: 0.9rem;
  color: var(--ink-muted);
  margin: 0 0 2px;
}

.profile-since {
  font-size: 0.8rem;
  color: var(--ink-faint);
  margin: 0;
}

/* ── Stats row ── */
.profile-stats {
  display: flex;
  gap: 16px;
}

.profile-stat {
  flex: 1;
  background: var(--paper-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.profile-stat-value {
  font-family: 'DM Serif Display', serif;
  font-size: 2rem;
  color: var(--ink);
  line-height: 1;
}

.profile-stat-label {
  font-size: 0.8rem;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* ── Success banner ── */
.profile-success {
  background: var(--accent-light);
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  font-size: 0.9rem;
}

/* ── Section cards ── */
.profile-section {
  background: var(--paper-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.profile-section-title {
  font-family: 'DM Serif Display', serif;
  font-size: 1.15rem;
  color: var(--ink);
  margin: 0;
}

/* ── Responsive ── */
@media (max-width: 600px) {
  .profile-page {
    padding: 32px 16px 60px;
  }

  .profile-section {
    padding: 20px;
  }
}
```

---

## Tests to write

Create `tests/test_profile.py`. Cover:

| Test | Expected outcome |
|---|---|
| `GET /profile` while logged out | 302 redirect to `/login` |
| `GET /profile` while logged in | 200, user name and email present in response |
| `POST /profile` with valid name | 302 redirect to `/profile?updated=name` |
| `POST /profile` with empty name | 200, error message "Name cannot be empty." |
| `POST /profile/password` with correct passwords | 302 redirect to `/profile?updated=password` |
| `POST /profile/password` with wrong current password | 200, "Current password is incorrect." |
| `POST /profile/password` with mismatched new passwords | 200, "Passwords do not match." |
| `POST /profile/password` with new password < 8 chars | 200, "New password must be at least 8 characters." |
| `POST /profile/password` with same old/new password | 200, "New password must differ from your current password." |
| `POST /profile/password` while logged out | 302 redirect to `/login` |

---

## Verify it works

1. Run the app: `python app.py`
2. Log in at `http://localhost:5001/login` (use the seeded user `alice@example.com` / `password123`).
3. Navigate to `http://localhost:5001/profile` — confirm name, email, member-since, and stats are shown.
4. Update the display name → should redirect back and show the green "Name updated successfully." banner.
5. Try submitting the name form blank → should show the inline error.
6. Fill in the password form with the wrong current password → should show the error.
7. Fill in mismatched new/confirm passwords → should show the error.
8. Change the password successfully → banner appears; log out, log in with the new password to confirm it works.

---

## Key concepts

| Concept | Why it matters here |
|---|---|
| PRG (Post/Redirect/Get) | Prevents duplicate form submission on browser refresh; success state lives in the query string |
| `?updated=name` query param | A lightweight one-time success flag — no server-side flash session needed |
| `check_password_hash` before update | Verifies the user knows the current password before allowing a change — prevents account takeover if a session is left open |
| Separate `/profile/password` route | Keeps the two forms' validation logic independent and avoids `if "name" in form` branching |
| Avatar from initials | No file upload complexity; just `user.name[0]` rendered in a styled circle |
