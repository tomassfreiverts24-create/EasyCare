import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from kindwise import PlantApi
import requests
import urllib.parse
import threading


from Registracija import set_database

set_database("database.db")

from Registracija import (
    login, register, save_plant, get_user_plants, delete_plant
)

# ================== API KEYS ==================
api = PlantApi("GcPNebO8G8ItSZ0OJNJZfyvpTylhpMjoqN4gvxS9BhZJSGnDOL")
PERENUAL_KEY = "sk-7kCh69b7f944cffbd15498"

current_user = None
latest_plant = {}

# ================== NATURE GREEN PALETE ==================
BG_MAIN = "#E8F3EC"      # dabīgs gaiši zaļš
CARD_BG = "#FFFFFF"
CARD_BORDER = "#C7DED1"
ACCENT = "#3A7F5C"
TEXT_MAIN = "#2E2E2E"

# ================== NORMALIZĀCIJA ==================
def normalize_scientific_name(value):
    if not value:
        return ""
    if isinstance(value, list):
        value = value[0]
    value = str(value).split("(")[0].strip()
    parts = value.split()
    if len(parts) >= 2:
        return f"{parts[0].capitalize()} {parts[1].lower()}"
    return value.capitalize()

# ================== TULKOŠANA ==================
def translate_to_lv(text):
    try:
        r = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client":"gtx","sl":"en","tl":"lv","dt":"t","q":text},
            timeout=10
        )
        return "".join(x[0] for x in r.json()[0])
    except:
        return text

# ================== SKAIDROJUMI ==================
def explain_watering(level):
    return {
        "minimum": "Laistīt 1× ik pēc 10–14 dienām.",
        "low": "Laistīt 1× nedēļā.",
        "average": "Laistīt 2× nedēļā.",
        "moderate": "Laistīt 2–3× nedēļā.",
        "frequent": "Laistīt 3–4× nedēļā."
    }.get(level.lower(), "Laistīt, kad augsnes virskārta izžūst.")

def explain_sunlight(text):
    t = text.lower()
    if "full" in t:
        return "Tieša saule (6–8 h dienā)."
    if "part" in t:
        return "Daļēja saule – gaiša vieta bez pusdienas stariem."
    if "shade" in t:
        return "Pusēna – netieša gaisma."
    return "Gaiša vieta ar izkliedētu gaismu."

def explain_temperature(watering):
    if watering in ["frequent", "average", "moderate"]:
        return "Optimāli: 18–26 °C"
    return "Optimāli: 15–24 °C"

# ================== PROGRESS BAR ==================
def progress_start():
    progress["value"] = 0
    root.update_idletasks()

def progress_set(val):
    progress["value"] = val
    root.update_idletasks()

def progress_done():
    progress["value"] = 100
    root.after(400, lambda: progress.config(value=0))

# ================== PERENUAL ==================
def get_perenual(scientific):
    progress_set(40)
    q = urllib.parse.quote(scientific)
    data = requests.get(
        f"https://perenual.com/api/v2/species-list?key={PERENUAL_KEY}&q={q}",
        timeout=15
    ).json()

    if not data.get("data"):
        return False

    pid = data["data"][0]["id"]
    progress_set(65)

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
        "desc": translate_to_lv(details.get("description",""))
    })

    return True

# ================== PLANT CARD ==================
def plant_card(parent):
    card = tk.Frame(
        parent, bg=CARD_BG,
        highlightbackground=CARD_BORDER,
        highlightthickness=1,
        padx=12, pady=10
    )
    card.pack(fill="x", pady=10)

    tk.Label(card, text=latest_plant["name"],
             bg=CARD_BG, fg=ACCENT,
             font=("Segoe UI", 14, "bold")).pack(anchor="w")

    tk.Label(card, text=latest_plant["scientific"],
             bg=CARD_BG, fg="#666",
             font=("Segoe UI", 10, "italic")).pack(anchor="w")

    tk.Label(card, text=f"💧 {latest_plant['watering']}",
             bg=CARD_BG, fg=TEXT_MAIN).pack(anchor="w", pady=(6,0))
    tk.Label(card, text=f"☀️ {latest_plant['sunlight']}",
             bg=CARD_BG, fg=TEXT_MAIN).pack(anchor="w")
    tk.Label(card, text=f"🌡️ {latest_plant['temperature']}",
             bg=CARD_BG, fg=TEXT_MAIN).pack(anchor="w")

    tk.Label(card, text="📖 Apraksts:",
             bg=CARD_BG, font=("Segoe UI",10,"bold")).pack(anchor="w", pady=(6,0))
    tk.Label(card, text=latest_plant["desc"],
             bg=CARD_BG, fg=TEXT_MAIN,
             wraplength=760, justify="left").pack(anchor="w")

# ================== AUTOCOMPLETE ==================
class AutocompleteEntry(tk.Entry):
    def __init__(self, parent, callback):
        super().__init__(parent, width=30)
        self.callback = callback
        self.listbox = None
        self.bind("<KeyRelease>", self.key)

    def key(self, event):
        txt = self.get()
        if len(txt) < 3:
            self.hide()
            return
        q = urllib.parse.quote(txt)
        try:
            data = requests.get(
                f"https://perenual.com/api/v2/species-list?key={PERENUAL_KEY}&q={q}",
                timeout=6
            ).json()
            items = [
                normalize_scientific_name(p.get("scientific_name"))
                for p in data.get("data", [])[:6]
            ]
            self.show(items)
        except:
            self.hide()

    def show(self, items):
        if not self.listbox:
            self.listbox = tk.Listbox(height=6)
            self.listbox.place(x=self.winfo_x(), y=self.winfo_y()+25)
            self.listbox.bind("<<ListboxSelect>>", self.pick)
        self.listbox.delete(0, tk.END)
        for i in items:
            self.listbox.insert(tk.END, i)

    def hide(self):
        if self.listbox:
            self.listbox.destroy()
            self.listbox = None

    def pick(self, event):
        val = self.listbox.get(self.listbox.curselection())
        self.delete(0, tk.END)
        self.insert(0, val)
        self.hide()
        self.callback(val)

# ================== LOGIN ==================
def show_login():
    for w in root.winfo_children():
        w.destroy()
    root.configure(bg=BG_MAIN)

    tk.Label(root, text="Lietotājvārds", bg=BG_MAIN).pack()
    u = tk.Entry(root); u.pack()
    tk.Label(root, text="Parole", bg=BG_MAIN).pack()
    p = tk.Entry(root, show="*"); p.pack()
    msg = tk.Label(root, bg=BG_MAIN); msg.pack()

    def do_login():
        global current_user
        current_user = login(u.get(), p.get())
        show_main() if current_user else msg.config(text="❌ Nepareizi dati")

    def do_register():
        msg.config(text="✅ Reģistrēts" if register(u.get(), p.get()) else "⚠️ Jau eksistē")

    tk.Button(root, text="Pieslēgties", command=do_login).pack()
    tk.Button(root, text="Reģistrēties", command=do_register).pack()

# ================== MAIN ==================
def show_main():
    for w in root.winfo_children():
        w.destroy()
    root.configure(bg=BG_MAIN)

    global result, img_label, progress

    top = tk.Frame(root, bg=BG_MAIN); top.pack(pady=5)
    tk.Button(top, text="📷 Bilde", command=start_identify).pack(side="left", padx=5)
    tk.Button(top, text="➕ Saglabāt", command=save_current).pack(side="left", padx=5)
    tk.Button(top, text="📚 Bibliotēka", command=show_library).pack(side="left", padx=5)

    search = tk.Frame(root, bg=BG_MAIN); search.pack(pady=5)
    tk.Label(search, text="🔎 Meklēt augu:", bg=BG_MAIN).pack(side="left")
    entry = AutocompleteEntry(search, search_by_name)
    entry.pack(side="left", padx=5)

    img_label = tk.Label(root, bg=BG_MAIN); img_label.pack()

    result = tk.Text(root, width=90, height=26,
                     bg=BG_MAIN, borderwidth=0)
    result.pack()

    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Green.Horizontal.TProgressbar",
        troughcolor=BG_MAIN,
        background=ACCENT,
        thickness=12
    )

    progress = ttk.Progressbar(
        root, style="Green.Horizontal.TProgressbar",
        length=420, mode="determinate"
    )
    progress.pack(pady=8)

# ================== ATPAZĪŠANA ==================
def start_identify():
    path = filedialog.askopenfilename()
    if not path:
        return
    progress_start()
    progress_set(10)

    img = Image.open(path).resize((300,300))
    img_label.image = ImageTk.PhotoImage(img)
    img_label.config(image=img_label.image)

    threading.Thread(target=identify_worker, args=(path,), daemon=True).start()

def identify_worker(path):
    try:
        progress_set(30)
        res = api.identify(path)
        best = max(res.result.classification.suggestions, key=lambda x: x.probability)

        sci = normalize_scientific_name(best.name)
        latest_plant.clear()
        latest_plant["name"] = sci
        latest_plant["scientific"] = sci

        if get_perenual(sci):
            progress_set(85)
            root.after(0, show_output)
            root.after(0, progress_done)
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Kļūda", str(e)))
        root.after(0, progress_done)

# ================== SEARCH ==================
def search_by_name(name):
    if not name.strip():
        return
    progress_start()
    progress_set(20)
    threading.Thread(target=search_worker, args=(name,), daemon=True).start()

def search_worker(name):
    try:
        sci = normalize_scientific_name(name)
        latest_plant.clear()
        latest_plant["name"] = sci
        latest_plant["scientific"] = sci

        if get_perenual(sci):
            progress_set(85)
            root.after(0, show_output)
            root.after(0, progress_done)
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Kļūda", str(e)))
        root.after(0, progress_done)

# ================== OUTPUT ==================
def show_output():
    result.delete("1.0", tk.END)
    frame = tk.Frame(result, bg=BG_MAIN)
    result.window_create(tk.END, window=frame)
    plant_card(frame)

# ================== DB ==================
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
    messagebox.showinfo("Saglabāts", "Augs pievienots bibliotēkā 🌱")

def show_library():
    result.delete("1.0", tk.END)
    frame = tk.Frame(result, bg=BG_MAIN)
    result.window_create(tk.END, window=frame)

    for name, sci, water, light in get_user_plants(current_user):
        latest_plant.update({
            "name": name,
            "scientific": sci,
            "watering": water,
            "sunlight": light,
            "temperature": "",
            "desc": ""
        })
        plant_card(frame)

# ================== START ==================
root = tk.Tk()
root.title("EasyCare 🌿")
show_login()
root.mainloop()