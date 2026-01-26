"""
s2_Outline_gui.py
What it does:
This script provides a graphical user interface (GUI) for visualizing and editing 2D point cloud data (YZ plane) from JSON files. It allows users to interactively view, select, remove, and recolor points, as well as save modified data. The interface is built with Tkinter and Matplotlib, supporting multiple sides and steps, and includes options for coloring by section, adjusting point size, and maintaining equal aspect ratio.

Example of use:
    Run this script directly to launch the 2D point cloud viewer for files in the 'Sample_postprocess' directory.

    python Outline_gui.py
"""
import os
import glob
import re
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from collections import Counter

class PointCloudViewer2D:
    """
    PointCloudViewer2D / (class)
    What it does:
    Provides a Tkinter-based GUI for visualizing, editing, and saving 2D point cloud data by side and step. Supports interactive point removal, color and size adjustments, and section-based coloring.
    """
    def __init__(self, root):
        """
        __init__ / (method)
        What it does:
        Initializes the GUI, sets up frames, loads data, and prepares the visualization and control panels.
        """
        self.root = root
        self.root.title("2D Point Cloud Viewer (YZ Plane)")
        self.root.geometry("1200x800")
        
        # Fixed directory setup
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_dir = os.path.join(self.base_dir, "Sample_postprocess")
        
        # Data storage
        self.data_by_side = {}  # Will store full data by side
        self.current_side = None
        self.current_step = None
        
        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create left frame for visualization (80% width)
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create right frame for controls (20% width)
        self.right_frame = ttk.Frame(self.main_frame, width=240)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False, padx=5, pady=5)
        self.right_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        # Setup the 2D figure
        self.setup_figure()
        
        # Setup the control panel
        self.setup_controls()
        
        # Automatically load files on startup
        self.load_files()
        
    def setup_figure(self):
        """
        setup_figure / (method)
        What it does:
        Sets up the 2D Matplotlib figure and canvas for displaying the point cloud, including toolbar and event bindings.
        """
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('Y')
        self.ax.set_ylabel('Z')
        self.ax.set_title('2D Point Cloud (YZ Plane)')
        self.ax.grid(True)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.left_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Connect click event
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Add toolbar
        self.toolbar_frame = ttk.Frame(self.left_frame)
        self.toolbar_frame.pack(fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

    def on_click(self, event):
        """
        on_click / (method)
        What it does:
        Handles mouse click events on the plot, allowing users to remove points near the clicked location and update the visualization.
        """
        if (self.current_side is None or 
            self.current_step is None or 
            self.current_side not in self.data_by_side or
            event.inaxes != self.ax):
            return
        
        # Get click coordinates
        click_y = event.xdata
        click_z = event.ydata
        
        # Get current step data
        steps = self.data_by_side[self.current_side].get("steps", [])
        if self.current_step >= len(steps):
            return
            
        step = steps[self.current_step]
        points = step.get("points", [])
        
        # Find closest point(s)
        threshold = 0.1  # Distance threshold for clicking
        points_to_remove = []
        
        for i, point in enumerate(points):
            y = point.get("y", 0)
            z = point.get("z", 0)
            
            # Calculate distance between click and point
            distance = np.sqrt((y - click_y)**2 + (z - click_z)**2)
            
            if distance < threshold:
                points_to_remove.append(i)
        
        # Remove points (in reverse order to avoid index issues)
        if points_to_remove:
            for idx in sorted(points_to_remove, reverse=True):
                del points[idx]
            
            # Update data
            step["points"] = points
            step["point_count"] = len(points)
            
            # Update visualization
            self.update_display()
            
            # Show message
            messagebox.showinfo("Points Removed", f"Removed {len(points_to_remove)} point(s).")
        
    def setup_controls(self):
        """
        setup_controls / (method)
        What it does:
        Sets up the control panel on the right side of the GUI, including directory info, file loading, side/step selection, display options, and save functionality.
        """
        # Directory info label
        ttk.Label(self.right_frame, text="Working Directory:").pack(fill=tk.X, padx=5, pady=(10, 0))
        self.dir_label = ttk.Label(self.right_frame, text=self.input_dir, wraplength=220)
        self.dir_label.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Load files button
        self.load_btn = ttk.Button(self.right_frame, text="Reload Files", command=self.load_files)
        self.load_btn.pack(fill=tk.X, padx=5, pady=5)
        
        # Side selection
        ttk.Label(self.right_frame, text="Side:").pack(fill=tk.X, padx=5, pady=(10, 0))
        self.side_combobox = ttk.Combobox(self.right_frame, state="readonly")
        self.side_combobox.pack(fill=tk.X, padx=5, pady=(0, 10))
        self.side_combobox.bind("<<ComboboxSelected>>", self.on_side_selected)
        
        # Step selection
        ttk.Label(self.right_frame, text="Step:").pack(fill=tk.X, padx=5, pady=(10, 0))
        self.step_listbox = tk.Listbox(self.right_frame, height=10)
        self.step_listbox.pack(fill=tk.BOTH, padx=5, pady=(0, 10), expand=True)
        self.step_listbox.bind("<<ListboxSelect>>", self.on_step_selected)
        
        # Point cloud info
        ttk.Separator(self.right_frame, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        
        self.info_frame = ttk.LabelFrame(self.right_frame, text="Point Cloud Info")
        self.info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.points_label = ttk.Label(self.info_frame, text="Points: N/A")
        self.points_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.section_label = ttk.Label(self.info_frame, text="Section: N/A")
        self.section_label.pack(fill=tk.X, padx=5, pady=2)
        
        # Color controls
        ttk.Separator(self.right_frame, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        
        self.color_frame = ttk.LabelFrame(self.right_frame, text="Display Options")
        self.color_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.color_var = tk.StringVar(value="blue")
        ttk.Label(self.color_frame, text="Point Color:").pack(fill=tk.X, padx=5, pady=(5, 0))
        
        colors = ["blue", "red", "green", "purple", "orange", "black"]
        self.color_combobox = ttk.Combobox(self.color_frame, values=colors, textvariable=self.color_var)
        self.color_combobox.pack(fill=tk.X, padx=5, pady=(0, 5))
        self.color_combobox.bind("<<ComboboxSelected>>", self.update_display)
        
        self.point_size_var = tk.DoubleVar(value=1.0)
        ttk.Label(self.color_frame, text="Point Size:").pack(fill=tk.X, padx=5, pady=(5, 0))
        
        self.point_size_slider = ttk.Scale(self.color_frame, from_=0.1, to=5.0, orient=tk.HORIZONTAL, 
                                          variable=self.point_size_var, command=self.update_display)
        self.point_size_slider.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Equal aspect ratio checkbox
        self.equal_aspect_var = tk.BooleanVar(value=False)
        self.equal_aspect_check = ttk.Checkbutton(self.color_frame, text="Equal Aspect Ratio", 
                                                variable=self.equal_aspect_var, command=self.update_display)
        self.equal_aspect_check.pack(fill=tk.X, padx=5, pady=5)
        
        # Color by section checkbox
        self.color_by_section_var = tk.BooleanVar(value=False)
        self.color_by_section_check = ttk.Checkbutton(self.color_frame, text="Color by Section", 
                                                    variable=self.color_by_section_var, command=self.update_display)
        self.color_by_section_check.pack(fill=tk.X, padx=5, pady=5)
        
        # Save button
        ttk.Separator(self.right_frame, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        
        self.save_btn = ttk.Button(self.right_frame, text="Save Modified Data", command=self.save_modified_data)
        self.save_btn.pack(fill=tk.X, padx=5, pady=10)

    def save_modified_data(self):
        """
        save_modified_data / (method)
        What it does:
        Saves the currently modified point cloud data for the selected side to a new JSON file in the input directory.
        """
        if not self.data_by_side or not self.current_side:
            messagebox.showinfo("Info", "No data loaded to save.")
            return
        
        # Create a filename in the sample_postprocess directory
        filename = f"{self.current_side}_Modified.json"
        filepath = os.path.join(self.input_dir, filename)
        
        # Save data
        try:
            with open(filepath, 'w') as f:
                json.dump(self.data_by_side[self.current_side], f, indent=2)
            messagebox.showinfo("Success", f"Data saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")
    
    def load_files(self):
        """
        load_files / (method)
        What it does:
        Loads the latest iteration JSON files for each side from the input directory, updating the GUI with available data.
        """
        if not os.path.isdir(self.input_dir):
            try:
                os.makedirs(self.input_dir)
                messagebox.showinfo("Directory Created", f"Created directory: {self.input_dir}\nPlease place JSON files there.")
                return
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create directory: {str(e)}")
                return
        
        # Find latest iteration files
        files_dict = find_latest_iteration_files(self.input_dir)
        if not files_dict:
            messagebox.showinfo("Info", f"No matching files found in:\n{self.input_dir}")
            return
        
        # Load data from each file
        self.data_by_side = {}
        for side, file_path in files_dict.items():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                self.data_by_side[side] = data
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load {file_path}: {str(e)}")
        
        # Update side combobox
        self.side_combobox['values'] = list(self.data_by_side.keys())
        if self.side_combobox['values']:
            self.side_combobox.current(0)
            self.on_side_selected(None)  # Simulate selection event
            messagebox.showinfo("Success", f"Loaded data from {len(self.data_by_side)} files.")
        else:
            messagebox.showinfo("Info", "No valid data found in the files.")
    
    def get_predominant_section(self, points):
        """
        get_predominant_section / (method)
        What it does:
        Determines the most common section label among a list of points, used for display and coloring purposes.
        """
        if not points:
            return "Unknown"
            
        # Extract all sections
        sections = [p.get("section", "Unknown") for p in points]
        
        # Count occurrences
        section_counter = Counter(sections)
        
        # Get most common section
        if section_counter:
            return section_counter.most_common(1)[0][0]
        return "Unknown"
        
    def on_side_selected(self, event):
        """
        on_side_selected / (method)
        What it does:
        Handles the event when a side is selected in the GUI, updating the step list and triggering display updates.
        """
        self.current_side = self.side_combobox.get()
        if not self.current_side or self.current_side not in self.data_by_side:
            return
        
        # Clear and update step listbox
        self.step_listbox.delete(0, tk.END)
        steps = self.data_by_side[self.current_side].get("steps", [])
        for i, step in enumerate(steps):
            step_num = step.get("step_number", i+1)
            points = step.get("points", [])
            points_count = len(points)
            
            # Get predominant section
            predominant_section = self.get_predominant_section(points)
            
            # Add to listbox
            self.step_listbox.insert(tk.END, f"Step {step_num} - {predominant_section} ({points_count} pts)")
        
        # Select first step if available
        if self.step_listbox.size() > 0:
            self.step_listbox.selection_set(0)
            self.on_step_selected(None)  # Simulate selection event
    
    def on_step_selected(self, event):
        """
        on_step_selected / (method)
        What it does:
        Handles the event when a step is selected in the GUI, updating the current step and refreshing the display.
        """
        if not self.step_listbox.curselection():
            return
            
        selected_idx = self.step_listbox.curselection()[0]
        self.current_step = selected_idx
        
        # Display the selected step's points
        self.update_display()
    
    def update_display(self, *args):
        """
        update_display / (method)
        What it does:
        Updates the 2D point cloud visualization based on the current side, step, and display options (color, size, aspect ratio, section coloring).
        """
        if (self.current_side is None or 
            self.current_step is None or 
            self.current_side not in self.data_by_side):
            return
            
        # Get steps for current side
        steps = self.data_by_side[self.current_side].get("steps", [])
        if self.current_step >= len(steps):
            return
        
        # Calculate global limits for consistent scale
        global_y_min = float('inf')
        global_y_max = float('-inf')
        global_z_min = float('inf')
        global_z_max = float('-inf')
        
        for step_data in steps:
            step_points = step_data.get("points", [])
            if step_points:
                y_values = [p.get("y", 0) for p in step_points]
                z_values = [p.get("z", 0) for p in step_points]
                
                if y_values:
                    global_y_min = min(global_y_min, min(y_values))
                    global_y_max = max(global_y_max, max(y_values))
                if z_values:
                    global_z_min = min(global_z_min, min(z_values))
                    global_z_max = max(global_z_max, max(z_values))

        z_range = global_z_max - global_z_min
        padding = z_range * 0.1  # 10% padding
        padded_z_min = global_z_min - padding
        padded_z_max = global_z_max + padding
                
        # Get current step and points
        step = steps[self.current_step]
        points = step.get("points", [])
        
        # Get step information
        step_num = step.get("step_number", self.current_step+1)
        predominant_section = self.get_predominant_section(points)
        
        # Extract coordinates (only Y and Z for 2D view)
        y = [p.get("y", 0) for p in points]
        z = [p.get("z", 0) for p in points]
        
        # Extract sections if we're coloring by section
        sections = [p.get("section", "Unknown") for p in points]
        unique_sections = list(set(sections))
        
        # Clear previous plot
        self.ax.clear()
        
        # Plot points
        if self.color_by_section_var.get() and len(unique_sections) > 1:
            # Plot by section
            section_colors = {}
            color_options = ['red', 'blue', 'green', 'purple', 'orange', 'brown', 'pink', 'gray', 'olive', 'cyan']
            
            for i, section in enumerate(unique_sections):
                color_idx = i % len(color_options)
                section_colors[section] = color_options[color_idx]
            
            # Create a scatter plot for each section
            for section in unique_sections:
                indices = [i for i, s in enumerate(sections) if s == section]
                if indices:
                    section_y = [y[i] for i in indices]
                    section_z = [z[i] for i in indices]
                    self.ax.scatter(section_y, section_z, 
                                   c=section_colors.get(section, 'black'), 
                                   s=self.point_size_var.get() * 20,
                                   label=section)
            
            self.ax.legend()
        else:
            # Single color for all points
            color = self.color_var.get()
            size = self.point_size_var.get() * 20
            self.ax.scatter(y, z, c=color, s=size)
        
        # Set labels and title
        self.ax.set_xlabel('Y')
        self.ax.set_ylabel('Z')
        self.ax.set_title(f'{self.current_side} - Step {step_num} - {predominant_section}')
        self.ax.grid(True)
        
        # Equal aspect ratio if selected
        if self.equal_aspect_var.get():
            self.ax.set_aspect('equal')
        else:
            self.ax.set_aspect('auto')
        
        # Set consistent axis limits
        #self.ax.set_xlim(global_y_min, global_y_max)
        self.ax.set_ylim(padded_z_min, padded_z_max)

        # Update the canvas
        self.canvas.draw()
        
        # Update info
        self.points_label.config(text=f"Points: {len(points)}")
        self.section_label.config(text=f"Section: {predominant_section}")

def find_latest_iteration_files(directory, pattern="Side*_Cleaned_Iter*_IQR*"):
    """
    find_latest_iteration_files / (function)
    What it does:
    Scans the specified directory for files matching the given pattern, identifies the latest iteration for each side, and returns a dictionary mapping side to the path of the latest file.
    Example: {"Side1": "/path/Side1_Cleaned_Iter2_IQR.json", ...}
    """
    all_files = glob.glob(os.path.join(directory, pattern))
    if not all_files:
        print(f"No files found matching pattern '{pattern}' in directory: {directory}")
        return {}

    files_by_side = {}
    for path in all_files:
        name = os.path.basename(path)

        # Extract something like "Side1" from the beginning
        side_match = re.match(r"(Side\d+)_Cleaned", name, re.IGNORECASE)
        if side_match:
            side_id = side_match.group(1)
        else:
            side_id = "UnknownSide"

        # Extract iteration number (IterX)
        iter_match = re.search(r"_Iter(\d+)_", name, re.IGNORECASE)
        iter_num = 0
        if iter_match:
            iter_num = int(iter_match.group(1))

        if side_id not in files_by_side:
            files_by_side[side_id] = (path, iter_num)
        else:
            _, existing_iter = files_by_side[side_id]
            if iter_num > existing_iter:
                files_by_side[side_id] = (path, iter_num)

    # Return only the path of the file with the highest iteration
    return {
        side: info[0] for side, info in files_by_side.items()
    }

if __name__ == "__main__":
    root = tk.Tk()
    app = PointCloudViewer2D(root)
    root.mainloop()