import numpy as np
import logging

def parse_exp1_format(filepath: str) -> dict:
    """
    Lê o formato antigo 'bottom/wall' com tags.
    Retorna: {'bottom': np.array, 'wall': np.array}
    """
    data = {'bottom': [], 'wall': []}
    current_tag = None
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            # Detecta tags (Lógica flexível)
            if "#bottom" in line.lower():
                current_tag = 'bottom'
                continue
            elif "#wall" in line.lower():
                current_tag = 'wall'
                continue
            
            # Tenta ler números se estiver dentro de uma tag
            if current_tag:
                try:
                    # Substitui vírgula por ponto se necessário (comum em dados PT-BR/DE)
                    clean_line = line.replace(',', '.')
                    vals = [float(x) for x in clean_line.split()]
                    data[current_tag].append(vals)
                except ValueError:
                    logging.warning(f"Linha ignorada em {filepath}: {line}")
                    
    return {k: np.array(v) for k, v in data.items() if v}
        


def parse_exp2_simple(filepath: str) -> np.ndarray:
    """
    Lê o formato simples de colunas (L/R files).
    Retorna: np.array NxM
    """
    # Usa numpy direto, mas com tratamento de erro
    return np.loadtxt(filepath, comments="#")
    