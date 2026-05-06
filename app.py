from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
import sqlite3
from database.db import init_db, seed_db, create_user, verify_user
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
    insert_expense,
)
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

# Initialize database on startup
with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Redirect logged‑in users to home
    if session.get('user_id'):
        return redirect(url_for('landing'))
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        # Ensure tables exist (re‑initialize if DB missing)
        init_db()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        if not all([name, email, password, confirm_password]):
            flash("All fields are required.", "error")
            return render_template("register.html")
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")
        try:
            user_id = create_user(name, email, password)
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "error")
            return render_template("register.html")
    else:
        abort(405)


@app.route("/login", methods=["GET", "POST"])
def login():
    # Redirect logged‑in users to home
    if session.get('user_id'):
        return redirect(url_for('landing'))
    if request.method == "GET":
        return render_template("login.html")
    # POST handling
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    user = verify_user(email, password)
    if not user:
        flash("Invalid email or password.", "error")
        return render_template("login.html")
    # successful login
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    flash("Logged in successfully.", "success")
    return redirect(url_for("landing"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("landing"))




@app.route("/profile")
def profile():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    # Date filter handling
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    # Validate dates
    validated_from = None
    validated_to = None

    try:
        if date_from:
            datetime.strptime(date_from, '%Y-%m-%d')
            validated_from = date_from
        if date_to:
            datetime.strptime(date_to, '%Y-%m-%d')
            validated_to = date_to

        # Check date order
        if validated_from and validated_to and validated_from > validated_to:
            flash("Start date must be before end date.", "error")
            validated_from = None
            validated_to = None
    except ValueError:
        # Invalid date format - silently ignore and show unfiltered
        validated_from = None
        validated_to = None

    # Get user data
    user = get_user_by_id(session['user_id'])
    if user is None:
        session.clear()
        return redirect(url_for('login'))

    # Preset date calculations
    today = datetime.today().date()
    # This month
    this_month_start = today.replace(day=1)
    this_month_end = today
    # Last 3 months
    three_months_ago = this_month_start - timedelta(days=90)
    # Last 6 months
    six_months_ago = this_month_start - timedelta(days=180)

    # Get filtered data
    summary_stats = get_summary_stats(session['user_id'], validated_from, validated_to)
    transactions = get_recent_transactions(session['user_id'], 10, validated_from, validated_to)
    category_breakdown = get_category_breakdown(session['user_id'], validated_from, validated_to)

    return render_template('profile.html',
                           user=user,
                           summary_stats=summary_stats,
                           transactions=transactions,
                           category_breakdown=category_breakdown,
                           date_from=validated_from,
                           date_to=validated_to,
                           preset_this_month={'from': this_month_start.isoformat(), 'to': this_month_end.isoformat()},
                           preset_3_months={'from': three_months_ago.isoformat(), 'to': today.isoformat()},
                           preset_6_months={'from': six_months_ago.isoformat(), 'to': today.isoformat()})


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get('user_id'):
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("add_expense.html")

    elif request.method == "POST":
        # Get form data
        amount_str = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date_str = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        # Fixed categories
        valid_categories = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]

        errors = []

        # Validate amount
        try:
            amount = float(amount_str)
            if amount <= 0:
                errors.append("Amount must be greater than 0.")
        except ValueError:
            errors.append("Amount must be a valid number.")

        # Validate category
        if category not in valid_categories:
            errors.append("Please select a valid category.")

        # Validate date
        try:
            from datetime import datetime
            datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            errors.append("Date must be a valid date in YYYY-MM-DD format.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("add_expense.html",
                                   amount=amount_str,
                                   category=category,
                                   date=date_str,
                                   description=description)

        # Insert the expense
        try:
            expense_id = insert_expense(session["user_id"], amount, category, date_str, description)
            flash("Expense added successfully!", "success")
            return redirect(url_for("profile"))
        except Exception as e:
            flash(f"Failed to add expense: {str(e)}", "error")
            return render_template("add_expense.html",
                                   amount=amount_str,
                                   category=category,
                                   date=date_str,
                                   description=description)


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
