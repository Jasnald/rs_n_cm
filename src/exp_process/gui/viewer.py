from ..importations import *

from ..core.fitter import Fitter

class PointCloudViewer:
    def __init__(self, root, input_dir):
        self.root = root
        self.root.title("Visualizador de Resultados (Pontos + Polinômio)")
        self.root.geometry("1200x800")
        
        self.input_dir = input_dir
        self.data_by_side = {}
        self.current_side = None
        
        self._setup_ui()
        self.load_files()
        
    def _setup_ui(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Área do Gráfico
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Controles
        self.right_frame = ttk.Frame(self.main_frame, width=250)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False, padx=5, pady=5)
        
        self._setup_figure()
        self._setup_controls()

    def _setup_figure(self):
        # Cria figura 3D para suportar visualização de superfície se necessário
        # Mas como seu plot original era 2D (YZ), vamos manter 2D mas preparar o terreno
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111) # Visualização YZ padrão
        self.ax.set_xlabel('Y (mm)')
        self.ax.set_ylabel('Z (mm)')
        self.ax.grid(True, linestyle='--', alpha=0.6)
        
        self.canvas = FigureCanvasTkAgg(self.fig, self.left_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar_frame = ttk.Frame(self.left_frame)
        toolbar_frame.pack(fill=tk.X)
        NavigationToolbar2Tk(self.canvas, toolbar_frame)

    def _setup_controls(self):
        ttk.Label(self.right_frame, text="Arquivos (JSON):").pack(fill=tk.X, pady=(10,0))
        self.side_combo = ttk.Combobox(self.right_frame, state="readonly")
        self.side_combo.pack(fill=tk.X, pady=(0,10))
        self.side_combo.bind("<<ComboboxSelected>>", self.on_side_selected)
        
        # Opções de Visualização
        self.opt_frame = ttk.LabelFrame(self.right_frame, text="Visualização")
        self.opt_frame.pack(fill=tk.X, pady=5)
        
        self.show_poly = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.opt_frame, text="Mostrar Polinômio (Fit)", variable=self.show_poly, command=self.update_display).pack(fill=tk.X)
        
        self.aspect_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.opt_frame, text="Aspecto Igual (Escala)", variable=self.aspect_var, command=self.update_display).pack(fill=tk.X)

        self.info_lbl = ttk.Label(self.right_frame, text="Info: -", wraplength=200)
        self.info_lbl.pack(fill=tk.X, pady=20)

        ttk.Button(self.right_frame, text="Recarregar", command=self.load_files).pack(fill=tk.X, pady=20)

    def load_files(self):
        # Carrega arquivos JSON gerados pelo exp_process_run
        files = glob.glob(os.path.join(self.input_dir, "*.json"))
        
        self.data_by_side = {}
        if not files:
            messagebox.showinfo("Aviso", "Nenhum arquivo JSON encontrado na pasta output.")
            return

        for fpath in files:
            try:
                with open(fpath, 'r') as f:
                    data = json.load(f)
                    # Usa o nome do arquivo como chave se 'side' não existir
                    key = data.get('side', os.path.basename(fpath).replace('.json', ''))
                    self.data_by_side[key] = data
            except Exception as e:
                print(f"Erro ao ler {fpath}: {e}")
        
        self.side_combo['values'] = list(self.data_by_side.keys())
        if self.side_combo['values']:
            self.side_combo.current(0)
            self.on_side_selected(None)

    def on_side_selected(self, event):
        self.current_side = self.side_combo.get()
        self.update_display()

    def update_display(self):
        if not self.current_side: return
        
        data = self.data_by_side[self.current_side]
        self.ax.clear()
        self.ax.grid(True, linestyle='--', alpha=0.6)
        
        # 1. Desenhar Pontos (se existirem)
        if 'points' in data:
            pts = np.array(data['points'])
            # Assumindo formato [x, y, z] -> Plotando Y vs Z (visão lateral)
            # Se quiser X vs Z, mude para pts[:,0]
            self.ax.scatter(pts[:, 1], pts[:, 2], s=5, c='blue', alpha=0.5, label='Dados Brutos')
            
            # Atualiza Info
            self.info_lbl.config(text=f"Pontos: {len(pts)}\nGrau: {data.get('degree', '-')}")
        
        # 2. Desenhar Polinômio (Se ativado e coeficientes existirem)
        if self.show_poly.get() and 'coeffs' in data and 'points' in data:
            pts = np.array(data['points'])
            
            # Cria um grid baseado na extensão dos dados reais
            y_min, y_max = pts[:, 1].min(), pts[:, 1].max()
            x_min, x_max = pts[:, 0].min(), pts[:, 0].max() # O polinômio 2D precisa de X também
            
            # Gera linha de visualização no centro do X (corte transversal)
            # Ou projeta a curva
            
            # Vamos gerar uma linha suave em Y fixando X na média (apenas para visualização 2D)
            y_line = np.linspace(y_min, y_max, 100)
            x_line = np.full_like(y_line, (x_min + x_max)/2) 
            
            # Avalia Z usando o Fitter
            try:
                z_line = Fitter.eval_2d_poly(x_line, y_line, data)
                self.ax.plot(y_line, z_line, 'r-', linewidth=2, label='Fit (X médio)')
            except Exception as e:
                print(f"Erro ao plotar curva: {e}")

        if self.aspect_var.get():
            self.ax.set_aspect('equal')
        else:
            self.ax.set_aspect('auto')
            
        self.ax.set_xlabel('Y (mm)')
        self.ax.set_ylabel('Z (mm)')
        self.ax.legend()
        self.canvas.draw()