from importations import *

from .base import BasePipeline
from ..core.fitter import Fitter
from ..core.cleaner import OutlierCleaner

class SurfacePipeline(BasePipeline):

    def __init__(self, input_dir, output_dir):
        super().__init__(input_dir, output_dir, subfolder="surface_data")

    def map_files(self) -> dict:

        mapped = {}

        pattern = re.compile(r"(Side\d+)_(Measurment\d+)_(bottom|wall)", re.IGNORECASE)

        temp_pairs = {} 
        
        for fname in os.listdir(self.input_dir):
            match = pattern.search(fname)

            if not match:
                continue
                
            side, meas, type_raw = match.groups()
            type_key = type_raw.lower()

            pair_key = (side, meas)
            
            if pair_key not in temp_pairs:
                temp_pairs[pair_key] = {}
            
            temp_pairs[pair_key][type_key] = fname

        for (side, meas), files in temp_pairs.items():

            if 'bottom' not in files or 'wall' not in files:
                continue

            if side not in mapped:
                mapped[side] = []

            mapped[side].append(files)
        
        return mapped

    def load_and_process_data(self, measurements_list):

        all_points = []
        for m in measurements_list:
            b = self.loader.load_surface_data(m['bottom'])['bottom']
            w = self.loader.load_surface_data(m['wall'])['wall']
            if len(b) and len(w):
                all_points.append(np.vstack([b, w]))
        
        if not all_points: return None
        
        merged = np.vstack(all_points)
        

        cleaned = OutlierCleaner.filter_iqr(merged, {'z': 1.5})
        return cleaned

    def fit_model(self, points, degree):

        x, y, z = points[:, 0], points[:, 1], points[:, 2]
        return Fitter.fit_2d_poly(x, y, z, degree)