
"""
Modulis lietotāju un augu datubāzes pārvaldībai.

Šis modulis nodrošina:
- datubāzes inicializāciju
- lietotāju reģistrāciju un autentifikāciju
- lietotāja augu saglabāšanu, iegūšanu un dzēšanu

Datu uzglabāšanai tiek izmantota SQLite datubāze.
"""

import sqlite3
import hashlib


# Aktīvās datubāzes fails (tiek iestatīts dinamīgi)
from config import DB_NAME


def set_database(db_name):
    
    """
    Iestata aktīvās SQLite datubāzes faila nosaukumu.

    Šī funkcija ļauj izmantot dažādas datubāzes,
    piemēram, produkcijas un testa režīmā.

    :param db_name: Datubāzes faila nosaukums
    :type db_name: str
    """

    global DB_NAME
    DB_NAME = db_name


# ==================
# PASSWORD
# ==================
def hash_password(password):
    
    """
    Šifrē paroli, izmantojot SHA‑256 algoritmu.

    Parole netiek glabāta atklātā tekstā,
    kas uzlabo sistēmas drošību.

    :param password: Lietotāja ievadītā parole
    :type password: str
    :return: Paroles SHA‑256 hešs
    :rtype: str
    """
    
    return hashlib.sha256(password.encode()).hexdigest()


# ==================
# INIT DB
# ==================
def init_db():

    """
    Inicializē datubāzi.

    Izveido nepieciešamās tabulas, ja tās vēl neeksistē:
    - users (lietotāji)
    - plants (lietotāju augi)

    Funkcija ir droša atkārtotai izsaukšanai.
    """

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Lietotāju tabula
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Augu tabula
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


# ==================
# AUTH
# ==================
def register(username, password):
    
    """
    Reģistrē jaunu lietotāju datubāzē.

    :param username: Lietotājvārds
    :type username: str
    :param password: Parole (tiks šifrēta)
    :type password: str
    :return: True, ja lietotājs reģistrēts; False, ja jau eksistē
    :rtype: bool
    """

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
        # Lietotājvārds jau eksistē
        return False


def login(username, password):
    
    """
    Autentificē lietotāju.

    :param username: Lietotājvārds
    :type username: str
    :param password: Parole
    :type password: str
    :return: Lietotāja ID, ja dati pareizi; None pretējā gadījumā
    :rtype: int | None
    """

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        "SELECT id FROM users WHERE username = ? AND password = ?",
        (username, hash_password(password))
    )

    result = c.fetchone()
    conn.close()

    return result[0] if result else None


# ==================
# PLANTS
# ==================
def save_plant(user_id, plant_name, scientific_name, watering, sunlight, description):
    
    """
    Saglabā jaunu augu konkrētam lietotājam.

    :param user_id: Lietotāja ID
    :type user_id: int
    :param plant_name: Auga nosaukums
    :type plant_name: str
    :param scientific_name: Auga zinātniskais nosaukums
    :type scientific_name: str
    :param watering: Laistīšanas informācija
    :type watering: str
    :param sunlight: Apgaismojuma prasības
    :type sunlight: str
    :param description: Apraksts
    :type description: str
    """

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

    """
    Atgriež visus konkrētā lietotāja saglabātos augus.

    :param user_id: Lietotāja ID
    :type user_id: int
    :return: Saraksts ar augiem
    :rtype: list[tuple]
    """

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


# ==================
# DELETE PLANT
# ==================
def delete_plant(user_id, scientific_name):

    """
    Dzēš konkrētu augu konkrētam lietotājam.

    Tiek izmantots lietotāja ID, lai nodrošinātu,
    ka viens lietotājs nevar dzēst cita lietotāja augus.

    :param user_id: Lietotāja ID
    :type user_id: int
    :param scientific_name: Auga zinātniskais nosaukums
    :type scientific_name: str
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

