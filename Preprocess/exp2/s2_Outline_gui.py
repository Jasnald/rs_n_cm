"""
s2_Outline_gui_simple.py
Visualizador/Editor 2D (YZ) para arquivos JSON gerados em Sample_postprocess.

• Seleção por amostra (Sample1, Sample2…)
• Carrega sempre o arquivo com MAIOR iteração disponível; caso não haja,
  usa o _Average.json.
• Permite apagar pontos clicando e salva como _Modified.json.
"""

import os
import re
import glob
import json
from collections import Counter

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk
)
import tkinter as tk
from tkinter import ttk, messagebox

# --------------------------------------------------------------------------- #
# CONFIGURAÇÕES GERAIS                                                       #
# --------------------------------------------------------------------------- #
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
POST_DIR   = os.path.join(BASE_DIR, "Sample_postprocess")      # pasta fixa
CLICK_THRS = 0.1                                               # tol. p/ apagar
CLICK_PIX_THRESHOLD = 10      # raio de cliques em pixels (~ 10 px)
# --------------------------------------------------------------------------- #
# FUNÇÕES AUXILIARES                                                          #
# --------------------------------------------------------------------------- #
def latest_file_for_sample(sample_folder, sample_name):
    """
    devolve o caminho do arquivo mais recente da amostra:
    …\Sample_<n>\Sample<n>_IterX.json  (X mais alto)
    senão …\Sample_<n>\Sample<n>_Average.json
    """
    iter_files = glob.glob(
        os.path.join(sample_folder, f"{sample_name}_Iter*.json")
    )
    highest_iter = -1
    chosen = None
    for path in iter_files:
        m = re.search(r"_Iter(\d+)\.json$", path, re.IGNORECASE)
        if m:
            it = int(m.group(1))
            if it > highest_iter:
                highest_iter = it
                chosen = path
    if chosen:
        return chosen

    # fallback para Average
    avg_path = os.path.join(sample_folder, f"{sample_name}_Average.json")
    return avg_path if os.path.isfile(avg_path) else None

def find_all_samples():
    """
    varre POST_DIR, encontra pastas Sample_<n> e devolve dict
      { "Sample1": r"...\Sample_1\Sample1_Iter3.json", ... }
    """
    samples = {}
    patt = re.compile(r"Sample_(\d+)$", re.IGNORECASE)
    for folder in os.listdir(POST_DIR):
        full = os.path.join(POST_DIR, folder)
        if not os.path.isdir(full):
            continue
        m = patt.match(folder)
        if not m:
            continue
        num = m.group(1)
        name = f"Sample{num}"
        path = latest_file_for_sample(full, name)
        if path:
            samples[name] = path
    return samples

def predominant_section(points):
    if not points:
        return "Unknown"
    sections = [p.get("section", "Unknown") for p in points]
    return Counter(sections).most_common(1)[0][0]

# --------------------------------------------------------------------------- #
# CLASSE PRINCIPAL                                                            #
# --------------------------------------------------------------------------- #
class PointCloudViewer2D:
    def __init__(self, root):
        self.root = root
        self.root.title("2D Point Cloud Viewer (YZ)")
        self.root.geometry("1100x800")

        # ---- dados --------------------------------------------------------- #
        self.data_by_sample = {}   # {Sample1:{points:…}, …}
        self.current_sample = None

        # ---- layout principal --------------------------------------------- #
        self.main = ttk.Frame(root); self.main.pack(fill="both", expand=True)

        self.left  = ttk.Frame(self.main); self.left.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.right = ttk.Frame(self.main, width=240); self.right.pack(side="right", fill="y", padx=5, pady=5)
        self.right.pack_propagate(False)

        self._setup_figure()
        self._setup_controls()

        # carrega arquivos ao iniciar
        self.load_files()

    # --------------------------------------------------------------------- #
    # FIGURA                                                                #
    # --------------------------------------------------------------------- #
    def _setup_figure(self):
        self.fig, self.ax = plt.subplots(figsize=(9, 8))
        self.ax.set_xlabel("Y"); self.ax.set_ylabel("Z")
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.left)
        self.canvas.draw(); self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.left); self.toolbar.update()

        self.cid = self.fig.canvas.mpl_connect("button_press_event", self.on_click)

    # --------------------------------------------------------------------- #
    # CONTROLES                                                             #
    # --------------------------------------------------------------------- #
    def _setup_controls(self):
        # pasta info
        ttk.Label(self.right, text="Dir:").pack(anchor="w", padx=4, pady=(8,0))
        ttk.Label(self.right, text=POST_DIR, wraplength=220).pack(anchor="w", padx=4)

        ttk.Button(self.right, text="Reload Files", command=self.load_files)\
            .pack(fill="x", padx=5, pady=8)

        # combobox de amostras
        ttk.Label(self.right, text="Sample:").pack(anchor="w", padx=4)
        self.sample_cb = ttk.Combobox(self.right, state="readonly")
        self.sample_cb.pack(fill="x", padx=5, pady=(0,10))
        self.sample_cb.bind("<<ComboboxSelected>>", self.on_sample_selected)

        # info
        sep = ttk.Separator(self.right, orient="horizontal")
        sep.pack(fill="x", padx=5, pady=5)

        self.info_lab = ttk.Label(self.right, text="Points: -")
        self.info_lab.pack(anchor="w", padx=6)

        # opções de cor/tamanho
        disp = ttk.LabelFrame(self.right, text="Display")
        disp.pack(fill="x", padx=5, pady=5)

        self.color_var = tk.StringVar(value="blue")
        ttk.Label(disp, text="Color:").pack(anchor="w", padx=4, pady=(2,0))
        color_options = ["blue", "red", "green", "purple", "orange", "black"]
        self.color_cb = ttk.Combobox(
            disp,
            values=color_options,
            textvariable=self.color_var,
            state="readonly"
        )
        self.color_cb.pack(fill="x", padx=4, pady=(0, 4))
        self.color_cb.bind("<<ComboboxSelected>>", self.update_display)

        self.size_var = tk.DoubleVar(value=1.0)
        ttk.Label(disp, text="Size:").pack(anchor="w", padx=4)
        ttk.Scale(disp, from_=0.2, to=5.0, orient="horizontal",
                  variable=self.size_var, command=self.update_display)\
            .pack(fill="x", padx=4, pady=(0,4))

        self.equal_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(disp, text="Equal aspect", variable=self.equal_var,
                        command=self.update_display)\
            .pack(anchor="w", padx=4, pady=4)

        # salvar
        sep2 = ttk.Separator(self.right, orient="horizontal")
        sep2.pack(fill="x", padx=5, pady=5)

        ttk.Button(self.right, text="Save Modified Data", command=self.save_modified)\
            .pack(fill="x", padx=5, pady=8)

    # --------------------------------------------------------------------- #
    # CARREGAR / SALVAR                                                     #
    # --------------------------------------------------------------------- #
    def load_files(self):
        if not os.path.isdir(POST_DIR):
            os.makedirs(POST_DIR, exist_ok=True)
            messagebox.showinfo("Created", f"Dir criado: {POST_DIR}")
            return

        files = find_all_samples()
        if not files:
            messagebox.showinfo("Info", "Nenhum JSON encontrado.")
            return

        self.data_by_sample.clear()
        errors = []
        for samp, path in files.items():
            try:
                with open(path) as f:
                    data = json.load(f)
                if "points" in data:
                    self.data_by_sample[samp] = data
            except Exception as e:
                errors.append(f"{samp}: {e}")

        self.sample_cb["values"] = list(self.data_by_sample.keys())
        if self.sample_cb["values"]:
            self.sample_cb.current(0)
            self.on_sample_selected(None)

        if errors:
            messagebox.showwarning("Load errors", "\n".join(errors))

    def save_modified(self):
        if self.current_sample is None:
            messagebox.showinfo("Info", "Nada para salvar.")
            return
        samp_name = self.current_sample
        samp_folder = os.path.join(POST_DIR, f"{samp_name.replace('Sample','Sample_')}")
        os.makedirs(samp_folder, exist_ok=True)
        out_path = os.path.join(samp_folder, f"{samp_name}_Modified.json")
        try:
            with open(out_path, "w") as f:
                json.dump(self.data_by_sample[samp_name], f, indent=2)
            messagebox.showinfo("Saved", f"Arquivo salvo:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --------------------------------------------------------------------- #
    # EVENTOS GUI                                                           #
    # --------------------------------------------------------------------- #
    def on_sample_selected(self, _):
        self.current_sample = self.sample_cb.get()
        self.update_display()

    # ------------------------------------------------------------------
    # 2)  Substitua todo o método on_click pelo seguinte:
    # ------------------------------------------------------------------
    def on_click(self, event):
        """
        Remove o ponto MAIS PRÓXIMO ao clique se estiver a menos de
        CLICK_PIX_THRESHOLD pixels.
        """
        # Verificações iniciais
        if (self.current_sample is None or
            event.inaxes != self.ax or
            event.x is None or event.y is None):
            return

        pts = self.data_by_sample[self.current_sample]["points"]
        if not pts:
            return

        # Coordenada do clique em pixels (figura)
        click_px, click_py = event.x, event.y

        # Calcula distância em pixels de cada ponto até ao clique
        distances = []
        for p in pts:
            # transforma coordenadas de dados (y,z) -> pixels
            px, py = self.ax.transData.transform((p["x"], p["y"]))
            distances.append(np.hypot(px - click_px, py - click_py))

        distances = np.array(distances)
        min_idx   = int(np.argmin(distances))
        min_dist  = distances[min_idx]

        if min_dist <= CLICK_PIX_THRESHOLD:
            # apaga UM único ponto
            pts.pop(min_idx)
            self.update_display()
            messagebox.showinfo(
                "Removed",
                f"Removed 1 point (distance {min_dist:.1f}px)."
            )

    # --------------------------------------------------------------------- #
    # PLOT                                                                  #
    # --------------------------------------------------------------------- #
    def update_display(self, *_):
        if self.current_sample is None:
            return
        data = self.data_by_sample[self.current_sample]
        pts  = data.get("points", [])
        if not pts:
            return

        x = [p["x"] for p in pts]
        y = [p["y"] for p in pts]

        self.ax.clear()
        self.ax.scatter(x, y, c=self.color_var.get(),
                        s=self.size_var.get()*20)

        self.ax.set_xlabel("x"); self.ax.set_ylabel("y")
        self.ax.set_title(f"{self.current_sample}  -  {len(pts)} pts")
        self.ax.grid(True)

        if self.equal_var.get():
            self.ax.set_aspect("equal")
        else:
            self.ax.set_aspect("auto")

        self.canvas.draw()
        self.info_lab.config(text=f"Points: {len(pts)}")


# --------------------------------------------------------------------------- #
# MAIN                                                                        #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    root = tk.Tk()
    PointCloudViewer2D(root)
    root.mainloop()