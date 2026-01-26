from ..importations import *

logger = logging.getLogger(__name__)

class NumpyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def save_json(data: dict, filepath: str, indent: int = 2):

    parent_dir = os.path.dirname(filepath)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, cls=NumpyEncoder, indent=indent)
        
    logger.info(f"Arquivo salvo com sucesso: {filepath}")
    
def load_json(filepath: str) -> dict:

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
    
class IOUtils:
    """
    Classe utilitária para operações de IO (Input/Output),
    compatível com os pipelines criados.
    """
    
    @staticmethod
    def save_json(data: dict, filepath: str, indent: int = 2):
        parent_dir = os.path.dirname(filepath)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=NumpyEncoder, indent=indent)
            
        logger.info(f"Arquivo salvo com sucesso: {filepath}")
    
    @staticmethod
    def load_json(filepath: str) -> dict:
        if not os.path.exists(filepath):
            return None
            
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)