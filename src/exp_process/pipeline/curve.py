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

        # 1. Carrega dados brutos (N x M)
        raw_l = self.loader.load_curve_data(files['L'])
        raw_r = self.loader.load_curve_data(files['R'])
        
        # Assume colunas [0]=X, [1]=Z (Ajuste os índices se seu txt for diferente)
        xl, zl = raw_l[:, 0], raw_l[:, 1]
        xr, zr = raw_r[:, 0], raw_r[:, 1]
        
        # 2. Ordena vetores pelo X (correção caso um sensor leia ao contrário)
        idx_l = np.argsort(xl)
        xl, zl = xl[idx_l], zl[idx_l]
        
        idx_r = np.argsort(xr)
        xr, zr = xr[idx_r], zr[idx_r]
        
        # 3. Cria um Grid X comum (intersecção dos domínios)
        start = max(xl.min(), xr.min())
        end = min(xl.max(), xr.max())
        
        # Número de pontos = média da densidade dos originais
        n_points = int((len(xl) + len(xr)) / 2)
        x_common = np.linspace(start, end, n_points)
        
        # 4. Interpola ambos para o Grid comum
        z_l_interp = np.interp(x_common, xl, zl)
        z_r_interp = np.interp(x_common, xr, zr)
        
        # 5. Calcula a Média
        z_avg = (z_l_interp + z_r_interp) / 2.0
        
        # Retorna formato (N x 2) compatível com o resto do sistema
        return np.column_stack((x_common, z_avg))

    def fit_model(self, points, degree):
        x = points[:, 0]
        z = points[:, 1]
        return Fitter.fit_1d_poly(x, z, degree)