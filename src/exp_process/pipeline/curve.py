from ..importations import *

from .base import BasePipeline
from ..core.fitter import Fitter

class CurvePipeline(BasePipeline):

    def __init__(self, input_dir, output_dir):

        super().__init__(input_dir, output_dir, subfolder="curve_data")

    def map_files(self) -> dict:
        mapped = {}
        pattern = re.compile(r"(Sample\d+).*[_\-\.](L|R)[_\-\.]", re.IGNORECASE)
        
        for fname in os.listdir(self.input_dir):
            match = pattern.search(fname)
            if match:
                sample_id, side = match.groups()
                side = side.upper()
                if sample_id not in mapped: mapped[sample_id] = {}
                mapped[sample_id][side] = fname
        return mapped

    def load_and_process_data(self, files):

        if 'L' not in files or 'R' not in files:
            return None # Ou levantar warning

        data_l = self.loader.load_curve_data(files['L'])
        data_r = self.loader.load_curve_data(files['R'])
        
        if data_l.shape != data_r.shape:
            raise ValueError("L/R shapes mismatch")
            
        return (data_l + data_r) / 2.0

    def fit_model(self, points, degree):

        x = points[:, 0]
        z = points[:, 1]
        return Fitter.fit_1d_poly(x, z, degree)