import os
import glob
import re
import numpy as np
import logging
import json

from ..core.loader import DataLoader
from ..core.cleaner import OutlierCleaner
from ..core.fitter import Fitter

# Configuração de Log local
logger = logging.getLogger(__name__)

class SurfacePipeline:
    """
    Pipeline para processamento de superfícies 3D (Experimento 1).
    Fluxo:
    1. Busca pares de arquivos _bottom e _wall.
    2. Combina e tira a média entre múltiplas medições (Measurement1, 2...).
    3. Limpa outliers usando IQR.
    4. Ajusta uma superfície polinomial 2D (z = f(x, y)).
    5. Salva os resultados.
    """

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.loader = DataLoader(input_dir)
        
        # Garante que pastas de saída existam
        os.makedirs(os.path.join(output_dir, "surface_data"), exist_ok=True)

    def run(self, degrees=[1, 2], clean_iterations=2):
        """
        Executa a pipeline completa.
        
        Args:
            degrees: Lista de graus polinomiais para ajustar (ex: [1, 2]).
            clean_iterations: Quantas passadas de filtro IQR aplicar.
        """
        logger.info("Iniciando Pipeline de Superfície...")

        # 1. Agrupar arquivos por Lado (Side)
        # Ex: Side1 tem Measurement1_bottom, Measurement1_wall, Measurement2...
        sides_map = self._map_files_by_side()

        if not sides_map:
            logger.warning("Nenhum arquivo '_bottom'/'_wall' encontrado.")
            return

        # 2. Processar cada Lado
        for side, measurements in sides_map.items():
            logger.info(f"Processando {side} ({len(measurements)} medições)...")
            
            # --- Passo A: Carregar e Combinar ---
            combined_points = []
            for m_files in measurements:
                # Carrega Bottom e Wall
                data_bottom = self.loader.load_surface_data(m_files['bottom'])['bottom']
                data_wall = self.loader.load_surface_data(m_files['wall'])['wall']
                
                # Junta tudo num array único Nx3 (x, y, z)
                # Assumindo que o loader devolve Nx3. Se tiver cabeçalho ou metadados, ajustar.
                if len(data_bottom) > 0 and len(data_wall) > 0:
                    merged = np.vstack([data_bottom, data_wall])
                    combined_points.append(merged)
                
                
            if not combined_points:
                continue

            # --- Passo B: Média das Medições ---
            # Simplificação: Empilha todos os pontos de todas as medições para criar uma "nuvem mestra"
            # (Alternativa: tirar média ponto a ponto se a malha for idêntica, mas empilhar é mais robusto)
            all_points = np.vstack(combined_points)
            logger.info(f"  Total de pontos brutos: {len(all_points)}")

            # --- Passo C: Limpeza (IQR) ---
            cleaned_points = all_points
            for i in range(clean_iterations):
                # Parâmetros de limpeza (ajustável)
                factors = {'z': 1.5 if i == 0 else 1.0} # Mais rigoroso na segunda passada
                cleaned_points = OutlierCleaner.filter_iqr(cleaned_points, factors)
                logger.info(f"  Limpeza Iteração {i+1}: {len(cleaned_points)} pontos restantes")

            # --- Passo D: Ajuste de Superfície (Fit) ---
            for degree in degrees:
                logger.info(f"  Ajustando Polinômio Grau {degree}...")
                
                # Extrai X, Y, Z
                x = cleaned_points[:, 0]
                y = cleaned_points[:, 1]
                z = cleaned_points[:, 2]

                # Ajusta
                fit_result = Fitter.fit_2d_poly(x, y, z, degree)
                
                # Salva Resultado
                self._save_result(side, cleaned_points, fit_result, degree)

    def _map_files_by_side(self) -> dict:
        """
        Varre o diretório e agrupa arquivos.
        Retorna: { 'Side1': [ {'bottom': 'file_b.txt', 'wall': 'file_w.txt'}, ... ] }
        """
        mapped = {}
        # Regex para capturar Side e Measurement
        # Espera algo como: Side1_Measurment2_bottom.txt
        pattern = re.compile(r"(Side\d+)_(Measurment\d+)_(bottom|wall)")
        
        # Lista todos os arquivos
        all_files = os.listdir(self.input_dir)
        
        temp_map = {} # Chave temporária: (Side, Measurement)

        for fname in all_files:
            match = pattern.search(fname)
            if match:
                side, meas, type_ = match.groups()
                key = (side, meas)
                
                if key not in temp_map:
                    temp_map[key] = {}
                
                temp_map[key][type_] = fname

        # Converte para o formato final
        for (side, meas), files in temp_map.items():
            if 'bottom' in files and 'wall' in files:
                if side not in mapped:
                    mapped[side] = []
                mapped[side].append(files)
            else:
                logger.warning(f"Par incompleto para {side}/{meas}: {files}")
        
        return mapped

    def _save_result(self, side: str, points: np.ndarray, fit_model: dict, degree: int):
        """Salva o JSON final processado."""
        filename = f"{side}_Degree{degree}_Processed.json"
        path = os.path.join(self.output_dir, "surface_data", filename)
        
        output_data = {
            "side": side,
            "raw_points_count": len(points),
            # Salva amostra dos pontos (opcional, para não ficar gigante)
            # "points_sample": points[::10].tolist(), 
            "fit_model": fit_model
        }
        
        with open(path, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"  Salvo: {path}")