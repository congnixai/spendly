#!/usr/bin/env python3
import random
from datetime import datetime, timedelta
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from database.db import get_db

# Category definitions with Indian context
categories = [
    {"name": "Food", "min": 50, "max": 800, "count_weight": 20},
    {"name": "Transport", "min": 20, "max": 500, "count_weight": 10},
    {"name": "Bills", "min": 200, "max": 3000, "count_weight": 15},
    {"name": "Health", "min": 100, "max": 2000, "count_weight": 5},
    {"name": "Entertainment", "min": 100, "max": 1500, "count_weight": 3},
    {"name": "Shopping", "min": 200, "max": 5000, "count_weight": 10},
    {"name": "Other", "min": 58, "max": 1000, "count_weight": 5}
]

# Validate arguments
if len(sys.argv) != 4 or not all(arg.isdigit() for arg in sys.argv[1:]):
    print(f"Usage: {sys.argv[0]} <user_id> <count> <months>")
    print(f"Example: {sys.argv[0]} 1 50 6")
    sys.exit(1)

user_id = int(sys.argv[1])
count = int(sys.argv[2])
months = int(sys.argv[3])

# Verify user exists
conn = get_db()
user = conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
if not user:
    print(f"No user found with id {user_id}.")
    conn.close()
    sys.exit(1)

# Calculate date range
start_date = datetime.now() - timedelta(days=30*months)
end_date = datetime.now()

# Generate expenses with weighted category distribution
expenses = []
total_weight = sum(c["count_weight"] for c in categories)
for _ in range(count):
    # Select category with weighted probability
    selected = random.choices(categories, weights=[c["count_weight"] for c in categories])[0]

    # Generate amount within range
    amount = random.uniform(selected["min"], selected["max"])

    # Calculate random date within range
    date_offset = random.randint(0, months*30)
    expense_date = start_date + timedelta(days=date_offset)
    formatted_date = expense_date.strftime("%Y-%m-%d")

    # Generate realistic description
    description = f"{selected['name'].lower()}: {random.randint(50, 1500)}"

    # Add to list
    expenses.append( (
        user_id,
        amount,
        selected['name'],
        formatted_date,
        description
    ) )

# Insert using transaction
try:
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses
    )
    conn.commit()
except Exception as e:
    conn.rollback()
    print(f"Error inserting expenses: {e}")
    sys.exit(1)

# Print summary
print(f"Inserted {len(expenses)} expense(s) for user {user_id}")
print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

# Print 5 samples
print("Sample records:")
for record in expenses[:5]:
    print(f"{record[0]} | {record[1]:.2f} | {record[2]} | {record[3]} | {record[4]}")