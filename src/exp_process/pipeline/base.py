from ..importations import *

from ..core.loader import DataLoader
from ..utils.io import save_json

logger = logging.getLogger(__name__)

class BasePipeline(ABC):
    def __init__(self, input_dir: str, output_dir: str, subfolder: str):
        self.input_dir = input_dir
        self.output_dir = os.path.join(output_dir, subfolder)
        self.loader = DataLoader(input_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self, degrees=[1]):
        logger.info(f"Iniciando pipeline em: {self.input_dir}")

        items_map = self.map_files() 
        
        if not items_map:
            logger.warning("Nenhum arquivo encontrado para processar.")
            return

        for key_id, files in items_map.items():
            logger.info(f"Processando item: {key_id}")

            try:
                points = self.load_and_process_data(files)

                if points is None or len(points) == 0:
                    logger.warning(f"  Dados vazios para {key_id}. Pulando.")
                    continue

                for degree in degrees:

                    model = self.fit_model(points, degree)
                    
                    self._save_standard_result(key_id, points, model, degree)
                    
            except Exception as e:
                logger.error(f"  Erro crítico em {key_id}: {e}")
                continue

    def _save_standard_result(self, key_id, points, model, degree):

        filename = f"{key_id}_Degree{degree}_Processed.json"
        path = os.path.join(self.output_dir, filename)
        
        payload = {
            "id": key_id,
            "degree": degree,
            "points_count": len(points),
            "fit_model": model
        }
        save_json(payload, path)
    
    @abstractmethod
    def map_files(self) -> dict:
        """Deve retornar dict: { 'ID_Unico': ['arq1', 'arq2'] ou {'L':..., 'R':...} }"""
        pass

    @abstractmethod
    def load_and_process_data(self, files) -> any:
        """Deve retornar a nuvem de pontos limpa (Numpy array) pronta para o fit."""
        pass

    @abstractmethod
    def fit_model(self, points, degree) -> dict:
        """Deve retornar o dicionário do modelo ajustado."""
        pass