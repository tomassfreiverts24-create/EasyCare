
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
from kindwise import PlantApi
import requests
import urllib.parse
import threading
import traceback

from plant_search import search_plants_by_name, get_plant_care_by_scientific_name
from Registracija import login, register, save_plant, get_user_plants
from online_plant_search import search_plants_online


# ================== API KEYS ==================
api = PlantApi("jMJ0TsKkBoIR3Xvo8sgPhNpcwknJDnTOImc2VwURiJfaYTOcZ9")
PERENUAL_KEY = "sk-7kCh69b7f944cffbd15498"

current_user = None
latest_plant = {}


# ================== TRANSLATE ==================
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
    except Exception:
        return text


# ================== PERENUAL ==================
def get_perenual(scientific):
    q = urllib.parse.quote(scientific)

    try:
        search = requests.get(
            f"https://perenual.com/api/v2/species-list?key={PERENUAL_KEY}&q={q}",
            timeout=15
        ).json()

        if not search.get("data"):
            return "\n❌ Nav datu no Perenual."

        pid = search["data"][0]["id"]

        details = requests.get(
            f"https://perenual.com/api/v2/species/details/{pid}?key={PERENUAL_KEY}",
            timeout=15
        ).json()

    except Exception as e:
        return f"\n❌ Kļūda Perenual API: {e}"

    latest_plant.update({
        "scientific": scientific,
        "watering": details.get("watering", "Nav zināms"),
        "sunlight": ", ".join(details.get("sunlight", [])),
        "desc": details.get("description", "")
    })

    out = "\n=== 🌱 Kopšana ===\n"
    out += f"Laistīšana: {latest_plant['watering']}\n"
    out += f"Gaisma: {translate_to_lv(latest_plant['sunlight'])}\n\n"
    out += translate_to_lv(latest_plant["desc"])

    return out


# ================== PROGRESS ==================
def set_progress(val):
    progress["value"] = val
    root.update_idletasks()


# ================== LOGIN ==================
def show_login():
    for w in root.winfo_children():
        w.destroy()

    tk.Label(root, text="Lietotājvārds").pack()
    u = tk.Entry(root)
    u.pack()

    tk.Label(root, text="Parole").pack()
    p = tk.Entry(root, show="*")
    p.pack()

    msg = tk.Label(root)
    msg.pack()

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

    global result, img_label, progress

    tk.Button(root, text="📷 Izvēlēties augu", command=start_identify).pack()
    tk.Button(root, text="➕ Pievienot bibliotēkai", command=save_current).pack()
    tk.Button(root, text="📚 Mana bibliotēka", command=show_library).pack()

    progress = ttk.Progressbar(root, length=320, maximum=100)
    progress.pack(pady=5)

    img_label = tk.Label(root)
    img_label.pack(pady=5)

    result = tk.Text(root, width=70, height=22)
    result.pack()

    ttk.Button(
        root,
        text="🔍 Meklēt augu datubāzē",
        command=search_in_database
    ).pack(pady=5)


# ================== DB SEARCH ==================
def search_in_database():
    popup = tk.Toplevel(root)
    popup.title("Meklēt augu datubāzē")

    tk.Label(popup, text="Ievadi nosaukuma daļu:").pack()
    entry = tk.Entry(popup)
    entry.pack()

    listbox = tk.Listbox(popup, width=60)
    listbox.pack()

    def do_search():
        listbox.delete(0, tk.END)
        for n, s in search_plants_by_name(entry.get()):
            listbox.insert(tk.END, f"{n} ({s})")
        
        

    def show_selected():
        sel = listbox.curselection()
        if not sel:
            return

        sci = listbox.get(sel[0]).split("(")[-1].replace(")", "")
        plant = get_plant_care_by_scientific_name(sci)
        popup.destroy()

        if plant:
            n, s, w, l, d = plant
            result.delete("1.0", tk.END)
            result.insert(
                tk.END,
                f"{n}\n{s}\n\nLaistīšana: {w}\nGaisma: {l}\n\n{d}"
            )

    ttk.Button(popup, text="Meklēt", command=do_search).pack()
    ttk.Button(popup, text="Parādīt", command=show_selected).pack()


# ================== IDENTIFY (UI) ==================
def start_identify():
    latest_plant.clear()
    set_progress(0)

    path = filedialog.askopenfilename()
    if not path:
        return

    img = Image.open(path).resize((300, 300))
    img_label.image = ImageTk.PhotoImage(img)
    img_label.config(image=img_label.image)

    result.delete("1.0", tk.END)
    result.insert(tk.END, "🔍 Atpazīst augu...\n")
    set_progress(25)

    threading.Thread(
        target=identify_worker,
        args=(path,),
        daemon=True
    ).start()


# ================== IDENTIFY (THREAD) ==================
def identify_worker(path):
    try:
        set_progress(40)

        res = api.identify(path)
        best = max(
            res.result.classification.suggestions,
            key=lambda x: x.probability
        )

        latest_plant["name"] = best.name
        latest_plant["scientific"] = best.name

        set_progress(65)

        care = get_perenual(best.name)

        set_progress(85)

        root.after(0, show_result, best, care)

    except Exception as e:
        root.after(0, show_error, e)


def show_result(best, care):
    result.delete("1.0", tk.END)
    result.insert(
        tk.END,
        f"{best.name}\n"
        f"Varbūtība: {best.probability:.2%}\n"
        f"{care}"
    )
    set_progress(100)


def hybrid_search(query: str):
   
    local_results = search_plants_by_name(query)
    if local_results:
        return "local", local_results

    online_results = search_plants_online(query)
    if online_results:
        return "online", online_results

    return "none", []


def show_error(e):
    result.delete("1.0", tk.END)
    result.insert(tk.END, "❌ Kļūda auga atpazīšanā:\n\n" + str(e))
    traceback.print_exc()
    set_progress(0)


# ================== SAVE ==================
def save_current():
    if not latest_plant:
        return

    save_plant(
        current_user,
        latest_plant["name"],
        latest_plant["scientific"],
        latest_plant.get("watering", ""),
        latest_plant.get("sunlight", ""),
        latest_plant.get("desc", "")
    )

    result.insert(tk.END, "\n✅ Saglabāts bibliotēkā!\n")


# ================== LIBRARY ==================
def show_library():
    result.delete("1.0", tk.END)
    plants = get_user_plants(current_user)

    if not plants:
        result.insert(tk.END, "📭 Bibliotēka ir tukša")
        return

    for p in plants:
        result.insert(
            tk.END,
            f"🌱 {p[0]} ({p[1]})\n"
            f"Laistīšana: {p[2]} | Gaisma: {p[3]}\n\n"
        )


# ================== START ==================
root = tk.Tk()
root.title("EasyCare 🌿")
show_login()
root.mainloop()
