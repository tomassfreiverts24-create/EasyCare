

"""
Testa modulis funkcijām no Registracija.py

Šis modulis satur vienībtestus (unit tests),
kas pārbauda lietotāju reģistrāciju, pieslēgšanos
un augu saglabāšanu SQLite datubāzē.

Testos tiek izmantota atsevišķa, īslaicīga testa
datubāze katram testam, lai neietekmētu reālos datus.
"""

import unittest
import os
import uuid

from registracija import (
    set_database,
    init_db,
    register,
    login,
    save_plant,
    get_user_plants,
    delete_plant
)


class TestRegistracijaDB(unittest.TestCase):
    """
    Vienībtestu klase modulim Registracija.py.

    Katrs tests darbojas ar savu unikālu SQLite datubāzi,
    kas tiek izveidota testa sākumā un dzēsta pēc testa beigām.
    """

    def setUp(self):
        """
        Izpildās PIRMS katra testa.

        - Izveido unikālu testa datubāzes failu
        - Pārslēdz aplikāciju uz šo datubāzi
        - Inicializē datubāzes tabulas
        """
        # Unikāls DB nosaukums (novērš lock problēmas Windows vidē)
        self.test_db = f"test_{uuid.uuid4().hex}.db"

        # Norādām, ka turpmāk jāizmanto šī DB
        set_database(self.test_db)

        # Izveido nepieciešamās tabulas
        init_db()

    def tearDown(self):
        """
        Izpildās PĒC katra testa.

        - Dzēš testa datubāzes failu
        - Aizsargā pret Windows failu bloķēšanas kļūdām
        """
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except PermissionError:
                # Windows dažkārt aizkavē DB atbrīvošanu
                pass

    def test_register_and_login(self):
        """
        Pārbauda, vai lietotājs var:
        - veiksmīgi reģistrēties
        - veiksmīgi pieslēgties ar tiem pašiem datiem
        """
        # Reģistrācija
        result = register("user1", "pass")
        self.assertTrue(result)

        # Pieslēgšanās
        user_id = login("user1", "pass")
        self.assertIsNotNone(user_id)

    def test_duplicate_register(self):
        """
        Pārbauda, vai sistēma neatļauj
        reģistrēt vienu un to pašu lietotājvārdu divreiz.
        """
        register("dup_user", "pass")
        second = register("dup_user", "pass")

        # Otrajai reģistrācijai jāatgriež False
        self.assertFalse(second)

    def test_save_and_get_plant(self):
        """
        Pārbauda, vai:
        - lietotājs var saglabāt augu
        - saglabātais augs parādās lietotāja bibliotēkā
        """
        register("plant_user", "pass")
        user_id = login("plant_user", "pass")

        # Saglabā augu
        save_plant(
            user_id,
            "Test Plant",
            "Testus plantus",
            "Vidēja",
            "Saulains",
            "Testa apraksts"
        )

        # Iegūst lietotāja augus
        plants = get_user_plants(user_id)
        self.assertEqual(len(plants), 1)

    def test_delete_plant(self):
        """
        Pārbauda, vai lietotājs var izdzēst
        augu no savas bibliotēkas.
        """
        register("del_user", "pass")
        user_id = login("del_user", "pass")

        save_plant(
            user_id,
            "Plant",
            "Plantus deleto",
            "Zema",
            "Ēna",
            "Apraksts"
        )

        # Dzēš augu
        delete_plant(user_id, "Plantus deleto")

        # Pārbauda, vai augs tiešām dzēsts
        plants = get_user_plants(user_id)
        self.assertEqual(len(plants), 0)


if __name__ == "__main__":
    unittest.main()


