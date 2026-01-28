from ..importations import *

from ..core.fitter import Fitter


class PointCloudViewer:
    def __init__(self, root, input_dir):
        self.root = root
        self.root.title("Visualizador e Editor de Dados (YZ)")
        self.root.geometry("1200x800")
        
        self.input_dir = input_dir
        self.data_store = {} 
        self.current_file = None
        self.current_step_idx = None
        self.modified = False
        
        self._setup_ui()
        self.load_files()
        
    def _setup_ui(self):

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

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

        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click_delete)
        
        toolbar_frame = ttk.Frame(self.left_frame)
        toolbar_frame.pack(fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

    def _setup_controls(self):

        ttk.Label(self.right_frame, text="Arquivo / Amostra:").pack(fill=tk.X, pady=(10,0))
        self.file_combo = ttk.Combobox(self.right_frame, state="readonly")
        self.file_combo.pack(fill=tk.X, pady=(0,10))
        self.file_combo.bind("<<ComboboxSelected>>", self.on_file_selected)
        
        ttk.Label(self.right_frame, text="Passos (Steps):").pack(fill=tk.X, pady=(5,0))
        self.step_listbox = tk.Listbox(self.right_frame, height=15)
        self.step_listbox.pack(fill=tk.BOTH, pady=(0, 10), expand=False)
        self.step_listbox.bind("<<ListboxSelect>>", self.on_step_selected)

        inst_frame = ttk.LabelFrame(self.right_frame, text="Instruções")
        inst_frame.pack(fill=tk.X, pady=5)
        lbl = ttk.Label(inst_frame, text="1. Selecione um Passo na lista.\n2. Clique no ponto p/ deletar.", wraplength=250)
        lbl.pack(padx=5, pady=5)

        self.btn_save = ttk.Button(self.right_frame, text="Salvar Alterações", command=self.save_changes)
        self.btn_save.pack(fill=tk.X, pady=10)
        
        self.info_lbl = ttk.Label(self.right_frame, text="Info: -")
        self.info_lbl.pack(fill=tk.X, pady=10)

    def load_files(self):

        files = glob.glob(os.path.join(self.input_dir, "*.json"))
        self.data_store = {}
        
        if not files:
            messagebox.showinfo("Aviso", "Nenhum arquivo JSON encontrado na pasta de saída.")
            return

        for fpath in files:
            try:
                with open(fpath, 'r') as f:
                    data = json.load(f)
                
                fname = os.path.basename(fpath)

                if 'steps' in data and isinstance(data['steps'], list):
                    ftype = 'steps'
                elif 'points' in data and isinstance(data['points'], list):
                    ftype = 'flat'  
                else:
                    ftype = 'model'
                
                self.data_store[fname] = {
                    'data': data,
                    'type': ftype,
                    'path': fpath
                }
            except Exception as e:
                print(f"Erro ao carregar {fpath}: {e}")

        sorted_files = sorted(self.data_store.keys())
        self.file_combo['values'] = sorted_files

        steps_files = [f for f in sorted_files if self.data_store[f]['type'] == 'steps']
        if steps_files:
            self.file_combo.set(steps_files[0])
            self.on_file_selected(None)
        elif sorted_files:
            self.file_combo.current(0)
            self.on_file_selected(None)

    def on_file_selected(self, event):
        self.current_file = self.file_combo.get()
        if not self.current_file: return
        
        info = self.data_store[self.current_file]
        data = info['data']
        ftype = info['type']

        self.step_listbox.delete(0, tk.END)
        
        if ftype == 'steps':
            steps = data.get('steps', [])
            for i, s in enumerate(steps):
                cnt = s.get('point_count', len(s.get('points', [])))
                self.step_listbox.insert(tk.END, f"Passo {i+1} ({cnt} pts)")

            if steps:
                self.step_listbox.selection_set(0)
                self.on_step_selected(None)
            else:
                self.current_step_idx = None
                self.update_plot()
                
        elif ftype == 'flat':

            cnt = len(data.get('points', []))
            self.step_listbox.insert(tk.END, f"Todos os Pontos ({cnt} pts)")
            self.step_listbox.selection_set(0)
            self.on_step_selected(None)
            
        else:
            self.step_listbox.insert(tk.END, "(Apenas Modelo/Coeficientes)")
            self.current_step_idx = None
            self.update_plot()

    def on_step_selected(self, event):
        sel = self.step_listbox.curselection()
        if not sel: return
        self.current_step_idx = sel[0]
        self.update_plot()

    def get_current_points(self):

        if not self.current_file or self.current_step_idx is None:
            return None
            
        info = self.data_store[self.current_file]
        data = info['data']
        ftype = info['type']
        
        if ftype == 'steps':
            steps = data.get('steps', [])
            if self.current_step_idx < len(steps):
                pts = steps[self.current_step_idx].get('points', [])
                return np.array(pts)
        elif ftype == 'flat':
            pts = data.get('points', [])
            return np.array(pts)
            
        return None

    def update_current_points(self, new_points):

        if not self.current_file or self.current_step_idx is None: return
        
        info = self.data_store[self.current_file]
        data = info['data']
        ftype = info['type']
        
        pts_list = new_points.tolist()
        
        if ftype == 'steps':
            data['steps'][self.current_step_idx]['points'] = pts_list
            data['steps'][self.current_step_idx]['point_count'] = len(pts_list)
            
            # Atualiza texto na listbox para refletir a nova contagem
            self.step_listbox.delete(self.current_step_idx)
            self.step_listbox.insert(self.current_step_idx, f"Passo {self.current_step_idx+1} ({len(pts_list)} pts)")
            self.step_listbox.selection_set(self.current_step_idx)
            
        elif ftype == 'flat':
            data['points'] = pts_list
            self.step_listbox.delete(0)
            self.step_listbox.insert(0, f"Todos os Pontos ({len(pts_list)} pts)")
            self.step_listbox.selection_set(0)

    def update_plot(self):
        self.ax.clear()
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.ax.set_xlabel('Y (mm)')
        self.ax.set_ylabel('Z (mm)')
        
        if not self.current_file:
            self.canvas.draw()
            return
            
        info = self.data_store[self.current_file]
        
        pts = self.get_current_points()
        has_points = False
        
        if pts is not None and pts.size > 0:
            if pts.shape[1] >= 3:

                self.ax.scatter(pts[:, 1], pts[:, 2], s=20, c='blue', alpha=0.7, label='Pontos', picker=5)
                has_points = True
                
                # Ajuste automático de limites com margem
                ymin, ymax = pts[:, 1].min(), pts[:, 1].max()
                zmin, zmax = pts[:, 2].min(), pts[:, 2].max()
                ymarg, zmarg = (ymax-ymin)*0.1, (zmax-zmin)*0.1
                if ymarg==0: ymarg=1
                if zmarg==0: zmarg=0.1
                self.ax.set_xlim(ymin-ymarg, ymax+ymarg)
                self.ax.set_ylim(zmin-zmarg, zmax+zmarg)

        data = info['data']
        if 'coeffs' in data:
            try:
                xlims = self.ax.get_xlim()
                y_line = np.linspace(xlims[0], xlims[1], 100)
                x_mid = 0 if pts is None else np.mean(pts[:, 0])
                x_line = np.full_like(y_line, x_mid)
                
                z_line = Fitter.eval_2d_poly(x_line, y_line, data)
                self.ax.plot(y_line, z_line, 'r-', lw=2, label='Fit Global')
                has_points = True
            except: pass

        if has_points:
            self.ax.legend()
        
        self.ax.set_title(f"{self.current_file}")
        self.canvas.draw()
        
        txt = f"Tipo: {info['type']}"
        if pts is not None: txt += f" | Pts no Passo: {len(pts)}"
        self.info_lbl.config(text=txt)

    def on_click_delete(self, event):

        if self.toolbar.mode != "" or event.inaxes != self.ax: return
        
        pts = self.get_current_points()
        if pts is None or len(pts) == 0: return
        
        click_y, click_z = event.xdata, event.ydata
        
        dist = np.sqrt((pts[:, 1] - click_y)**2 + (pts[:, 2] - click_z)**2)
        idx_min = np.argmin(dist)
        min_dist = dist[idx_min]

        if min_dist < 1.0:
            new_pts = np.delete(pts, idx_min, axis=0)
            self.update_current_points(new_pts)
            self.modified = True
            self.update_plot()
            print(f"Ponto deletado. Restam {len(new_pts)}.")

    def save_changes(self):
        if not self.current_file: return
        info = self.data_store[self.current_file]
        
        try:
            with open(info['path'], 'w') as f:
                json.dump(info['data'], f, indent=2)
            messagebox.showinfo("Salvo", f"Arquivo salvo com sucesso:\n{self.current_file}")
            self.modified = False
        except Exception as e:
            messagebox.showerror("Erro", str(e))