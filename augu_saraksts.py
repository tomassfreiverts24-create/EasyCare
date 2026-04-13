
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
from kindwise import PlantApi
import requests
import urllib.parse
from plant_search import search_plants_by_name, get_plant_care_by_scientific_name
from Registracija import login, register, save_plant, get_user_plants


# ================== API KEYS ==================
api = PlantApi("jMJ0TsKkBoIR3Xvo8sgPhNpcwknJDnTOImc2VwURiJfaYTOcZ9")
PERENUAL_KEY = "sk-7kCh69b7f944cffbd15498"

current_user = None
latest_plant = {}


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
            }
        )
        return "".join(x[0] for x in r.json()[0])
    except:
        return text


# ================== PERENUAL ==================
def get_perenual(scientific):
    q = urllib.parse.quote(scientific)

    search = requests.get(
        f"https://perenual.com/api/v2/species-list?key={PERENUAL_KEY}&q={q}"
    ).json()

    if not search.get("data"):
        return "Nav datu no Perenual."

    pid = search["data"][0]["id"]

    details = requests.get(
        f"https://perenual.com/api/v2/species/details/{pid}?key={PERENUAL_KEY}"
    ).json()

    latest_plant.update({
        "scientific": scientific,
        "watering": details.get("watering"),
        "sunlight": ", ".join(details.get("sunlight", [])),
        "desc": details.get("description", "")
    })

    out = "\n=== Kopšana ===\n"
    if details.get("watering"):
        out += f"Laistīšana: {details['watering']}\n"
    if details.get("sunlight"):
        out += f"Gaisma: {translate_to_lv(', '.join(details['sunlight']))}\n"
    if details.get("description"):
        out += "\n" + translate_to_lv(details["description"])

    return out


# ================== PROGRESS ==================
def set_progress(val, text=""):
    progress["value"] = val
    if text:
        result.delete("1.0", tk.END)
        result.insert(tk.END, text)
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
            msg.config(text="Nepareizi dati")

    def do_register():
        if register(u.get(), p.get()):
            msg.config(text="Reģistrēts! Tagad pieslēdzies.")
        else:
            msg.config(text="Lietotājs jau eksistē")

    tk.Button(root, text="Pieslēgties", command=do_login).pack()
    tk.Button(root, text="Reģistrēties", command=do_register).pack()

# ================== datubaze ==================

def search_in_database():
    popup = tk.Toplevel(root)
    popup.title("Meklēt augu datubāzē")

    tk.Label(popup, text="Ievadi auga nosaukumu vai tā daļu:").pack(pady=5)
    entry = tk.Entry(popup, width=30)
    entry.pack(pady=5)

    listbox = tk.Listbox(popup, width=50)
    listbox.pack(pady=5)

    def do_search():
        listbox.delete(0, tk.END)
        query = entry.get().strip()
        if not query:
            return

        results = search_plants_by_name(query)
        for plant_name, scientific_name in results:
            listbox.insert(
                tk.END,
                f"{plant_name} ({scientific_name})"
            )

    def show_selected():
        selection = listbox.curselection()
        if not selection:
            return

        selected_text = listbox.get(selection[0])
        scientific_name = selected_text.split("(")[-1].replace(")", "")

        plant = get_plant_care_by_scientific_name(scientific_name)
        popup.destroy()

        if plant:
            plant_name, sci, watering, sunlight, desc = plant
            result.delete("1.0", tk.END)
            result.insert(
                tk.END,
                f"Augs: {plant_name}\n"
                f"Zinātniskais nosaukums: {sci}\n\n"
                f"Laistīšana: {watering}\n"
                f"Apgaismojums: {sunlight}\n\n"
                f"Apraksts:\n{desc}"
            )

    ttk.Button(popup, text="Meklēt", command=do_search).pack(pady=5)
    ttk.Button(popup, text="Parādīt", command=show_selected).pack(pady=5)
    


# ================== MAIN MENU ==================
def show_main():
    for w in root.winfo_children():
        w.destroy()

    global result, img_label, progress

    tk.Button(root, text="Izvēlēties augu", command=identify).pack()
    tk.Button(root, text="Pievienot bibliotēkai", command=save_current).pack()
    tk.Button(root, text="Mana bibliotēka", command=show_library).pack()

    progress = ttk.Progressbar(
        root, orient="horizontal", length=300, mode="determinate", maximum=100
    )
    progress.pack(pady=5)

    img_label = tk.Label(root)
    img_label.pack()

    result = tk.Text(root, width=65, height=20)
    result.pack()

    ttk.Button(
    root,
    text="Meklēt augu datubāzē",
    command=search_in_database
).pack(pady=5)


# ================== IDENTIFY ==================
def identify():
    latest_plant.clear()
    set_progress(0, "Izvēlies attēlu...")

    path = filedialog.askopenfilename()
    if not path:
        set_progress(0)
        return

    img = Image.open(path).resize((300, 300))
    img_label.image = ImageTk.PhotoImage(img)
    img_label.config(image=img_label.image)
    set_progress(20, "Attēls ielādēts")

    set_progress(40, "Atpazīst augu...")
    res = api.identify(path, details=["common_names"])
    best = max(res.result.classification.suggestions, key=lambda x: x.probability)

    latest_plant["name"] = best.name
    set_progress(65, "Augs noteikts")

    set_progress(80, "Iegūst kopšanas informāciju...")
    care = get_perenual(best.name)

    set_progress(95, "Formatē rezultātu...")
    result.delete("1.0", tk.END)
    result.insert(
        tk.END,
        f"{best.name}\nVarbūtība: {best.probability:.2%}\n{care}"
    )

    set_progress(100, "Gatavs ✅")


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
    result.insert(tk.END, "\n✅ Saglabāts!\n")


# ================== LIBRARY ==================
def show_library():
    result.delete("1.0", tk.END)
    for p in get_user_plants(current_user):
        result.insert(tk.END, f"{p[0]} ({p[1]})\n{p[2]} | {p[3]}\n\n")


# ================== START ==================
root = tk.Tk()
root.title("EasyCare")

show_login()
root.mainloop()
