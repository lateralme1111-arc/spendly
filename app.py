from datetime import date, datetime

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash

from database.db import (
    init_db, seed_db, create_user,
    get_user_by_id, get_user_by_email,
    get_expenses_by_user, get_spending_by_category,
    update_user_name, update_user_password,
    get_expense_count, get_category_count,
)

app = Flask(__name__)
app.secret_key = "change-me-in-production"

with app.app_context():
    init_db()


@app.cli.command("seed")
def seed_command():
    seed_db()
    print("Database seeded.")


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    if "user_id" in session:
        return redirect(url_for("profile"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if "user_id" in session:
            return redirect(url_for("dashboard"))
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


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    email    = request.form.get("email",    "").strip().lower()
    password = request.form.get("password", "").strip()

    if not email or not password:
        return render_template("login.html", error="Email and password are required.")

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.")

    session["user_id"] = user["id"]
    return redirect(url_for("profile"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user     = get_user_by_id(session["user_id"])
    expenses = get_expenses_by_user(session["user_id"])
    by_cat   = get_spending_by_category(session["user_id"])

    total      = sum(e["amount"] for e in expenses)
    this_month = sum(
        e["amount"] for e in expenses
        if e["date"].startswith(date.today().strftime("%Y-%m"))
    )
    max_cat = max((r["total"] for r in by_cat), default=1)

    return render_template(
        "dashboard.html",
        user=user,
        expenses=expenses,
        by_cat=by_cat,
        total=total,
        this_month=this_month,
        max_cat=max_cat,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


def _format_joined(created_at_str):
    return datetime.strptime(created_at_str[:19], "%Y-%m-%d %H:%M:%S").strftime("%B %Y")


def _profile_ctx(user_id):
    user     = get_user_by_id(user_id)
    expenses = get_expenses_by_user(user_id)
    by_cat   = get_spending_by_category(user_id)
    total      = sum(e["amount"] for e in expenses)
    this_month = sum(
        e["amount"] for e in expenses
        if e["date"].startswith(date.today().strftime("%Y-%m"))
    )
    return dict(
        user=user,
        joined=_format_joined(user["created_at"]),
        expenses=expenses,
        by_cat=by_cat,
        total=total,
        this_month=this_month,
        max_cat=max((r["total"] for r in by_cat), default=1),
    )


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template("profile.html", **_profile_ctx(user_id),
                                   name_error="Name cannot be empty.")
        update_user_name(user_id, name)
        return redirect(url_for("profile", updated="name"))

    return render_template("profile.html", **_profile_ctx(user_id))


@app.route("/profile/password", methods=["POST"])
def profile_password():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id    = session["user_id"]
    user       = get_user_by_id(user_id)
    current_pw = request.form.get("current_password", "")
    new_pw     = request.form.get("new_password", "")
    confirm_pw = request.form.get("confirm_password", "")

    def rerender(error):
        return render_template("profile.html", **_profile_ctx(user_id), pw_error=error)

    if not check_password_hash(user["password_hash"], current_pw):
        return rerender("Current password is incorrect.")
    if len(new_pw) < 8:
        return rerender("New password must be at least 8 characters.")
    if new_pw != confirm_pw:
        return rerender("Passwords do not match.")
    if check_password_hash(user["password_hash"], new_pw):
        return rerender("New password must differ from your current password.")

    update_user_password(user_id, new_pw)
    return redirect(url_for("profile", updated="password"))


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
