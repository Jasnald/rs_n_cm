import os
import sys
import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt

# Prevent cache creation
sys.dont_write_bytecode = True

# Path Configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, 'src')
sys.path.append(os.path.abspath(src_path))

# Project Imports
from exp_process.pipeline.curve import CurvePipeline
from exp_process.core.fitter import Fitter
from exp_process.core.operations import ModelOps
from exp_process.utils.io import IOUtils
from exp_process.gui.viewer import PointCloudViewer
from exp_process.core.transformer import DataTransformer

# Global Configuration
INPUT_DIR = os.path.join(project_root, "data", "input", "exp2")
OUTPUT_DIR = os.path.join(project_root, "data", "output", "exp2")
CURVE_DIR = os.path.join(OUTPUT_DIR, "curve_data")

HIGH_DEGREE = 2
LOW_DEGREE = 1
IO = IOUtils()

# Transformation Rules (Optional)
DATA_FIX_RULES = {
    # "1": { "mirror_x": True } 
}

def step1_preprocess():
    print("\n=== STEP 1: PRE-PROCESS (Load & Merge L/R) ===")
    
    # Agora usa a classe original, pois ela já sabe ler as pastas
    pipeline = CurvePipeline(INPUT_DIR, OUTPUT_DIR)
    
    files_map = pipeline.map_files()
    processed_ids = []

    if not files_map:
        print(f"ERROR: No matching folders (1L, 1R...) found in {INPUT_DIR}")
        return []

    for sample_id, files in files_map.items():
        if 'L' not in files or 'R' not in files:
            print(f">> Skipping Sample {sample_id}: Missing L or R.")
            continue

        print(f">> Processing Sample {sample_id}...")
        
        # Load and Merge L/R
        points = pipeline.load_and_process_data(files)
        
        if points is None: continue

        data_payload = {
            "id": sample_id,
            "points_count": len(points),
            "points": points.tolist()
        }
        
        save_path = os.path.join(CURVE_DIR, f"{sample_id}_Raw.json")
        IO.save_json(data_payload, save_path)
        processed_ids.append(sample_id)
        
    return processed_ids

def step2_manual_validation():
    print("\n=== STEP 2: MANUAL VALIDATION (GUI) ===")
    print(">> Edit points and SAVE. Close to continue.")
    
    root = tk.Tk()
    app = PointCloudViewer(root, input_dir=CURVE_DIR)
    
    def on_closing():
        plt.close('all')
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

def step3_fitting_and_flattening(sample_ids):
    print(f"\n=== STEP 3: FITTING & FLATTENING ({HIGH_DEGREE} - {LOW_DEGREE}) ===")
    transformer = DataTransformer(DATA_FIX_RULES)

    for s_id in sample_ids:
        raw_file = os.path.join(CURVE_DIR, f"{s_id}_Raw.json")
        if not os.path.exists(raw_file): continue
            
        print(f">> Fitting Sample {s_id}...")
        data = IO.load_json(raw_file)
        points_np = np.array(data['points'])
        
        if len(points_np) < 5: continue

        points_np = transformer.apply(s_id, points_np)

        # 1D Profile Assumption: X vs Z
        X, Z = points_np[:, 0], points_np[:, 1] 

        # 1. Fit High Degree (Detail)
        model_high = Fitter.fit_1d_poly(X, Z, degree=HIGH_DEGREE)
        
        # 2. Fit Low Degree (Trend)
        model_low = Fitter.fit_1d_poly(X, Z, degree=LOW_DEGREE)
        
        # 3. Flatten
        model_flat = ModelOps.subtract_coeffs(model_high, model_low)
        
        model_flat['id'] = s_id
        model_flat['points'] = points_np.tolist()
        model_flat['note'] = f"Flattened: Deg {HIGH_DEGREE} - {LOW_DEGREE}"
        
        save_path = os.path.join(CURVE_DIR, f"{s_id}.json")
        IO.save_json(model_flat, save_path)
        print(f"   Saved: {s_id}.json")

def main():
    sample_ids = step1_preprocess()
    if not sample_ids: return
    
    step2_manual_validation()
    step3_fitting_and_flattening(sample_ids)
    print("\n=== FINISHED ===")

if __name__ == "__main__":
    main()