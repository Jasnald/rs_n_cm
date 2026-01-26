from ..importations import *

class PointCloudViewer:
    """
    GUI for visualizing and editing 2D point cloud data (YZ Plane).
    Adapted for the new exp_process structure.
    """
    def __init__(self, root, input_dir):
        self.root = root
        self.root.title("2D Point Cloud Viewer (YZ Plane)")
        self.root.geometry("1200x800")
        
        self.input_dir = input_dir
        self.data_by_side = {}
        self.current_side = None
        self.current_step = None
        
        self._setup_ui()
        self.load_files()
        
    def _setup_ui(self):
        # Main Layout
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left: Visualization (80%)
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right: Controls (20%)
        self.right_frame = ttk.Frame(self.main_frame, width=240)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False, padx=5, pady=5)
        self.right_frame.pack_propagate(False)

        self._setup_figure()
        self._setup_controls()

    def _setup_figure(self):
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('Y')
        self.ax.set_ylabel('Z')
        self.ax.grid(True)
        
        self.canvas = FigureCanvasTkAgg(self.fig, self.left_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        toolbar_frame = ttk.Frame(self.left_frame)
        toolbar_frame.pack(fill=tk.X)
        NavigationToolbar2Tk(self.canvas, toolbar_frame)

    def _setup_controls(self):
        # Info
        ttk.Label(self.right_frame, text="Directory:").pack(fill=tk.X, pady=(10,0))
        ttk.Label(self.right_frame, text=os.path.basename(self.input_dir)).pack(fill=tk.X, pady=(0,10))
        
        ttk.Button(self.right_frame, text="Reload Files", command=self.load_files).pack(fill=tk.X, pady=5)
        
        # Selection
        ttk.Label(self.right_frame, text="Side:").pack(fill=tk.X, pady=(10,0))
        self.side_combo = ttk.Combobox(self.right_frame, state="readonly")
        self.side_combo.pack(fill=tk.X, pady=(0,10))
        self.side_combo.bind("<<ComboboxSelected>>", self.on_side_selected)
        
        ttk.Label(self.right_frame, text="Step:").pack(fill=tk.X, pady=(10,0))
        self.step_list = tk.Listbox(self.right_frame, height=10)
        self.step_list.pack(fill=tk.BOTH, expand=True, pady=(0,10))
        self.step_list.bind("<<ListboxSelect>>", self.on_step_selected)

        # Options
        self.opt_frame = ttk.LabelFrame(self.right_frame, text="Options")
        self.opt_frame.pack(fill=tk.X, pady=5)
        
        self.color_var = tk.StringVar(value="blue")
        ttk.Combobox(self.opt_frame, values=["blue", "red", "black"], textvariable=self.color_var).pack(fill=tk.X, pady=2)
        
        self.aspect_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.opt_frame, text="Equal Aspect", variable=self.aspect_var, command=self.update_display).pack(fill=tk.X)
        
        self.section_color_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.opt_frame, text="Color by Section", variable=self.section_color_var, command=self.update_display).pack(fill=tk.X)

        # Save
        ttk.Button(self.right_frame, text="Save Modified", command=self.save_data).pack(fill=tk.X, pady=20)

    def load_files(self):
        files = glob.glob(os.path.join(self.input_dir, "*_Steps.json")) + \
                glob.glob(os.path.join(self.input_dir, "*_Cleaned*.json"))
                
        if not files:
            messagebox.showinfo("Info", "No compatible JSON files found.")
            return

        self.data_by_side = {}
        for fpath in files:
            try:
                with open(fpath, 'r') as f:
                    data = json.load(f)
                    side = data.get('side', 'Unknown')
                    # Simple version: keep only latest loaded for that side or logic to find latest iter
                    self.data_by_side[side] = {'data': data, 'path': fpath}
            except Exception:
                continue
        
        self.side_combo['values'] = list(self.data_by_side.keys())
        if self.side_combo['values']:
            self.side_combo.current(0)
            self.on_side_selected(None)

    def on_side_selected(self, event):
        side = self.side_combo.get()
        if side not in self.data_by_side: return
        
        self.current_side = side
        data = self.data_by_side[side]['data']
        self.step_list.delete(0, tk.END)
        
        for i, step in enumerate(data.get('steps', [])):
            count = len(step.get('points', []))
            self.step_list.insert(tk.END, f"Step {i+1} ({count} pts)")
            
        if self.step_list.size() > 0:
            self.step_list.selection_set(0)
            self.on_step_selected(None)

    def on_step_selected(self, event):
        if not self.step_list.curselection(): return
        self.current_step = self.step_list.curselection()[0]
        self.update_display()

    def update_display(self):
        if not self.current_side or self.current_step is None: return
        
        steps = self.data_by_side[self.current_side]['data'].get('steps', [])
        if self.current_step >= len(steps): return
        
        points = steps[self.current_step].get('points', [])
        y = [p['y'] for p in points]
        z = [p['z'] for p in points]
        sections = [p.get('section', 'unknown') for p in points]

        self.ax.clear()
        
        if self.section_color_var.get():
            unique_secs = list(set(sections))
            for sec in unique_secs:
                idxs = [i for i, s in enumerate(sections) if s == sec]
                self.ax.scatter([y[i] for i in idxs], [z[i] for i in idxs], label=sec, s=10)
            self.ax.legend()
        else:
            self.ax.scatter(y, z, c=self.color_var.get(), s=10)

        self.ax.set_aspect('equal' if self.aspect_var.get() else 'auto')
        self.ax.set_xlabel('Y'); self.ax.set_ylabel('Z')
        self.canvas.draw()

    def on_click(self, event):
        if event.inaxes != self.ax or self.current_step is None: return
        
        # Logic to remove points (simplified)
        click_y, click_z = event.xdata, event.ydata
        step = self.data_by_side[self.current_side]['data']['steps'][self.current_step]
        points = step['points']
        
        threshold = 0.2
        # Filter keep points
        new_points = [p for p in points if np.sqrt((p['y']-click_y)**2 + (p['z']-click_z)**2) > threshold]
        
        if len(new_points) < len(points):
            step['points'] = new_points
            self.update_display()

    def save_data(self):
        if not self.current_side: return
        info = self.data_by_side[self.current_side]
        path = info['path'].replace('.json', '_Modified.json')
        with open(path, 'w') as f:
            json.dump(info['data'], f, indent=2)
        messagebox.showinfo("Saved", f"Saved to {os.path.basename(path)}")