import os
import sqlite3

db_path = os.getenv("DATABASE_PATH", "/data/app.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = sqlite3.connect(db_path)

conn.execute(
    "CREATE TABLE IF NOT EXISTS users ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "username TEXT NOT NULL UNIQUE, "
    "password TEXT NOT NULL)"
)

conn.execute(
    "CREATE TABLE IF NOT EXISTS secrets ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "name TEXT NOT NULL, "
    "value TEXT NOT NULL)"
)

conn.execute(
    "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
    ("alice", "password123"),
)
conn.execute(
    "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
    ("bob", "qwerty123"),
)
conn.execute(
    "INSERT OR IGNORE INTO secrets (id, name, value) VALUES (?, ?, ?)",
    (1, "flag", "SQL_INJECTION_LAB{login_bypass_success}"),
)

conn.commit()
conn.close()
