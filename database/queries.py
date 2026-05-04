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


def get_summary_stats(user_id):
    """Return dict with total_spent, transaction_count, top_category.
    If user has no expenses: total_spent=0, transaction_count=0, top_category='—'."""
    conn = get_db()
    try:
        # Get total spent and count
        cur = conn.execute(
            "SELECT SUM(amount) AS total, COUNT(*) AS cnt FROM expenses WHERE user_id = ?",
            (user_id,)
        )
        row = cur.fetchone()
        total_spent = row["total"] if row["total"] is not None else 0.0
        transaction_count = row["cnt"] if row["cnt"] is not None else 0

        if transaction_count == 0:
            top_category = "—"
        else:
            cur = conn.execute(
                "SELECT category, SUM(amount) AS cat_total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY cat_total DESC LIMIT 1",
                (user_id,)
            )
            row = cur.fetchone()
            top_category = row["category"] if row else "—"

        return {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_category,
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10):
    """Return list of dicts with date, description, category, amount (newest first).
    Each dict has keys: date, description, category, amount."""
    conn = get_db()
    try:
        cur = conn.execute(
            "SELECT date, description, category, amount FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT ?",
            (user_id, limit)
        )
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


def get_category_breakdown(user_id):
    """Return list of dicts with name, amount, pct (int, sums to 100).
    Ordered by amount desc. If user has no expenses, returns empty list.
    The pct values are integers that sum to 100; the category with the largest
    raw remainder absorbs any rounding delta."""
    conn = get_db()
    try:
        cur = conn.execute(
            "SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC",
            (user_id,)
        )
        rows = cur.fetchall()
        if not rows:
            return []

        # Overall total spent for the user
        cur_total = conn.execute(
            "SELECT SUM(amount) AS total FROM expenses WHERE user_id = ?",
            (user_id,)
        )
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
