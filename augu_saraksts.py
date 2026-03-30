
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
from kindwise import PlantApi
import requests
import urllib.parse
import json
from Registracija import login, register, save_plant, get_user_plants

# ==========================
# API ATSLĒGAS
# ==========================
api = PlantApi('jMJ0TsKkBoIR3Xvo8sgPhNpcwknJDnTOImc2VwURiJfaYTOcZ9')
PERENUAL_KEY = "sk-7kCh69b7f944cffbd15498"

current_user = None
latest_plant_data = {}


# ----------------------------------------------------------
# GOOGLE TULKOŠANA
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
        return text


# ----------------------------------------------------------
# PERENUAL — 2 SOLI: Meklēšana + Details
# ----------------------------------------------------------
def get_perenual_care_info(scientific_name):

    query = urllib.parse.quote(scientific_name)
    search_url = f"https://perenual.com/api/v2/species-list?key={PERENUAL_KEY}&q={query}"

    try:
        search_data = requests.get(search_url).json()

        if "data" not in search_data or not search_data["data"]:
            return "\n--- Perenual: Informācija nav atrasta.\n"

        plant_id = search_data["data"][0]["id"]

        details_url = f"https://perenual.com/api/v2/species/details/{plant_id}?key={PERENUAL_KEY}"
        details = requests.get(details_url).json()

        latest_plant_data.update({
            "scientific_name": scientific_name,
            "watering": details.get("watering"),
            "sunlight": ", ".join(details.get("sunlight", [])),
            "description": details.get("description", "")
        })

        care = "\n=== Perenual kopšanas informācija ===\n"

        watering_map = {
            "frequent": "3–5 reizes nedēļā",
            "average": "1–2 reizes nedēļā",
            "minimum": "1 reizi 10–14 dienās",
            "none": "Nav nepieciešams laistīt"
        }

        w = details.get("watering")
        if w: care += f"- Laistīšana: {watering_map.get(w.lower(), w)}\n"

        s = details.get("sunlight")
        if s: care += f"- Saules gaisma: {translate_to_lv(', '.join(s))}\n"

        h = details.get("humidity")
        if h: care += f"- Mitrums: {translate_to_lv(h)}\n"

        cl = details.get("care_level")
        if cl: care += f"- Aprūpes līmenis: {translate_to_lv(cl)}\n"

        p = details.get("poisonous_to_pets")
        if p is not None: care += f"- Indīgs mājdzīvniekiem: {'Jā' if p else 'Nē'}\n"

        d = details.get("description")
        if d: care += f"\nApraksts:\n{translate_to_lv(d)}\n"

        return care

    except Exception as e:
        return f"\nKļūda Perenual API: {str(e)}\n"


# ----------------------------------------------------------
# LOGIN LOGS
# ----------------------------------------------------------
def login_window():
    global current_user
    win = tk.Toplevel()
    win.title("Pieslēgšanās")

    tk.Label(win, text="Lietotājvārds:").pack()
    entry_user = tk.Entry(win)
    entry_user.pack()

    tk.Label(win, text="Parole:").pack()
    entry_pass = tk.Entry(win, show="*")
    entry_pass.pack()

    def do_login():
        global current_user
        uid = login(entry_user.get(), entry_pass.get())
        if uid:
            current_user = uid
            win.destroy()
        else:
            tk.Label(win, text="Nepareizi dati!", fg="red").pack()

    def do_register():
        if register(entry_user.get(), entry_pass.get()):
            tk.Label(win, text="Profils izveidots!", fg="green").pack()
        else:
            tk.Label(win, text="Lietotājvārds jau eksistē!", fg="red").pack()

    ttk.Button(win, text="Pieslēgties", command=do_login).pack(pady=5)
    ttk.Button(win, text="Reģistrēties", command=do_register).pack(pady=5)
    win.grab_set()


# ----------------------------------------------------------
# AUGA ATPAZĪŠANA
# ----------------------------------------------------------
def identify_plant():
    global img_tk, latest_plant_data
    latest_plant_data.clear()

    image_path = filedialog.askopenfilename(
        title="Izvēlies auga bildi",
        filetypes=[("Image files", "*.jpg *.jpeg *.png")]
    )
    if not image_path:
        show_result("Nav izvēlēta bilde")
        return

    img = Image.open(image_path).resize((300, 300))
    img_tk = ImageTk.PhotoImage(img)
    image_label.config(image=img_tk)

    progress.start()
    show_result("Analizēju attēlu...")
    root.update_idletasks()

    identification = api.identify(image_path, details=['url', 'common_names'])
    progress.stop()

    suggestions = identification.result.classification.suggestions
    best = max(suggestions, key=lambda x: x.probability)

    output = f"Vai tas ir augs: {'Jā' if identification.result.is_plant.binary else 'Nē'}\n\n"
    output += "Labākā atbilstība:\n\n"

    common_names = ", ".join(best.details.get("common_names", []))
    output += f"- Nosaukums: {translate_to_lv(best.name)}\n"
    output += f"  Varbūtība: {best.probability:.2%}\n"
    output += f"  URL: {best.details['url']}\n"
    output += f"  Citas formas: {translate_to_lv(common_names)}\n\n"

    latest_plant_data["plant_name"] = common_names or best.name

    output += get_perenual_care_info(best.name)
    show_result(output)


# ----------------------------------------------------------
# SAGLABĀT AUGU
# ----------------------------------------------------------
def save_plant_to_library():
    if not latest_plant_data:
        show_result("Nav ko saglabāt!")
        return

    save_plant(
        current_user,
        latest_plant_data["plant_name"],
        latest_plant_data["scientific_name"],
        latest_plant_data["watering"],
        latest_plant_data["sunlight"],
        latest_plant_data["description"]
    )
    show_result("✅ Augs pievienots bibliotēkai!")


# ----------------------------------------------------------
# MANĀ BIBLIOTĒKA
# ----------------------------------------------------------
def show_library():
    plants = get_user_plants(current_user)
    txt = "📚 Tavi saglabātie augi:\n\n"
    for p in plants:
        txt += f"{p[0]} ({p[1]})\nLaistīšana: {p[2]}\nGaisma: {p[3]}\n\n"
    show_result(txt)


# ----------------------------------------------------------
# GUI
# ----------------------------------------------------------
def show_result(text):
    result_box.config(state="normal")
    result_box.delete("1.0", tk.END)
    result_box.insert(tk.END, text)
    result_box.config(state="disabled")


root = tk.Tk()
root.title("Augu atpazīšana ar lietotāja profilu")

login_window()

ttk.Button(root, text="Izvēlēties bildi un noteikt augu", command=identify_plant).pack(pady=10)
ttk.Button(root, text="Pievienot bibliotēkai", command=save_plant_to_library).pack(pady=5)
ttk.Button(root, text="Mana bibliotēka", command=show_library).pack(pady=5)

progress = ttk.Progressbar(root, mode="indeterminate")
progress.pack(pady=5)

image_label = tk.Label(root)
image_label.pack(pady=10)

result_box = tk.Text(root, width=70, height=25, wrap="word")
result_box.pack(padx=10, pady=10)
result_box.config(state="disabled")

root.mainloop()
