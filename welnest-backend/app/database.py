# app/database.py

import sqlite3
from pathlib import Path

# 📌 Absolute path to project root
BASE_DIR = Path(__file__).resolve().parent.parent

# 📌 Single source of truth for DB
DB_PATH = BASE_DIR / "welnest.db"


def get_db():
    """
    Returns a SQLite connection.
    """
    print("✅ FASTAPI USING DB:", DB_PATH)
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    """
    Initializes all database tables.
    This MUST be called once at app startup.
    """
    db = get_db()
    cursor = db.cursor()

    # ---------------- USERS TABLE ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------- MOODS TABLE ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            mood_score INTEGER NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------- JOURNALS TABLE ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.close()
