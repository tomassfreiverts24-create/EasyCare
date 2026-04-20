import sqlite3
import hashlib

DB_NAME = "database.db"


# ================== PASSWORD ==================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ================== INIT DB ==================
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
        description TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


# ================== AUTH ==================
def register(username, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )

        conn.commit()
        conn.close()
        return True

    except sqlite3.IntegrityError:
        return False


def login(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        "SELECT id FROM users WHERE username = ? AND password = ?",
        (username, hash_password(password))
    )

    result = c.fetchone()
    conn.close()

    return result[0] if result else None


# ================== PLANTS ==================
def save_plant(user_id, plant_name, scientific_name, watering, sunlight, description):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO plants (
            user_id,
            plant_name,
            scientific_name,
            watering,
            sunlight,
            description
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        plant_name,
        scientific_name,
        watering,
        sunlight,
        description
    ))

    conn.commit()
    conn.close()


def get_user_plants(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT
            plant_name,
            scientific_name,
            watering,
            sunlight
        FROM plants
        WHERE user_id = ?
        ORDER BY plant_name
    """, (user_id,))

    rows = c.fetchall()
    conn.close()
    return rows


# ================== DELETE PLANT ==================
def delete_plant(user_id, scientific_name):
    """
    Dzēš konkrētu augu konkrētam lietotājam
    (ar apzinātu ierobežojumu — nevar izdzēst cita lietotāja augus)
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        DELETE FROM plants
        WHERE user_id = ?
        AND scientific_name = ?
    """, (user_id, scientific_name))

    conn.commit()
    conn.close()


# ================== START ==================
init_db()
