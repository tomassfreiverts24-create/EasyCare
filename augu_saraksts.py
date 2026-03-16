import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
from kindwise import PlantApi

api = PlantApi('jMJ0TsKkBoIR3Xvo8sgPhNpcwknJDnTOImc2VwURiJfaYTOcZ9')

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

    # ======== PARĀDĀM BILDI GUI ========
    img = Image.open(image_path)
    img = img.resize((300, 300))
    img_tk = ImageTk.PhotoImage(img)
    image_label.config(image=img_tk)

    # ======== PARĀDĀM PROGRESS BAR ========
    progress.start()
    show_result("Analizēju attēlu...")

    root.update_idletasks()

    # ======== API PIEPRASĪJUMS ========
    identification = api.identify(image_path, details=['url', 'common_names'])

    progress.stop()

    # ======== APSTRĀDĀM REZULTĀTUS ========
    suggestions = identification.result.classification.suggestions

    # Atrodam maksimālo varbūtību
    max_prob = max(s.probability for s in suggestions)

    # Atlasām tikai tos, kuriem ir max varbūtība
    best_matches = [s for s in suggestions if s.probability == max_prob]

    # ======== FORMATĒJAM IZVADI ========
    output = ""

    output += "Vai tas ir augs: "
    output += "Jā\n\n" if identification.result.is_plant.binary else "Nē\n\n"

    output += "Labākā atbilstība:\n\n"

    for s in best_matches:
        output += f"- {s.name}\n"
        output += f"  Varbūtība: {s.probability:.2%}\n"
        output += f"  URL: {s.details['url']}\n"
        output += f"  Nosaukumi: {s.details['common_names']}\n\n"

        # Aprūpes padomi (nav API, bet vieta nākotnei)
        output += "Aprūpes padomi:\n"
        output += "  (API šobrīd neparedz aprūpes padomus)\n\n"

    show_result(output)


def show_result(text):
    result_box.config(state="normal")
    result_box.delete("1.0", tk.END)
    result_box.insert(tk.END, text)
    result_box.config(state="disabled")


# ======== GUI ========
root = tk.Tk()
root.title("Augu atpazīšana")

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
