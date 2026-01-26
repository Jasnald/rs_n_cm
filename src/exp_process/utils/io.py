from importations import *

logger = logging.getLogger(__name__)

class NumpyEncoder(json.JSONEncoder):
    """
    Encoder customizado para salvar tipos do Numpy em JSON.
    Resolve o erro: 'Object of type float32 is not JSON serializable'
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def save_json(data: dict, filepath: str, indent: int = 2):
    """
    Salva um dicionário como JSON, garantindo que o diretório pai exista
    e convertendo tipos do Numpy automaticamente.
    """
    # Garante que a pasta existe
    parent_dir = os.path.dirname(filepath)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, cls=NumpyEncoder, indent=indent)
        
    logger.info(f"Arquivo salvo com sucesso: {filepath}")
    
def load_json(filepath: str) -> dict:
    """Carrega um JSON do disco."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)