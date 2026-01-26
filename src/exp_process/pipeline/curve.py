import os
import re
import numpy as np
import logging
import json

from ..core.loader import DataLoader
from ..core.fitter import Fitter
# Se curvas precisarem de limpeza, descomente abaixo:
# from ..core.cleaner import OutlierCleaner 

logger = logging.getLogger(__name__)

class CurvePipeline:
    """
    Pipeline para processamento de Curvas 2D (Experimento 2 - L/R).
    Fluxo:
    1. Busca pares de arquivos L (Left) e R (Right) para cada Amostra (Sample).
    2. Carrega e tira a média aritmética entre os lados.
    3. Ajusta um polinômio 1D (z = f(x)).
    4. Salva os resultados.
    """

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.loader = DataLoader(input_dir)
        
        # Cria diretório de saída
        os.makedirs(os.path.join(output_dir, "curve_data"), exist_ok=True)

    def run(self, degrees=[2, 4]):
        """
        Executa a pipeline de curvas.
        Args:
            degrees: Lista de graus polinomiais para ajuste.
        """
        logger.info("Iniciando Pipeline de Curvas (L/R)...")

        # 1. Agrupar arquivos (Sample -> L/R)
        samples_map = self._map_files_by_sample()

        if not samples_map:
            logger.warning("Nenhum par de arquivos L/R encontrado.")
            return

        # 2. Processar cada Amostra
        for sample_id, files in samples_map.items():
            
            # Guard Clause 1: Garante par completo
            if 'L' not in files or 'R' not in files:
                logger.warning(f"Par incompleto para {sample_id}: {files}")
                continue

            logger.info(f"Processando {sample_id}...")
            
            # --- Passo A: Carregamento ---
            # O loader/parser estoura erro se arquivo não existir ou estiver corrompido
            data_l = self.loader.load_curve_data(files['L'])
            data_r = self.loader.load_curve_data(files['R'])

            # Guard Clause 2: Dados vazios
            if data_l.size == 0 or data_r.size == 0:
                logger.warning(f"Dados vazios em {sample_id}. Pulando.")
                continue

            # Guard Clause 3: Compatibilidade de shape para média
            if data_l.shape != data_r.shape:
                raise ValueError(f"Shape mismatch em {sample_id}: L={data_l.shape}, R={data_r.shape}")

            # --- Passo B: Média (L + R) / 2 ---
            # Assume formato [x, z] ou [x, y, z]. Se for curva 2D, geralmente é coluna X e Z.
            avg_points = (data_l + data_r) / 2.0
            
            # (Opcional) Limpeza de Outliers poderia entrar aqui se necessário
            # avg_points = OutlierCleaner.filter_iqr(avg_points, {'z': 1.5})

            # --- Passo C: Ajuste 1D (Fit) ---
            # Assume Coluna 0 = X, Coluna 1 = Z (ajuste conforme seu dado real)
            x = avg_points[:, 0]
            z = avg_points[:, 1]

            for degree in degrees:
                logger.info(f"  Ajustando Polinômio Grau {degree}...")
                
                fit_result = Fitter.fit_1d_poly(x, z, degree)
                
                self._save_result(sample_id, avg_points, fit_result, degree)

    def _map_files_by_sample(self) -> dict:
        """
        Mapeia arquivos L e R.
        Espera nomes como: Sample1_L.txt, Sample05_R_processed.txt
        Retorna: { 'Sample1': {'L': '...', 'R': '...'}, ... }
        """
        mapped = {}
        # Regex flexível: Captura "SampleX" e depois procura indicativo de L ou R
        # Grupo 1: ID da amostra (ex: Sample1)
        # Grupo 2: Lado (L ou R)
        pattern = re.compile(r"(Sample\d+).*[_\-\.](L|R)[_\-\.]", re.IGNORECASE)
        
        all_files = os.listdir(self.input_dir)

        for fname in all_files:
            match = pattern.search(fname)
            
            # Guard Clause: Ignora arquivos que não batem no padrão
            if not match:
                continue

            sample_id, side_tag = match.groups()
            side_key = side_tag.upper() # Normaliza para 'L' ou 'R'
            
            if sample_id not in mapped:
                mapped[sample_id] = {}
            
            # Checa duplicidade (fail fast se já tiver arquivo para aquele lado)
            if side_key in mapped[sample_id]:
                raise FileExistsError(f"Multiplos arquivos '{side_key}' encontrados para {sample_id}: {fname}")

            mapped[sample_id][side_key] = fname
        
        return mapped

    def _save_result(self, sample_id: str, points: np.ndarray, fit_model: dict, degree: int):
        filename = f"{sample_id}_Degree{degree}_Avg.json"
        path = os.path.join(self.output_dir, "curve_data", filename)
        
        output_data = {
            "sample": sample_id,
            "raw_points_count": len(points),
            "fit_model": fit_model
        }
        
        with open(path, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"  Salvo: {path}")