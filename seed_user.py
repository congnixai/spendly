import random
from datetime import datetime
from werkzeug.security import generate_password_hash

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from database.db import get_db

first_names = [
    "Rahul", "Priya", "Amit", "Anjali", "Vikram", "Neha", "Raj", "Pooja",
    "Sanjay", "Meera", "Arjun", "Ananya", "Rohit", "Sneha", "Karan", "Riya",
    "Vijay", "Anjali", "Suresh", "Priya", "Rahul", "Anita", "Mohan", "Sunita"
]
last_names = [
    "Sharma", "Patel", "Singh", "Gupta", "Reddy", "Khan", "Joshi", "Das",
    "Iyer", "Verma", "Malhotra", "Desai", "Nair", "Kumar", "Rao", "Agarwal",
    "Bhat", "Chopra", "Mehta", "Shah", "Trivedi", "Mishra", "Yadav", "Saxena"
]

def generate_unique_email(conn, first, last):
    while True:
        num = random.randint(10, 999)
        email = f"{first.lower()}.{last.lower()}{num}@gmail.com"
        cur = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        if cur.fetchone() is None:
            return email

def main():
    conn = get_db()
    try:
        first = random.choice(first_names)
        last = random.choice(last_names)
        name = f"{first} {last}"

        email = generate_unique_email(conn, first, last)
        password_hash = generate_password_hash("password123")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email, password_hash, created_at)
        )
        conn.commit()
        user_id = cur.lastrowid

        print(f"User seeded successfully:")
        print(f"id: {user_id}")
        print(f"name: {name}")
        print(f"email: {email}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
