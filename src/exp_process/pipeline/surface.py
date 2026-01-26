from importations import *

from .base import BasePipeline
from ..core.fitter import Fitter
from ..core.cleaner import OutlierCleaner

class SurfacePipeline(BasePipeline):
    def __init__(self, input_dir, output_dir):
        super().__init__(input_dir, output_dir, subfolder="surface_data")

    def map_files(self) -> dict:
        """
        Agrupa arquivos por Side e Measurement.
        Retorna: { 'Side1': [ {'bottom': '...', 'wall': '...'}, ... ], ... }
        """
        mapped = {}
        # Regex ajustado para capturar Side, Measurement e Tipo (bottom/wall)
        # Nota: Ajuste 'Measurment' para 'Measurement' se seus arquivos estiverem corrigidos
        pattern = re.compile(r"(Side\d+)_(Measurment\d+)_(bottom|wall)", re.IGNORECASE)
        
        # Dicionário temporário para parear: (Side, Measurement) -> {bottom: ..., wall: ...}
        temp_pairs = {} 
        
        for fname in os.listdir(self.input_dir):
            match = pattern.search(fname)
            
            # Guard Clause 1: Ignora arquivos que não seguem o padrão
            if not match:
                continue
                
            side, meas, type_raw = match.groups()
            type_key = type_raw.lower() # Garante 'bottom' ou 'wall' minúsculo
            
            # Chave única para identificar o par
            pair_key = (side, meas)
            
            if pair_key not in temp_pairs:
                temp_pairs[pair_key] = {}
            
            temp_pairs[pair_key][type_key] = fname

        # Transformação final: De pares isolados para agrupamento por Side
        for (side, meas), files in temp_pairs.items():
            
            # Guard Clause 2: Só aceita se tiver o par completo (bottom E wall)
            if 'bottom' not in files or 'wall' not in files:
                # logger.warning(f"Par incompleto ignorado em {side}/{meas}")
                continue

            # Inicializa a lista do Side se não existir
            if side not in mapped:
                mapped[side] = []
            
            # Adiciona o par validado à lista de medições desse lado
            mapped[side].append(files)
        
        return mapped

    def load_and_process_data(self, measurements_list):
        # Lógica específica: Empilhar múltiplas medições
        all_points = []
        for m in measurements_list:
            b = self.loader.load_surface_data(m['bottom'])['bottom']
            w = self.loader.load_surface_data(m['wall'])['wall']
            if len(b) and len(w):
                all_points.append(np.vstack([b, w]))
        
        if not all_points: return None
        
        merged = np.vstack(all_points)
        
        # Lógica específica: Limpeza Pesada (IQR)
        cleaned = OutlierCleaner.filter_iqr(merged, {'z': 1.5})
        return cleaned

    def fit_model(self, points, degree):
        # Lógica específica: Fit 2D
        x, y, z = points[:, 0], points[:, 1], points[:, 2]
        return Fitter.fit_2d_poly(x, y, z, degree)