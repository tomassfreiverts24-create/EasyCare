
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
from kindwise import PlantApi
import requests
import urllib.parse

# ==========================
# TAVS KINDWISE API KEY
# ==========================
api = PlantApi('jMJ0TsKkBoIR3Xvo8sgPhNpcwknJDnTOImc2VwURiJfaYTOcZ9')

# ==========================
# TAVS PERENUAL API KEY
# ==========================
PERENUAL_KEY = "sk-7kCh69b7f944cffbd15498"

# ----------------------------------------------------------
#   FUNKCIJA: Iegūst kopšanas informāciju no Perenual API
# ----------------------------------------------------------
def get_perenual_care_info(scientific_name):

    query = urllib.parse.quote(scientific_name)
    url = f"https://perenual.com/api/v2/species-list?key={PERENUAL_KEY}&q={query}"

    try:
        response = requests.get(url)
        
        print("Perenual URL:", url)
        print("Response:", response.text)

        data = response.json()

        # Nav rezultātu
        if "data" not in data or not data["data"]:
            return "\n---\nPerenual: Nav informācijas par šo augu.\n"

        plant = data["data"][0]  # Pirmais atbilstošais ieraksts

        care_info = "\n=== Perenual kopšanas informācija ===\n"

        # Saules gaisma
        sunlight = plant.get("sunlight", [])
        if sunlight:
            care_info += f"- Saules gaisma: {', '.join(sunlight)}\n"

        # Laistīšana
        watering = plant.get("watering", None)
        if watering:
            care_info += f"- Laistīšana: {watering}\n"

        # Kopšanas līmenis
        care_level = plant.get("care_level", "")
        if care_level:
            care_info += f"- Aprūpes līmenis: {care_level}\n"

        # Indīgums / ēdamība
        edible = plant.get("edible", None)
        poisonous = plant.get("poisonous", None)
        if edible is not None:
            care_info += f"- Ēdams: {'Jā' if edible else 'Nē'}\n"
        if poisonous is not None:
            care_info += f"- Indīgs: {'Jā' if poisonous else 'Nē'}\n"

        # Apraksts
        description = plant.get("description", "")
        if description:
            care_info += f"\nApraksts:\n{description}\n"

        return care_info

    except Exception as e:
        return f"\nKļūda, pieslēdzoties Perenual API: {str(e)}\n"



# ----------------------------------------------------------
#   FUNKCIJA: Attēla izvēle + auga identifikācija
# ----------------------------------------------------------
def identify_plant():
    global img_tk

    # izvēlēties failu
    image_path = filedialog.askopenfilename(
        title="Izvēlies auga bildi",
        filetypes=[("Image files", "*.jpg *.jpeg *.png")]
    )

    if not image_path:
        show_result("Nav izvēlēta bilde")
        return

    # PARĀDĀM BILDI GUI
    img = Image.open(image_path)
    img = img.resize((300, 300))
    img_tk = ImageTk.PhotoImage(img)
    image_label.config(image=img_tk)

    # PARĀDĀM PROGRESS BAR
    progress.start()
    show_result("Analizēju attēlu...")

    root.update_idletasks()

    # API PIEPRASĪJUMS KINDWISE (attēlu atpazīšana)
    identification = api.identify(image_path, details=['url', 'common_names'])

    progress.stop()

    # APSTRĀDĀM REZULTĀTUS
    suggestions = identification.result.classification.suggestions
    max_prob = max(s.probability for s in suggestions)
    best_matches = [s for s in suggestions if s.probability == max_prob]

    # FORMATĒJAM IZVADI
    output = ""

    output += "Vai tas ir augs: "
    output += "Jā\n\n" if identification.result.is_plant.binary else "Nē\n\n"

    output += "Labākā atbilstība:\n\n"

    for s in best_matches:
        output += f"- {s.name}\n"
        output += f"  Varbūtība: {s.probability:.2%}\n"
        output += f"  URL: {s.details['url']}\n"
        output += f"  Citas formas: {s.details['common_names']}\n\n"

        # 🔥 PIEVIENO PERENUAL API KOPŠANAS INFORMĀCIJU
        output += get_perenual_care_info(s.name)

    show_result(output)



# ----------------------------------------------------------
#        GUI ELEMENTI
# ----------------------------------------------------------
def show_result(text):
    result_box.config(state="normal")
    result_box.delete("1.0", tk.END)
    result_box.insert(tk.END, text)
    result_box.config(state="disabled")


root = tk.Tk()
root.title("Augu atpazīšana ar kopšanas datiem")

ttk.Button(root, text="Izvēlēties bildi un noteikt augu", command=identify_plant).pack(pady=10)

# Progress bar
progress = ttk.Progressbar(root, mode="indeterminate")
progress.pack(pady=5)

# Bilde
image_label = tk.Label(root)
image_label.pack(pady=10)

# Rezultātu logs
result_box = tk.Text(root, width=70, height=20, wrap="word")
result_box.pack(padx=10, pady=10)
result_box.config(state="disabled")



root.mainloop()
