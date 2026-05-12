"""
Vienībtestu modulis plant_search.py funkcijām.

Šis modulis testē datubāzes funkcionalitāti, kas saistīta ar:
- augu meklēšanu pēc nosaukuma
- augu kopšanas informācijas iegūšanu
- augu dzēšanu no lietotāja bibliotēkas

Testos tiek izmantota atsevišķa SQLite testa datubāze,
lai neietekmētu produkcijas datus.
"""

import unittest
import sqlite3
import os

# Importē testējamo moduli
import plant_search


# Testa datubāzes nosaukums
TEST_DB = "test_database.db"


class TestPlantSearchDatabase(unittest.TestCase):
    """
    Vienībtestu klase modulim plant_search.py.

    Izmanto vienu kopīgu testa datubāzi visiem testiem klasē,
    kas tiek izveidota pirms testiem un dzēsta pēc tiem.
    """

    @classmethod
    def setUpClass(cls):
        """
        Izpildās VIENU REIZI pirms visiem testiem.

        - Dzēš veco testa datubāzi (ja tāda eksistē)
        - Izveido jaunu testa datubāzi
        - Izveido nepieciešamās tabulas
        - Ievieto testa datus
        """
        # Ja DB jau eksistē, dzēšam to
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        # Norādām, lai plant_search izmanto šo DB
        plant_search.DB_NAME = TEST_DB

        # Izveido savienojumu ar testa DB
        conn = sqlite3.connect(TEST_DB)
        c = conn.cursor()

        # Izveido augu tabulu
        c.execute("""
            CREATE TABLE plants (
                plant_name TEXT,
                scientific_name TEXT,
                watering TEXT,
                sunlight TEXT,
                description TEXT
            )
        """)

        # Izveido lietotāja-auga saistības tabulu
        c.execute("""
            CREATE TABLE user_plants (
                user_id INTEGER,
                scientific_name TEXT
            )
        """)

        # Ievieto testa augu
        c.execute(
            "INSERT INTO plants VALUES (?, ?, ?, ?, ?)",
            (
                "Roze",
                "Rosa canina",
                "Laistīt 1× nedēļā",
                "Tieša saule",
                "Savvaļas roze"
            )
        )

        # Piesaista testu augu lietotājam ar ID = 1
        c.execute(
            "INSERT INTO user_plants VALUES (?, ?)",
            (1, "Rosa canina")
        )

        conn.commit()
        conn.close()

    # ===============================
    # search_plants_by_name
    # ===============================
    def test_search_plants_by_name_found(self):
        """
        Pārbauda, vai augs tiek atrasts,
        ja meklēšanas teksts sakrīt ar nosaukumu
        vai zinātnisko nosaukumu.
        """
        results = plant_search.search_plants_by_name("Rosa")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "Roze")

    def test_search_plants_by_name_not_found(self):
        """
        Pārbauda, vai funkcija atgriež tukšu sarakstu,
        ja neviens augs neatbilst meklēšanas vaicājumam.
        """
        results = plant_search.search_plants_by_name("Tulpe")
        self.assertEqual(results, [])

    # ===============================
    # get_plant_care_by_scientific_name
    # ===============================
    def test_get_plant_care_found(self):
        """
        Pārbauda, vai kopšanas informācija tiek atgriezta,
        ja augs eksistē datubāzē.
        """
        plant = plant_search.get_plant_care_by_scientific_name("Rosa canina")

        self.assertIsNotNone(plant)
        self.assertEqual(plant[0], "Roze")
        self.assertEqual(plant[2], "Laistīt 1× nedēļā")

    def test_get_plant_care_not_found(self):
        """
        Pārbauda, vai funkcija atgriež None,
        ja augs ar norādīto zinātnisko nosaukumu neeksistē.
        """
        plant = plant_search.get_plant_care_by_scientific_name("Unknown")
        self.assertIsNone(plant)

    # ===============================
    # delete_user_plant
    # ===============================
    def test_delete_user_plant(self):
        """
        Pārbauda, vai augs tiek korekti izdzēsts
        no lietotāja bibliotēkas.
        """
        # Dzēš lietotāja augu
        plant_search.delete_user_plant(1, "Rosa canina")

        # Pārbauda DB, vai ieraksts tiešām dzēsts
        conn = sqlite3.connect(TEST_DB)
        c = conn.cursor()
        c.execute("""
            SELECT * FROM user_plants
            WHERE user_id = ? AND scientific_name = ?
        """, (1, "Rosa canina"))

        result = c.fetchone()
        conn.close()

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
