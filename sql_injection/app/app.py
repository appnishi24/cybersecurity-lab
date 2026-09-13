import os
import sqlite3

from flask import Flask, request

app = Flask(__name__)
DB_PATH = os.getenv("DATABASE_PATH", "/data/app.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def index():
    return (
        "<h1>SQL Injection Lab</h1>"
        "<p>Use POST /login with username and password.</p>"
    )


@app.post("/login")
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # INTENTIONALLY VULNERABLE:
    # User input is concatenated directly into the SQL statement.
    query = (
        "SELECT id, username FROM users "
        f"WHERE username = '{username}' AND password = '{password}'"
    )

    conn = get_db()
    try:
        user = conn.execute(query).fetchone()
    finally:
        conn.close()

    if user:
        return f"Login successful: {user['username']}"

    return "Login failed", 401


@app.get("/secret")
def secret():
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, value FROM secrets WHERE id = 1"
        ).fetchone()
    finally:
        conn.close()

    if not row:
        return "Secret not found", 404

    return f"{row['name']}: {row['value']}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
