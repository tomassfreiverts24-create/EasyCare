
import unittest
from Registracija import register, login, save_plant, get_user_plants

TEST_USER = "test_user_123"
TEST_PASS = "password123"


class TestAuthAndDB(unittest.TestCase):

    def test_register_and_login(self):
        """
        Tests, vai var reģistrēt lietotāju
        un pēc tam pieslēgties
        """
        # Reģistrācija (ja jau eksistē, tas nav tests kļūdai)
        register(TEST_USER, TEST_PASS)

        user_id = login(TEST_USER, TEST_PASS)
        self.assertIsNotNone(user_id)

    def test_save_and_get_plant(self):
        """
        Tests, vai augu var saglabāt un nolasīt no DB
        """
        user_id = login(TEST_USER, TEST_PASS)
        self.assertIsNotNone(user_id)

        save_plant(
            user_id,
            "Test Plant",
            "Testus plantus",
            "Vidēja",
            "Saulains",
            "Testa apraksts"
        )

        plants = get_user_plants(user_id)
        self.assertTrue(len(plants) > 0)


if __name__ == "__main__":
    unittest.main()
