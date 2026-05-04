from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
import sqlite3
from database.db import init_db, seed_db, create_user, verify_user
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)

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
    # Hardcoded data for profile page design (Step 4)
    user = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'member_since': '2025-01-15'
    }
    summary_stats = {
        'total_spent': 1250.75,
        'transaction_count': 24,
        'top_category': 'Food'
    }
    transactions = [
        {'date': '2026-04-28', 'description': 'Grocery shopping', 'category': 'Food', 'amount': 85.50},
        {'date': '2026-04-27', 'description': 'Taxi ride', 'category': 'Transport', 'amount': 25.00},
        {'date': '2026-04-26', 'description': 'Electricity bill', 'category': 'Bills', 'amount': 120.00},
    ]
    category_breakdown = [
        {'name': 'Food', 'total': 450.25, 'percent': 36},
        {'name': 'Transport', 'total': 300.50, 'percent': 24},
        {'name': 'Bills', 'total': 250.00, 'percent': 20},
        {'name': 'Health', 'total': 150.00, 'percent': 12},
        {'name': 'Other', 'total': 100.00, 'percent': 8},
    ]
    return render_template('profile.html',
                           user=user,
                           summary_stats=summary_stats,
                           transactions=transactions,
                           category_breakdown=category_breakdown)


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
