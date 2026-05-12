
"""
EasyCare 🌿 – augu atpazīšanas un kopšanas palīgs.

Šī programma nodrošina:
- lietotāju reģistrāciju un pieslēgšanos;
- augu atpazīšanu pēc attēla, izmantojot ārējo API;
- augu meklēšanu datubāzē pēc nosaukuma;
- augu kopšanas informācijas attēlošanu;
- personīgās augu bibliotēkas veidošanu un pārvaldību.

Lietotāja dati tiek glabāti SQLite datubāzē, ārējā modulī "Registracija".
Programmas grafiskā saskarne veidota, izmantojot Tkinter.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from kindwise import PlantApi
import requests
import urllib.parse
import threading
import traceback

from Registracija import (
    login,
    register,
    save_plant,
    get_user_plants,
    delete_plant
)

# ================== API KEYS ==================
# API augu atpazīšanai
api = PlantApi("GcPNebO8G8ItSZ0OJNJZfyvpTylhpMjoqN4gvxS9BhZJSGnDOL")
# API augu datubāzei (kopšanas informācij
PERENUAL_KEY = "sk-7kCh69b7f944cffbd15498"
# Pašreiz pieslēgtais lietotājs
current_user = None
# Pēdējais atpazītais vai meklētais augs
latest_plant = {}
# Karodziņš funkcijas izpildes laika kontrole
identify_finished = False

# ================== DIZAINS / TĒMA ==================
BG_MAIN = "#E8F3EC"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#C7DED1"
ACCENT = "#3A7F5C"

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_NORMAL = ("Segoe UI", 13)
FONT_SMALL = ("Segoe UI", 11)

# ================== PALĪGFUNKCIJAS ==================
def normalize_scientific_name(value):
    
    """
    Normalizē auga zinātnisko nosaukumu.

    Funkcija noņem lieko tekstu, iekavas un garantē,
    ka nosaukums ir pareizi formatēts (piem., Genus species).

    :param value: Ievadītais nosaukums
    :type value: str | list
    :return: Normalizēts nosaukums
    :rtype: str
    """

    if not value:
        return ""
    if isinstance(value, list):
        value = value[0]
    value = str(value).strip()
    if "(" in value:
        value = value.split("(")[0].strip()
    parts = value.split()
    if len(parts) < 2:
        return value.capitalize()
    return f"{parts[0].capitalize()} {parts[1].lower()}"

def translate_to_lv(text):
    
    """
    Tulkot tekstu no angļu valodas uz latviešu valodu,
    izmantojot Google Translate neoficiālo API.

    Ja tulkošana neizdodas, tiek atgriezts oriģinālais teksts.

    :param text: Teksts angļu valodā
    :type text: str
    :return: Tulkotais teksts
    :rtype: str
    """

    try:
        r = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": "en",
                "tl": "lv",
                "dt": "t",
                "q": text
            },
            timeout=10
        )
        return "".join(x[0] for x in r.json()[0])
    except:
        return text

def explain_watering(level):
    
    """
    Pārveido API laistīšanas līmeni uz saprotamu aprakstu.

    :param level: Laistīšanas līmenis no API
    :type level: str
    :return: Laistīšanas paskaidrojums
    :rtype: str
    """

    return {
        "minimum": "Laistīt 1× ik pēc 10–14 dienām.",
        "low": "Laistīt 1× nedēļā.",
        "average": "Laistīt 2× nedēļā.",
        "moderate": "Laistīt 2–3× nedēļā.",
        "frequent": "Laistīt 3–4× nedēļā."
    }.get(level.lower(), "Laistīt, kad augsnes virskārta izžūst.")

def explain_sunlight(text):
        
    """
    Paskaidro auga gaismas prasības.

    :param text: Gaismas informācija no API
    :type text: str
    :return: Gaismas paskaidrojums
    :rtype: str
    """

    t = text.lower()
    if "full sun" in t:
        return "Tieša saule (6–8 h dienā)."
    if "part" in t:
        return "Daļēja saule – bez pusdienas saules."
    if "shade" in t:
        return "Pusēna vai ēna."
    return "Izkliedēta dienasgaisma."

def explain_temperature(watering):
    
    """
    Nosaka ieteicamo temperatūru, balstoties uz laistīšanas līmeni.

    :param watering: Laistīšanas intensitāte
    :type watering: str
    :return: Temperatūras paskaidrojums
    :rtype: str
    """

    if watering in ["frequent", "average", "moderate"]:
        return "Optimāli: 18–26 °C"
    return "Optimāli: 15–24 °C"

# ================== PERENUAL ==================
def get_perenual(scientific):
    
    """
    Iegūst auga kopšanas informāciju no Perenual API,
    izmantojot auga zinātnisko nosaukumu.

    :param scientific: Auga zinātniskais nosaukums
    :type scientific: str
    :return: True, ja dati veiksmīgi iegūti
    :rtype: bool
    """

    q = urllib.parse.quote(scientific)
    search = requests.get(
        f"https://perenual.com/api/v2/species-list?key={PERENUAL_KEY}&q={q}",
        timeout=15
    ).json()

    if not search.get("data"):
        return False

    pid = search["data"][0]["id"]
    details = requests.get(
        f"https://perenual.com/api/v2/species/details/{pid}?key={PERENUAL_KEY}",
        timeout=15
    ).json()

    watering_raw = details.get("watering", "average")
    sunlight_raw = ", ".join(details.get("sunlight", []))

    latest_plant.update({
        "watering": explain_watering(watering_raw),
        "sunlight": explain_sunlight(sunlight_raw),
        "temperature": explain_temperature(watering_raw),
        "desc": translate_to_lv(details.get("description", ""))
    })
    return True

# ================== LOGIN ==================
def show_login():
    
    """
    Attēlo pieslēgšanās un reģistrācijas logu.
    """

    for w in root.winfo_children():
        w.destroy()

    root.configure(bg=BG_MAIN)

    tk.Label(root, text="EasyCare 🌿", font=FONT_TITLE, bg=BG_MAIN).pack(pady=20)

    tk.Label(root, text="Lietotājvārds", bg=BG_MAIN, font=FONT_NORMAL).pack()
    u = tk.Entry(root, font=FONT_NORMAL)
    u.pack(pady=5)

    tk.Label(root, text="Parole", bg=BG_MAIN, font=FONT_NORMAL).pack()
    p = tk.Entry(root, show="*", font=FONT_NORMAL)
    p.pack(pady=5)

    msg = tk.Label(root, bg=BG_MAIN, font=FONT_SMALL)
    msg.pack(pady=10)

    def do_login():
        
        """
        Veic lietotāja autentifikāciju.
        """

        global current_user
        uid = login(u.get(), p.get())
        if uid:
            current_user = uid
            show_main()
        else:
            msg.config(text="❌ Nepareizi dati")

    def do_register():
        
        """
        Reģistrē jaunu lietotāju sistēmā.
        """

        if register(u.get(), p.get()):
            msg.config(text="✅ Reģistrēts! Pieslēdzies.")
        else:
            msg.config(text="⚠️ Lietotājs jau eksistē")

    tk.Button(root, text="Pieslēgties", command=do_login,
              font=FONT_NORMAL, bg=ACCENT, fg="white", padx=20, pady=6).pack(pady=5)

    tk.Button(root, text="Reģistrēties", command=do_register,
              font=FONT_SMALL).pack()

# ================== MAIN UI ==================
def show_main():
    for w in root.winfo_children():
        w.destroy()

    global result, img_label

    root.configure(bg=BG_MAIN)

    # HUD
    top = tk.Frame(root, bg=BG_MAIN, pady=12)
    top.pack(fill="x")

    btn_opts = {
        "font": FONT_NORMAL,
        "bg": ACCENT,
        "fg": "white",
        "padx": 16,
        "pady": 8
    }

    tk.Button(top, text="📷 Atpazīt", command=start_identify, **btn_opts).pack(side="left", padx=10)
    tk.Button(top, text="➕ Saglabāt", command=save_current, **btn_opts).pack(side="left", padx=10)
    tk.Button(top, text="📚 Bibliotēka", command=show_library, **btn_opts).pack(side="left", padx=10)

    # Search
    search = tk.Frame(root, bg=BG_MAIN, pady=10)
    search.pack()

    tk.Label(search, text="🔎 Meklēt augu:", bg=BG_MAIN, font=FONT_NORMAL).pack(side="left")
    entry = tk.Entry(search, width=40, font=FONT_NORMAL)
    entry.pack(side="left", padx=8)

    tk.Button(search, text="Meklēt",
              command=lambda: search_by_name(entry.get()),
              **btn_opts).pack(side="left")

    img_label = tk.Label(root, bg=BG_MAIN)
    img_label.pack(pady=10)

    result = tk.Text(
        root,
        font=FONT_NORMAL,
        bg=BG_MAIN,
        relief="flat"
    )
    result.pack(fill="both", expand=True, padx=20, pady=10)

# ================== IDENTIFY ==================
def start_identify():
    path = filedialog.askopenfilename()
    if not path:
        return

    img = Image.open(path).resize((360, 360))
    img_label.image = ImageTk.PhotoImage(img)
    img_label.config(image=img_label.image)

    result.delete("1.0", tk.END)
    result.insert(tk.END, "🔍 Atpazīst augu...\n")

    
    global identify_finished
    identify_finished = False

    threading.Thread(
        target=identify_worker,
        args=(path,),
        daemon=True
    ).start()

    # 20 sekunžu timeout
    root.after(20000, lambda: (
        show_timeout_message() if not identify_finished else None
))


def identify_worker(path):
    global identify_finished
    try:
        res = api.identify(path)
        best = max(res.result.classification.suggestions, key=lambda x: x.probability)
        sci = normalize_scientific_name(best.name)

        latest_plant.clear()
        latest_plant["name"] = sci
        latest_plant["scientific"] = sci

        if get_perenual(sci):
            identify_finished = True
            root.after(0, show_output)
        
    except Exception as e:
        identify_finished = True
        root.after(0, show_timeout_message)
    
def show_timeout_message():
    latest_plant.clear()
    result.delete("1.0", tk.END)
    result.insert(tk.END, "❌ Mums neizdevās atpazīt jūsu augu. ļoti atvainojamies, zvanot uz 25463741 iespējams iegādāties PRO versiju ar lielāku augu izvēlni! \n")
    root.after(20000, lambda: result.delete("1.0", tk.END))
# ================== SEARCH ==================
def search_by_name(name):
    if not name.strip():
        return

    result.delete("1.0", tk.END)
    result.insert(tk.END, "🔍 Meklē augu datubāzē...\n")

    threading.Thread(target=search_worker, args=(name,), daemon=True).start()

def search_worker(name):
    try:
        q = urllib.parse.quote(name)
        data = requests.get(
            f"https://perenual.com/api/v2/species-list?key={PERENUAL_KEY}&q={q}",
            timeout=15
        ).json()

        if not data.get("data"):
            root.after(0, lambda: result.insert(tk.END, "❌ Augs nav atrasts"))
            return

        plant = data["data"][0]
        sci = normalize_scientific_name(plant.get("scientific_name"))

        latest_plant.clear()
        latest_plant["name"] = plant.get("common_name") or sci
        latest_plant["scientific"] = sci

        if get_perenual(sci):
            root.after(0, show_output)

    except Exception as e:
        root.after(0, show_error, e)

# ================== KARTĪTES ==================
def plant_card(parent, plant):
    card = tk.Frame(parent, bg=CARD_BG, highlightthickness=2,
                    highlightbackground=CARD_BORDER, padx=24, pady=18)
    card.pack(fill="x", padx=40, pady=20)

    tk.Label(card, text=plant["name"], font=FONT_TITLE,
             fg=ACCENT, bg=CARD_BG).pack(anchor="w")

    tk.Label(card, text=plant["scientific"], font=FONT_SMALL,
             fg="#666", bg=CARD_BG).pack(anchor="w")

    tk.Label(card, text=f"💧 {plant['watering']}",
             font=FONT_NORMAL, bg=CARD_BG).pack(anchor="w", pady=(14, 0))
    tk.Label(card, text=f"☀️ {plant['sunlight']}",
             font=FONT_NORMAL, bg=CARD_BG).pack(anchor="w")
    tk.Label(card, text=f"🌡️ {plant['temperature']}",
             font=FONT_NORMAL, bg=CARD_BG).pack(anchor="w")

    tk.Label(card, text="📖 Apraksts:",
             font=FONT_NORMAL, bg=CARD_BG).pack(anchor="w", pady=(14, 0))

    tk.Label(card, text=plant["desc"],
             wraplength=1100, justify="left",
             font=FONT_NORMAL, bg=CARD_BG).pack(anchor="w")

# ================== OUTPUT & LIBRARY ==================
def show_output():
    result.delete("1.0", tk.END)
    frame = tk.Frame(result, bg=BG_MAIN)
    result.window_create(tk.END, window=frame)
    plant_card(frame, latest_plant)

def show_library():
    result.delete("1.0", tk.END)
    plants = get_user_plants(current_user)

    frame = tk.Frame(result, bg=BG_MAIN)
    result.window_create(tk.END, window=frame)

    if not plants:
        tk.Label(frame, text="📭 Bibliotēka ir tukša",
                 font=FONT_NORMAL, bg=BG_MAIN).pack(pady=40)
        return

    for name, sci, water, light in plants:
        card = tk.Frame(frame, bg=CARD_BG, highlightthickness=2,
                        highlightbackground=CARD_BORDER, padx=20, pady=16)
        card.pack(fill="x", padx=40, pady=14)

        tk.Label(card, text=f"🌱 {name}", font=FONT_TITLE,
                 fg=ACCENT, bg=CARD_BG).pack(anchor="w")

        tk.Label(card, text=f"💧 {water}\n☀️ {light}",
                 font=FONT_NORMAL, bg=CARD_BG).pack(anchor="w", pady=8)

        tk.Button(card, text="🗑 Dzēst",
                  font=FONT_SMALL, bg="#C84B4B", fg="white",
                  command=lambda s=sci, n=name: confirm_delete(s, n)
                  ).pack(anchor="e")

def show_error(e):
    result.delete("1.0", tk.END)
    result.insert(tk.END, "❌ Kļūda:\n" + str(e))
    traceback.print_exc()

# ================== SAVE ==================
def save_current():
    if not latest_plant:
        return
    save_plant(
        current_user,
        latest_plant["name"],
        latest_plant["scientific"],
        latest_plant["watering"],
        latest_plant["sunlight"],
        latest_plant["desc"]
    )
    result.insert(tk.END, "\n✅ Saglabāts bibliotēkā\n")

# ================== DELETE ==================
def confirm_delete(sci, name):
    if messagebox.askyesno("Dzēst", f"Vai dzēst {name}?"):
        delete_plant(current_user, sci)
        show_library()

# ================== START ==================
# Programmas galvenā loga inicializācija
root = tk.Tk()
root.title("EasyCare 🌿")
root.configure(bg=BG_MAIN)
root.state("zoomed")          # Fullscreen (Windows)
root.bind("<Escape>", lambda e: root.state("normal"))
# Parāda pieslēgšanās logu un sāk galveno ciklu
show_login()
root.mainloop()
