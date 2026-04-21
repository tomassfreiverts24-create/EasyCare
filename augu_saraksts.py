import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from kindwise import PlantApi
import requests
import urllib.parse
import threading
import traceback


from Registracija import set_database

set_database("database.db")

from Registracija import (
    login,
    register,
    save_plant,
    get_user_plants,
    delete_plant
)

# ================== API KEYS ==================
api = PlantApi("GcPNebO8G8ItSZ0OJNJZfyvpTylhpMjoqN4gvxS9BhZJSGnDOL")
PERENUAL_KEY = "sk-7kCh69b7f944cffbd15498"

current_user = None
latest_plant = {}

# ================== NORMALIZĀCIJA ==================
def normalize_scientific_name(value):
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

# ================== TULKOŠANA ==================
def translate_to_lv(text):
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

# ================== SKAIDROJUMI ==================
def explain_watering(level):
    return {
        "minimum": "Laistīt 1× ik pēc 10–14 dienām. Augs panes sausumu.",
        "low": "Laistīt 1× nedēļā, kad augsnes virskārta ir sausa.",
        "average": "Laistīt 2× nedēļā, augsnei jābūt viegli mitrai.",
        "moderate": "Laistīt 2–3× nedēļā.",
        "frequent": "Laistīt 3–4× nedēļā, augs mīl mitrumu."
    }.get(level.lower(), "Laistīt, kad augsnes virskārta sāk izžūt.")

def explain_sunlight(text):
    t = text.lower()
    if "full sun" in t:
        return "Tieša saule (6–8 h dienā), piemērots dienvidu logiem."
    if "part" in t:
        return "Daļēja saule – gaiša vieta bez pusdienas saules."
    if "shade" in t:
        return "Pusēna vai ēna – tikai netieša gaisma."
    return "Gaiša vieta ar izkliedētu dienasgaismu."

def explain_temperature(watering):
    if watering in ["frequent", "average", "moderate"]:
        return "Optimālā temperatūra: 18–26 °C"
    return "Optimālā temperatūra: 15–24 °C"

# ================== PERENUAL ==================
def get_perenual(scientific):
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
    for w in root.winfo_children():
        w.destroy()

    tk.Label(root, text="Lietotājvārds").pack()
    u = tk.Entry(root); u.pack()

    tk.Label(root, text="Parole").pack()
    p = tk.Entry(root, show="*"); p.pack()

    msg = tk.Label(root); msg.pack()

    def do_login():
        global current_user
        uid = login(u.get(), p.get())
        if uid:
            current_user = uid
            show_main()
        else:
            msg.config(text="❌ Nepareizi dati")

    def do_register():
        if register(u.get(), p.get()):
            msg.config(text="✅ Reģistrēts! Tagad pieslēdzies.")
        else:
            msg.config(text="⚠️ Lietotājs jau eksistē")

    tk.Button(root, text="Pieslēgties", command=do_login).pack()
    tk.Button(root, text="Reģistrēties", command=do_register).pack()

# ================== MAIN ==================
def show_main():
    for w in root.winfo_children():
        w.destroy()

    global result, img_label

    top = tk.Frame(root)
    top.pack(pady=5)

    tk.Button(top, text="📷 Atpazīt no bildes", command=start_identify).pack(side="left")
    tk.Button(top, text="➕ Saglabāt", command=save_current).pack(side="left")
    tk.Button(top, text="📚 Mana bibliotēka", command=show_library).pack(side="left")

    search = tk.Frame(root)
    search.pack(pady=5)

    tk.Label(search, text="🔎 Meklēt augu pēc nosaukuma:").pack(side="left")
    entry = tk.Entry(search, width=30)
    entry.pack(side="left", padx=5)
    tk.Button(search, text="Meklēt", command=lambda: search_by_name(entry.get())).pack(side="left")

    img_label = tk.Label(root)
    img_label.pack()

    result = tk.Text(root, width=85, height=26)
    result.pack()

# ================== IMAGE IDENTIFY ==================
def start_identify():
    path = filedialog.askopenfilename()
    if not path:
        return

    img = Image.open(path).resize((300, 300))
    img_label.image = ImageTk.PhotoImage(img)
    img_label.config(image=img_label.image)

    result.delete("1.0", tk.END)
    result.insert(tk.END, "🔍 Atpazīst augu...\n")

    threading.Thread(target=identify_worker, args=(path,), daemon=True).start()

def identify_worker(path):
    try:
        res = api.identify(path)
        best = max(res.result.classification.suggestions, key=lambda x: x.probability)

        sci = normalize_scientific_name(best.name)

        latest_plant.clear()
        latest_plant["name"] = sci
        latest_plant["scientific"] = sci

        if get_perenual(sci):
            root.after(0, show_output)

    except Exception as e:
        root.after(0, show_error, e)

# ================== SEARCH BY NAME ==================
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
            root.after(0, lambda: result.insert(tk.END, "❌ Augs nav atrasts."))
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

# ================== OUTPUT ==================
def show_output():
    result.delete("1.0", tk.END)
    result.insert(
        tk.END,
        f"""
🌱 Nosaukums: {latest_plant['name']}
🔬 Zinātniskais nosaukums: {latest_plant['scientific']}

💧 Laistīšana:
{latest_plant['watering']}

☀️ Apgaismojums:
{latest_plant['sunlight']}

🌡️ Temperatūra:
{latest_plant['temperature']}

📖 Apraksts:
{latest_plant['desc']}
"""
    )

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

# ================== LIBRARY ==================
def confirm_delete(sci, name):
    if messagebox.askyesno("Dzēst", f"Vai dzēst {name}?"):
        delete_plant(current_user, sci)
        show_library()

def show_library():
    result.delete("1.0", tk.END)
    plants = get_user_plants(current_user)

    if not plants:
        result.insert(tk.END, "📭 Bibliotēka ir tukša")
        return

    frame = tk.Frame(result)
    result.window_create(tk.END, window=frame)

    for name, sci, water, light in plants:
        row = tk.Frame(frame, pady=5)
        row.pack(fill="x")

        tk.Label(
            row,
            text=f"🌱 {name}\n💧 {water}\n☀️ {light}",
            justify="left",
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

        tk.Button(
            row,
            text="🗑 Dzēst",
            command=lambda s=sci, n=name: confirm_delete(s, n)
        ).pack(side="right")

# ================== START ==================
root = tk.Tk()
root.title("EasyCare 🌿")
show_login()
root.mainloop()
