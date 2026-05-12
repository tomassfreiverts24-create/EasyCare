"""
online_plant_search.py

Šis modulis nodrošina augu meklēšanu INTERNETĀ,
izmantojot Perenual augu datubāzes API.

Atbildība:
- Meklēt augus pēc nosaukuma
- NEstrādā ar lokālo SQLite DB
- NEietver GUI loģiku
"""

import requests
import urllib.parse

# ================== API KONFIGURĀCIJA ==================

PERENUAL_API_KEY = "sk-7kCh69b7f944cffbd15498A"


# ================== MEKLĒŠANA INTERNETA DB ==================

def search_plants_online(query: str, limit: int = 5):
    """
    Meklē augus Perenual API pēc nosaukuma vai tā daļas.

    :param query: auga nosaukums vai fragmenta teksts
    :param limit: cik rezultātus atgriezt (default 5)
    :return: saraksts ar (common_name, scientific_name, plant_id)
    """

    if not query:
        return []

    encoded_query = urllib.parse.quote(query)

    try:
        response = requests.get(
            "https://perenual.com/api/v2/species-list",
            params={
                "key": PERENUAL_API_KEY,
                "q": encoded_query
            },
            timeout=10
        )

        data = response.json()
        results = []

        for plant in data.get("data", [])[:limit]:
            common_name = plant.get("common_name", "Nav nosaukuma")
            scientific_name = plant.get("scientific_name", [""])[0]
            plant_id = plant.get("id")

            results.append(
                (common_name, scientific_name, plant_id)
            )

        return results

    except requests.exceptions.Timeout:
        print("ONLINE SEARCH ERROR: Perenual API timeout")
        return []

    except Exception as e:
        print("ONLINE SEARCH ERROR:", e)
        return []
