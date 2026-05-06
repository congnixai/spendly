from pathlib import Path
import sqlite3
from datetime import datetime
from .db import get_db


def get_user_by_id(user_id):
    """Return dict with name, email, member_since (formatted as Month YYYY).
    Returns None if user not found."""
    conn = get_db()
    try:
        cur = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = cur.fetchone()
        if row is None:
            return None
        # Format '2026-05-04 12:34:56' -> 'May 2026'
        created_at = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
        member_since = created_at.strftime("%B %Y")
        return {
            "name": row["name"],
            "email": row["email"],
            "member_since": member_since,
        }
    finally:
        conn.close()


def get_summary_stats(user_id, date_from=None, date_to=None):
    """Return dict with total_spent, transaction_count, top_category.
    If user has no expenses: total_spent=0, transaction_count=0, top_category='—'."""
    conn = get_db()
    try:
        # Build base filter
        base_where = "WHERE user_id = ?"
        params = [user_id]
        if date_from and date_to:
            base_where += " AND date BETWEEN ? AND ?"
            params.extend([date_from, date_to])

        # Get total spent and count
        cur = conn.execute(
            f"SELECT SUM(amount) AS total, COUNT(*) AS cnt FROM expenses {base_where}",
            tuple(params)
        )
        row = cur.fetchone()
        total_spent = row["total"] if row["total"] is not None else 0.0
        transaction_count = row["cnt"] if row["cnt"] is not None else 0

        if transaction_count == 0:
            top_category = "—"
        else:
            # Top category with same filter
            cat_query = f"SELECT category, SUM(amount) AS cat_total FROM expenses {base_where} GROUP BY category ORDER BY cat_total DESC LIMIT 1"
            cur = conn.execute(cat_query, tuple(params))
            row = cur.fetchone()
            top_category = row["category"] if row else "—"

        return {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_category,
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    """Return list of dicts with date, description, category, amount (newest first).
    Each dict has keys: date, description, category, amount.
    Optional date_from/date_to filter the results."""
    conn = get_db()
    try:
        base_where = "WHERE user_id = ?"
        params = [user_id]
        if date_from and date_to:
            base_where += " AND date BETWEEN ? AND ?"
            params.extend([date_from, date_to])
        query = f"SELECT date, description, category, amount FROM expenses {base_where} ORDER BY date DESC LIMIT ?"
        params.append(limit)
        cur = conn.execute(query, tuple(params))
        rows = cur.fetchall()
        return [
            {
                "date": r["date"],
                "description": r["description"],
                "category": r["category"],
                "amount": r["amount"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_category_breakdown(user_id, date_from=None, date_to=None):
    """Return list of dicts with name, amount, pct (int, sums to 100).
    Ordered by amount desc. If user has no expenses, returns empty list.
    The pct values are integers that sum to 100; the category with the largest
    raw remainder absorbs any rounding delta."""
    conn = get_db()
    try:
        base_where = "WHERE user_id = ?"
        params = [user_id]
        if date_from and date_to:
            base_where += " AND date BETWEEN ? AND ?"
            params.extend([date_from, date_to])

        cur = conn.execute(
            f"SELECT category, SUM(amount) AS total FROM expenses {base_where} GROUP BY category ORDER BY total DESC",
            tuple(params)
        )
        rows = cur.fetchall()
        if not rows:
            return []

        # Overall total spent for the user with same filter
        total_query = f"SELECT SUM(amount) AS total FROM expenses {base_where}"
        cur_total = conn.execute(total_query, tuple(params))
        overall_total = cur_total.fetchone()["total"]
        if overall_total is None or overall_total == 0:
            return []

        categories = []
        raw_percentages = []
        for r in rows:
            raw = (r["total"] / overall_total) * 100.0
            floored = int(raw)
            remainder = raw - floored
            categories.append({"name": r["category"], "amount": r["total"], "pct": floored})
            raw_percentages.append((remainder, len(categories) - 1))

        current_sum = sum(c["pct"] for c in categories)
        delta = 100 - current_sum  # should be small integer, typically 0..num_cats-1

        if delta != 0:
            # Sort by remainder descending so the largest remainder gets the adjustment
            raw_percentages.sort(key=lambda x: x[0], reverse=True)
            for i in range(abs(delta)):
                idx = raw_percentages[i % len(raw_percentages)][1]
                if delta > 0:
                    categories[idx]["pct"] += 1
                else:
                    # defensive: never go negative, but delta should never be negative
                    if categories[idx]["pct"] > 0:
                        categories[idx]["pct"] -= 1

        return categories
    finally:
        conn.close()


def insert_expense(user_id, amount, category, date, description=None):
    """Insert a new expense and return its ID.
    Raises sqlite3.IntegrityError if invalid user_id or constraint violation.
    """
    conn = get_db()
    try:
        # If description is empty string, store as NULL
        desc_value = description if description and description.strip() else None

        cur = conn.execute(
            """INSERT INTO expenses (user_id, amount, category, date, description)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, amount, category, date, desc_value)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()
