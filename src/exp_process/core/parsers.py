from ..importations import *

def parse_exp1_format(filepath: str) -> dict:

    data = {'bottom': [], 'wall': []}
    current_tag = None
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue

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
                    data[current_tag].append(vals)
                except ValueError:
                    logging.warning(f"Linha ignorada em {filepath}: {line}")
                    
    return {k: np.array(v) for k, v in data.items() if v}
        


def parse_exp2_simple(filepath: str) -> np.ndarray:

    return np.loadtxt(filepath, comments="#")
    