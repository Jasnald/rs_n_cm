from ..importations import *

def parse_exp1_format(filepath: str, default_tag: str = None) -> dict:

    data = {'bottom': [], 'wall': []}
    current_tag = default_tag # Começa com o padrão (ex: 'bottom') se informado
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue

            # Se encontrar a tag no arquivo, ela tem prioridade
            if "#bottom" in line.lower():
                current_tag = 'bottom'
                continue
            elif "#wall" in line.lower():
                current_tag = 'wall'
                continue

            if current_tag:
                try:
                    clean_line = line.replace(',', '.')
                    vals = [float(x) for x in clean_line.split()]
                    if current_tag in data:
                        data[current_tag].append(vals)
                except ValueError:
                    logging.warning(f"Linha ignorada em {filepath}: {line}")
                    
    return {k: np.array(v) for k, v in data.items() if v}
        

def parse_exp2_simple(filepath: str) -> np.ndarray:
    return np.loadtxt(filepath, comments="#")

def find_exp2_folders(root_dir: str) -> dict:
    """
    Varre o diretório em busca de pastas no formato '1L', '1R', etc.
    Retorna: { '1': {'L': path_to_file, 'R': path_to_file}, ... }
    """
    mapped = {}
    pattern = re.compile(r"^(\d+)([LR])$", re.IGNORECASE)
    
    try:
        items = os.listdir(root_dir)
    except FileNotFoundError:
        return {}

    for folder_name in items:
        folder_path = os.path.join(root_dir, folder_name)
        
        if not os.path.isdir(folder_path): continue
            
        match = pattern.match(folder_name)
        if match:
            sample_id, side = match.groups()
            side = side.upper()
            
            # Define qual arquivo buscar dentro da pasta
            # Ajuste aqui se o nome do arquivo mudar
            target_file = os.path.join(folder_path, "2d-Gerade1.txt")
            
            if os.path.exists(target_file):
                if sample_id not in mapped: mapped[sample_id] = {}
                mapped[sample_id][side] = target_file

    return mapped