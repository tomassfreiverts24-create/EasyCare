
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
from kindwise import PlantApi
import requests
import urllib.parse
import json

# ==========================
# TAVS KINDWISE API KEY
# ==========================
api = PlantApi('jMJ0TsKkBoIR3Xvo8sgPhNpcwknJDnTOImc2VwURiJfaYTOcZ9')

# ==========================
# TAVS PERENUAL API KEY
# ==========================
PERENUAL_KEY = "sk-7kCh69b7f944cffbd15498"


# ----------------------------------------------------------
#   GOOGLE WEB TRANSLATE → LATVIEŠU VALODA
# ----------------------------------------------------------
def translate_to_lv(text):
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": "lv",
            "dt": "t",
            "q": text
        }
        response = requests.get(url, params=params)
        data = response.json()
        return "".join([t[0] for t in data[0]])
    except:
        return text  # ja tulkošana neizdodas, atstāj angliski



# ----------------------------------------------------------
#   Perenual: Detalizēta kopšanas informācija
# ----------------------------------------------------------
def get_perenual_care_info(scientific_name):

    query = urllib.parse.quote(scientific_name)

    # ❗ LABOTS — NOŅEMTS "&amp;"
    search_url = f"https://perenual.com/api/v2/species-list?key={PERENUAL_KEY}&q={query}"

    try:
        search_resp = requests.get(search_url).json()

        if "data" not in search_resp or not search_resp["data"]:
            return "\n---\nPerenual: Nav informācijas par šo augu.\n"

        plant = search_resp["data"][0]
        plant_id = plant["id"]

        details_url = f"https://perenual.com/api/v2/species/details/{plant_id}?key={PERENUAL_KEY}"
        details_resp = requests.get(details_url).json()

        care = "\n=== Perenual kopšanas informācija ===\n"

        # ------------------------------------
        # Latviesots laistīšanas kalkulators
        # ------------------------------------
        watering_map = {
            "frequent": "3–5 reizes nedēļā",
            "average": "1–2 reizes nedēļā",
            "minimum": "1 reizi 10–14 dienās",
            "none": "Nav nepieciešams laistīt"
        }

        watering = details_resp.get("watering")
        if watering:
            care += f"- Laistīšana: {watering_map.get(watering.lower(), watering)}\n"

        # Saules gaisma
        sunlight = details_resp.get("sunlight")
        if sunlight:
            lv_sun = translate_to_lv(", ".join(sunlight))
            care += f"- Saules gaisma: {lv_sun}\n"

        # Temperatūra
        temp_min = details_resp.get("temperature_min")
        if temp_min:
            care += f"- Minimālā temperatūra: {temp_min}°C\n"

        temp_max = details_resp.get("temperature_max")
        if temp_max:
            care += f"- Maksimālā temperatūra: {temp_max}°C\n"

        # Mitrums
        humidity = details_resp.get("humidity")
        if humidity:
            care += f"- Mitrums: {translate_to_lv(humidity)}\n"

        # Kopšanas līmenis
        care_level = details_resp.get("care_level")
        if care_level:
            care += f"- Aprūpes līmenis: {translate_to_lv(care_level)}\n"

        # Indīgums
        poisonous = details_resp.get("poisonous_to_pets")
        if poisonous is not None:
            care += f"- Indīgs mājdzīvniekiem: {'Jā' if poisonous else 'Nē'}\n"

        # Apraksts
        desc = details_resp.get("description")
        if desc:
            care += f"\nApraksts:\n{translate_to_lv(desc)}\n"

        return care

    except Exception as e:
        return f"\nKļūda, pieslēdzoties Perenual API: {str(e)}\n"



# ----------------------------------------------------------
#   Attēla izvēle + auga identifikācija
# ----------------------------------------------------------
def identify_plant():
    global img_tk

    image_path = filedialog.askopenfilename(
        title="Izvēlies auga bildi",
        filetypes=[("Image files", "*.jpg *.jpeg *.png")]
    )

    if not image_path:
        show_result("Nav izvēlēta bilde")
        return

    img = Image.open(image_path)
    img = img.resize((300, 300))
    img_tk = ImageTk.PhotoImage(img)
    image_label.config(image=img_tk)

    progress.start()
    show_result("Analizēju attēlu...")
    root.update_idletasks()

    identification = api.identify(image_path, details=['url', 'common_names'])

    progress.stop()

    suggestions = identification.result.classification.suggestions
    max_prob = max(s.probability for s in suggestions)
    best_matches = [s for s in suggestions if s.probability == max_prob]

    output = ""

    output += "Vai tas ir augs: "
    output += "Jā\n\n" if identification.result.is_plant.binary else "Nē\n\n"

    output += "Labākā atbilstība:\n\n"

    for s in best_matches:
        output += f"- Nosaukums: {translate_to_lv(s.name)}\n"
        output += f"  Varbūtība: {s.probability:.2%}\n"
        output += f"  URL: {s.details['url']}\n"
        
        cn = ", ".join(s.details.get("common_names", []))
        if cn:
            output += f"  Citas formas: {translate_to_lv(cn)}\n\n"

        # Pievienot kopšanas info
        output += get_perenual_care_info(s.name)

    show_result(output)



# ----------------------------------------------------------
#   GUI
# ----------------------------------------------------------
def show_result(text):
    result_box.config(state="normal")
    result_box.delete("1.0", tk.END)
    result_box.insert(tk.END, text)
    result_box.config(state="disabled")


root = tk.Tk()
root.title("Augu atpazīšana – ar tulkotu kopšanas informāciju")

ttk.Button(root, text="Izvēlēties bildi un noteikt augu", command=identify_plant).pack(pady=10)

progress = ttk.Progressbar(root, mode="indeterminate")
progress.pack(pady=5)

image_label = tk.Label(root)
image_label.pack(pady=10)

result_box = tk.Text(root, width=70, height=25, wrap="word")
result_box.pack(padx=10, pady=10)
result_box.config(state="disabled")

root.mainloop()

# testejam git
