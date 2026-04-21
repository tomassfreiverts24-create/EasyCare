
import unittest
import os
import uuid

from Registracija import (
    set_database,
    init_db,
    register,
    login,
    save_plant,
    get_user_plants,
    delete_plant
)

class TestRegistracijaDB(unittest.TestCase):

    def setUp(self):
        """
        Katram testam veido JAUNU DB failu
        (nav lock, nav konflikta, nav WinError)
        """
        self.test_db = f"test_{uuid.uuid4().hex}.db"
        set_database(self.test_db)
        init_db()

    def tearDown(self):
        """
        AIZVER un dzēš DB pēc katra testa
        """
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except PermissionError:
                pass  # Windows dažreiz aizkavē atslēgšanu

    def test_register_and_login(self):
        result = register("user1", "pass")
        self.assertTrue(result)

        user_id = login("user1", "pass")
        self.assertIsNotNone(user_id)

    def test_duplicate_register(self):
        register("dup_user", "pass")
        second = register("dup_user", "pass")
        self.assertFalse(second)

    def test_save_and_get_plant(self):
        register("plant_user", "pass")
        user_id = login("plant_user", "pass")

        save_plant(
            user_id,
            "Test Plant",
            "Testus plantus",
            "Vidēja",
            "Saulains",
            "Testa apraksts"
        )

        plants = get_user_plants(user_id)
        self.assertEqual(len(plants), 1)

    def test_delete_plant(self):
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

        delete_plant(user_id, "Plantus deleto")
        plants = get_user_plants(user_id)
        self.assertEqual(len(plants), 0)


if __name__ == "__main__":
    unittest.main()
