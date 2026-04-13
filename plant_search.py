
import sqlite3

DB_NAME = "database.db"


def search_plants_by_name(query):
    """
    Atgriež sarakstu ar augiem, kas SATUR meklējamo tekstu
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT plant_name, scientific_name
        FROM plants
        WHERE scientific_name LIKE ? OR plant_name LIKE ?
    """, (f"%{query}%", f"%{query}%"))

    results = c.fetchall()
    conn.close()
    return results


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
