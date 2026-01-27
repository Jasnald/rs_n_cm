from ..importations import *

class DataTransformer:
    """
    Responsável por aplicar correções geométricas (espelhamento, inversão, offset)
    nos dados brutos antes do processamento matemático.
    """
    
    def __init__(self, rules: dict = None):
        """
        Args:
            rules (dict): Dicionário configurando as ações por ID.
            Ex: { 
                "Side2": {"mirror_x": True, "invert_z": True},
                "Side3": {"offset_x": 10.0}
            }
        """
        self.rules = rules if rules else {}

    def apply(self, side_id: str, points: np.ndarray) -> np.ndarray:
        """Aplica as transformações configuradas para o side_id fornecido."""
        
        if side_id not in self.rules:
            return points # Retorna inalterado se não houver regra
            
        config = self.rules[side_id]
        pts = points.copy() # Não altera o original diretamente
        
        # 1. Espelhamento em X (Espelho em relação ao MAX ou centro)
        if config.get("mirror_x"):
            # x_new = x_max - x_atual (Inverte a direção do eixo X)
            pts[:, 0] = pts[:, 0].max() - pts[:, 0]
            
        # 2. Inversão de Z (Multiplica por -1)
        if config.get("invert_z"):
            pts[:, 2] = -pts[:, 2]

        # 3. Offsets (Deslocamentos)
        if "offset_x" in config: pts[:, 0] += config["offset_x"]
        if "offset_y" in config: pts[:, 1] += config["offset_y"]
        if "offset_z" in config: pts[:, 2] += config["offset_z"]

        return pts