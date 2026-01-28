# Arquivo: src/exp_process/pipeline/surface.py
from ..importations import *

from .base import BasePipeline
from ..core.fitter import Fitter
from ..core.segmenter import StepSegmenter
from ..core.cleaner import OutlierCleaner
from ..utils.io import save_json

class SurfacePipeline(BasePipeline):

    def __init__(self, input_dir, output_dir, *params):
        super().__init__(input_dir, output_dir, subfolder="surface_data")
        self.p_botton, self.p_top, self.p_general = params 

    def map_files(self) -> dict:

        mapped = {}
        pattern = re.compile(r"(Side\d+)_(Measurment\d+)_(bottom|wall)", re.IGNORECASE)
        temp_pairs = {} 
        
        for fname in os.listdir(self.input_dir):
            match = pattern.search(fname)
            if not match: continue
                
            side, meas, type_raw = match.groups()
            type_key = type_raw.lower()
            pair_key = (side, meas)
            
            if pair_key not in temp_pairs: temp_pairs[pair_key] = {}
            temp_pairs[pair_key][type_key] = fname

        for (side, meas), files in temp_pairs.items():
            if 'bottom' not in files or 'wall' not in files: continue
            if side not in mapped: mapped[side] = []
            mapped[side].append(files)
        
        return mapped
    
    def process_and_save_steps(self, key_id, points):

        steps_list = StepSegmenter.find_steps(points, threshold_percent=0.6)
        
        steps_data = {
            "id": key_id,
            "total_steps": len(steps_list),
            "steps": []
        }

        for i, step_points in enumerate(steps_list):
            steps_data["steps"].append({
                "step_number": i + 1,
                "point_count": len(step_points),
                "mean_x": float(np.mean(step_points[:, 0])),
                "points": step_points.tolist() 
            })

        filename = f"{key_id}_Steps.json"
        path = os.path.join(self.output_dir, filename)
        save_json(steps_data, path)
        
        return steps_list

    def load_and_process_data(self, measurements_list):
        all_points = []

        clean_params_bottom = {'z': self.p_botton} 
        clean_params_wall = {'z': self.p_top}

        for m in measurements_list:

            raw_b = self.loader.load_surface_data(m['bottom'])['bottom']
            clean_b = OutlierCleaner.filter_iqr(raw_b, clean_params_bottom)

            raw_w = self.loader.load_surface_data(m['wall'])['wall']
            clean_w = OutlierCleaner.filter_iqr(raw_w, clean_params_wall)

            if len(clean_b) > 0 and len(clean_w) > 0:
                all_points.append(np.vstack([clean_b, clean_w]))
        
        if not all_points: return None
        
        merged = np.vstack(all_points)
        
        final_clean = OutlierCleaner.filter_iqr(merged, {'z': self.p_general})
        
        return final_clean

    def fit_model(self, points, degree):
        x, y, z = points[:, 0], points[:, 1], points[:, 2]
        return Fitter.fit_2d_poly(x, y, z, degree)