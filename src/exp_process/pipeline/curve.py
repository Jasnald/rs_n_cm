from ..importations import *
from .base import BasePipeline
from ..core.fitter import Fitter
from ..core.parsers import find_exp2_folders

class CurvePipeline(BasePipeline):

    def __init__(self, input_dir, output_dir):
        super().__init__(input_dir, output_dir, subfolder="curve_data")

    def map_files(self) -> dict:
        return find_exp2_folders(self.input_dir)

    def load_and_process_data(self, files):
            if 'L' not in files or 'R' not in files:
                return None 

            # Load raw data
            raw_l = self.loader.load_curve_data(files['L'])
            raw_r = self.loader.load_curve_data(files['R'])
            
            # --- LOGIC CHANGED TO MATCH EXP2 (Index-based) ---
            
            # Ensure raw_r is reversed (as done in exp2: data_R[::-1])
            # Verify if your data requires this reversal based on acquisition direction
            raw_r = raw_r[::-1] 

            # Truncate to minimum common length
            min_len = min(len(raw_l), len(raw_r))
            
            # Slice arrays
            l_sliced = raw_l[:min_len]
            r_sliced = raw_r[:min_len]
            
            # Calculate element-wise average (X, Y/Z averaged directly)
            avg_data = (l_sliced + r_sliced) / 2.0
            
            # Ensure output is (N, 2) -> [X, Z]
            # Assuming input columns are 0:X, 1:Y, 2:Z or similar. 
            # Adjust column indices based on your file format.
            # If input is already 2 columns (X, Z):
            return avg_data
            
            # If input has 3 columns and you want X, Z:
            # return avg_data[:, [0, 2]]

    def fit_model(self, points, degree):
        x = points[:, 0]
        z = points[:, 1]
        return Fitter.fit_1d_poly(x, z, degree)