from datetime import date

from flask import Flask, render_template, request, redirect, url_for, session

from database.db import (init_db, seed_db, create_user, get_user_by_id,
                          get_user_by_email, get_expenses_by_user,
                          get_spending_by_category)

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
    return render_template("landing.html")


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


@app.route("/login")
def login():
    return render_template("login.html")


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
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


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
