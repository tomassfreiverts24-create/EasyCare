import sqlite3
import hashlib

DB_NAME = "database.db"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS plants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plant_name TEXT,
        scientific_name TEXT,
        watering TEXT,
        sunlight TEXT,
        description TEXT
    )
    """)

    conn.commit()
    conn.close()


def register(username, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except:
        return False


def login(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?",
              (username, hash_password(password)))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def save_plant(user_id, plant_name, scientific_name, watering, sunlight, description):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    INSERT INTO plants (user_id, plant_name, scientific_name, watering, sunlight, description)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, plant_name, scientific_name, watering, sunlight, description))
    conn.commit()
    conn.close()


def get_user_plants(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    SELECT plant_name, scientific_name, watering, sunlight
    FROM plants WHERE user_id = ?
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows


# ✅ Izveido DB automātiski
init_db()

