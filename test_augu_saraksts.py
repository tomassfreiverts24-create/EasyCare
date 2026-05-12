import unittest     
from unittest.mock import patch

# ✅ Importē funkcijas no augu_saraksts.py
from augu_saraksts import (
    normalize_scientific_name,
    explain_watering,
    explain_sunlight,
    explain_temperature,
    translate_to_lv
)


class TestNormalizeScientificName(unittest.TestCase):

    def test_normal_name(self):
        self.assertEqual(
            normalize_scientific_name("Rosa Canina"),
            "Rosa canina"
        )

    def test_name_with_parentheses(self):
        self.assertEqual(
            normalize_scientific_name("Rosa Canina (Dog Rose)"),
            "Rosa canina"
        )

    def test_list_input(self):
        self.assertEqual(
            normalize_scientific_name(["Ficus Elastica"]),
            "Ficus elastica"
        )

    def test_empty_value(self):
        self.assertEqual(normalize_scientific_name(""), "")


class TestExplainWatering(unittest.TestCase):

    def test_known_level(self):
        self.assertEqual(
            explain_watering("low"),
            "Laistīt 1× nedēļā."
        )

    def test_unknown_level(self):
        self.assertEqual(
            explain_watering("abc"),
            "Laistīt, kad augsnes virskārta izžūst."
        )


class TestExplainSunlight(unittest.TestCase):

    def test_full_sun(self):
        self.assertEqual(
            explain_sunlight("full sun"),
            "Tieša saule (6–8 h dienā)."
        )

    def test_partial_sun(self):
        self.assertIn(
            "Daļēja saule",
            explain_sunlight("part shade")
        )

    def test_shade(self):
        self.assertEqual(
            explain_sunlight("shade"),
            "Pusēna vai ēna."
        )


class TestExplainTemperature(unittest.TestCase):

    def test_frequent_watering(self):
        self.assertEqual(
            explain_temperature("frequent"),
            "Optimāli: 18–26 °C"
        )

    def test_minimum_watering(self):
        self.assertEqual(
            explain_temperature("minimum"),
            "Optimāli: 15–24 °C"
        )


class TestTranslateToLV(unittest.TestCase):

    @patch("augu_saraksts.requests.get")
    def test_translate_success(self, mock_get):
        mock_get.return_value.json.return_value = [
            [["Augs ir skaists", "The plant is beautiful", None, None]]
        ]

        result = translate_to_lv("The plant is beautiful")
        self.assertEqual(result, "Augs ir skaists")

    @patch("augu_saraksts.requests.get", side_effect=Exception("No internet"))
    def test_translate_failure_returns_original(self, mock_get):
        text = "Hello"
        self.assertEqual(translate_to_lv(text), text)


if __name__ == "__main__":
    unittest.main()
