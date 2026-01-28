from ..importations import *

from .base import BasePipeline
from ..core.fitter import Fitter
from ..core.parsers import find_exp2_folders

class CurvePipeline(BasePipeline):

    def __init__(self, input_dir, output_dir):

        super().__init__(input_dir, output_dir, subfolder="curve_data")

    def map_files(self) -> dict:
            """
            Delega a busca de arquivos para o parser especializado em pastas.
            """
            return find_exp2_folders(self.input_dir)

    def load_and_process_data(self, files):
        # Verifica se tem o par completo
        if 'L' not in files or 'R' not in files:
            return None 

        # Carrega os dados brutos
        data_l = self.loader.load_curve_data(files['L'])
        data_r = self.loader.load_curve_data(files['R'])

        min_len = min(len(data_l), len(data_r))

        data_l = data_l[:min_len]
        data_r = data_r[:min_len]
        # --------------------------------

        # Retorna a média
        return (data_l + data_r) / 2.0

    def fit_model(self, points, degree):

        x = points[:, 0]
        z = points[:, 1]
        return Fitter.fit_1d_poly(x, z, degree)