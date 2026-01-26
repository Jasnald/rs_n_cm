from ..importations import *

from ..core.fitter import Fitter
class PointCloudViewer:
    def __init__(self, root, input_dir):
        self.root = root
        self.root.title("Editor Interativo de Pontos (Clique para Deletar)")
        self.root.geometry("1200x800")
        
        self.input_dir = input_dir
        self.data_by_side = {}
        self.current_side = None
        self.modified = False # Flag para saber se houve alterações
        
        self._setup_ui()
        self.load_files()
        
    def _setup_ui(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Área do Gráfico ---
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- Controles ---
        self.right_frame = ttk.Frame(self.main_frame, width=280)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False, padx=5, pady=5)
        
        self._setup_figure()
        self._setup_controls()

    def _setup_figure(self):
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('Y (mm)')
        self.ax.set_ylabel('Z (mm)')
        self.ax.grid(True, linestyle='--', alpha=0.6)
        
        self.canvas = FigureCanvasTkAgg(self.fig, self.left_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Conecta o evento de CLIQUE do mouse
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click_delete)
        
        toolbar_frame = ttk.Frame(self.left_frame)
        toolbar_frame.pack(fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

    def _setup_controls(self):
        # Seleção de Arquivo
        ttk.Label(self.right_frame, text="Selecione o Modelo:").pack(fill=tk.X, pady=(10,0))
        self.side_combo = ttk.Combobox(self.right_frame, state="readonly")
        self.side_combo.pack(fill=tk.X, pady=(0,10))
        self.side_combo.bind("<<ComboboxSelected>>", self.on_side_selected)
        
        # Instruções
        inst_frame = ttk.LabelFrame(self.right_frame, text="Como Usar")
        inst_frame.pack(fill=tk.X, pady=5)
        lbl = ttk.Label(inst_frame, text="1. Botão ESQUERDO: Deleta ponto\n2. Botão DIREITO: Restaura último\n(Use o Zoom da barra se precisar)", wraplength=250)
        lbl.pack(padx=5, pady=5)

        # Botões de Ação
        self.btn_recalc = ttk.Button(self.right_frame, text="Recalcular Curva", command=self.recalculate_fit)
        self.btn_recalc.pack(fill=tk.X, pady=(20, 5))
        
        self.btn_save = ttk.Button(self.right_frame, text="Salvar Alterações", command=self.save_changes)
        self.btn_save.pack(fill=tk.X, pady=5)
        
        # Info
        self.info_lbl = ttk.Label(self.right_frame, text="Pontos: -\nGrau: -", wraplength=200)
        self.info_lbl.pack(fill=tk.X, pady=20)

    def load_files(self):
        files = glob.glob(os.path.join(self.input_dir, "*.json"))
        self.data_by_side = {}
        if not files:
            messagebox.showinfo("Aviso", "Nenhum arquivo JSON encontrado.")
            return

        for fpath in files:
            try:
                with open(fpath, 'r') as f:
                    data = json.load(f)
                    key = data.get('side', os.path.basename(fpath))
                    # Guarda backup dos pontos originais para reset se precisar
                    data['_original_points'] = data.get('points', [])
                    self.data_by_side[key] = {'data': data, 'path': fpath}
            except Exception: continue
        
        self.side_combo['values'] = list(self.data_by_side.keys())
        if self.side_combo['values']:
            self.side_combo.current(0)
            self.on_side_selected(None)

    def on_side_selected(self, event):
        self.current_side = self.side_combo.get()
        self.modified = False
        self.update_plot()

    def on_click_delete(self, event):
        """Detecta clique e remove o ponto mais próximo."""
        # Ignora se estiver usando ferramentas de zoom/pan da toolbar
        if self.toolbar.mode != "" or event.inaxes != self.ax: return
        if not self.current_side: return
        
        data_wrapper = self.data_by_side[self.current_side]['data']
        points = np.array(data_wrapper['points'])
        if len(points) == 0: return

        # Coordenadas do clique (Y, Z)
        click_y, click_z = event.xdata, event.ydata
        
        # Calcula distâncias (apenas no plano YZ visualizado)
        # points[:, 1] é Y, points[:, 2] é Z
        dist = np.sqrt((points[:, 1] - click_y)**2 + (points[:, 2] - click_z)**2)
        
        # Encontra o índice do ponto mais próximo
        idx_min = np.argmin(dist)
        min_dist = dist[idx_min]
        
        # Limite de tolerância para deletar (ajuste se necessário)
        TOLERANCE = 1.0 # mm
        
        if min_dist < TOLERANCE:
            # Remove o ponto
            print(f"Deletando ponto índice {idx_min} (dist={min_dist:.2f})")
            new_points = np.delete(points, idx_min, axis=0)
            data_wrapper['points'] = new_points.tolist()
            self.modified = True
            
            # Atualiza apenas o gráfico (não recalcula a curva ainda para ser rápido)
            self.update_plot(recalc=False)

    def recalculate_fit(self):
        """Recalcula o polinômio com os pontos atuais."""
        if not self.current_side: return
        data = self.data_by_side[self.current_side]['data']
        pts = np.array(data['points'])
        degree = data.get('degree', 2)
        
        try:
            # Chama o Fitter estático para recalcular coeficientes
            # Nota: O Fitter espera X, Y, Z.
            new_model = Fitter.fit_2d_poly(pts[:, 0], pts[:, 1], pts[:, 2], degree)
            
            # Atualiza os coeficientes no objeto de dados
            data['coeffs'] = new_model['coeffs']
            data['r_squared'] = new_model['r_squared']
            
            messagebox.showinfo("Sucesso", f"Curva recalculada!\nR²: {new_model['r_squared']:.4f}")
            self.update_plot(recalc=True)
            self.modified = True
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao ajustar: {e}")

    def save_changes(self):
        if not self.current_side: return
        wrapper = self.data_by_side[self.current_side]
        path = wrapper['path']
        
        try:
            with open(path, 'w') as f:
                json.dump(wrapper['data'], f, indent=2) # Removemos o cls NumpyEncoder para simplificar, certifique-se que points é lista
            messagebox.showinfo("Salvo", f"Arquivo atualizado:\n{os.path.basename(path)}")
            self.modified = False
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", str(e))

    def update_plot(self, recalc=True):
        if not self.current_side: return
        data = self.data_by_side[self.current_side]['data']
        
        self.ax.clear()
        self.ax.grid(True, linestyle='--', alpha=0.6)
        
        # 1. Plot Pontos
        pts = np.array(data['points'])
        if len(pts) > 0:
            self.ax.scatter(pts[:, 1], pts[:, 2], s=15, c='blue', alpha=0.6, label='Pontos', picker=True)
        
        # 2. Plot Curva (Se coeficientes existirem)
        if 'coeffs' in data and len(pts) > 0:
            y_min, y_max = pts[:, 1].min(), pts[:, 1].max()
            x_mid = np.mean(pts[:, 0]) # Usa o X médio para o corte 2D
            
            y_line = np.linspace(y_min, y_max, 100)
            x_line = np.full_like(y_line, x_mid)
            
            try:
                z_line = Fitter.eval_2d_poly(x_line, y_line, data)
                self.ax.plot(y_line, z_line, 'r-', linewidth=2, label='Fit Atual')
            except: pass

        self.ax.set_title(f"{self.current_side} (Pontos: {len(pts)})")
        self.ax.set_xlabel('Y (mm)')
        self.ax.set_ylabel('Z (mm)')
        self.ax.legend()
        self.canvas.draw()