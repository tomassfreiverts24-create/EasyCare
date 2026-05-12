import sqlite3
from config import DB_NAME


# =======================
# MEKLĒŠANA PĒC NOSAUKUMA
# =======================
def search_plants_by_name(query):
    """
    Atgriež sarakstu ar augiem,
    kuru nosaukums vai zinātniskais nosaukums
    satur meklēto tekstu
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT plant_name, scientific_name
        FROM plants
        WHERE plant_name LIKE ? OR scientific_name LIKE ?
    """, (f"%{query}%", f"%{query}%"))

    results = c.fetchall()
    conn.close()
    return results


# =======================
# KOPŠANAS INFO PĒC ZIN. NOS.
# =======================
def get_plant_care_by_scientific_name(scientific_name):
    """
    Atgriež kopšanas informāciju konkrētam augam
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT plant_name, scientific_name, watering, sunlight, description
        FROM plants
        WHERE scientific_name = ?
    """, (scientific_name,))

    plant = c.fetchone()
    conn.close()
    return plant


# =======================
# DZĒST AUGU NO LIETOTĀJA BIBLIOTĒKAS
# =======================
def delete_user_plant(user_id, scientific_name):
    """
    Dzēš konkrētu augu no konkrēta lietotāja bibliotēkas
    (NEAIZTIEK kopējo augu tabulu!)
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        DELETE FROM user_plants
        WHERE user_id = ? AND scientific_name = ?
    """, (user_id, scientific_name))

    conn.commit()
    conn.close()