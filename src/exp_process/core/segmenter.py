from ..importations import *

class StepSegmenter:
    """
    Responsável por segmentar uma nuvem de pontos em 'passos' (steps)
    baseado em descontinuidades no eixo X.
    """

    @staticmethod
    def find_steps(points: np.ndarray, threshold_percent: float = 0.6) -> list:
        """
        Recebe uma nuvem de pontos (N, 3) -> [x, y, z].
        Retorna uma lista de arrays, onde cada array é um passo isolado.
        """
        if points is None or len(points) == 0:
            return []

        # 1. Ordenação Lexicográfica:
        # Ordena primariamente por X (coluna 0) e secundariamente por Y (coluna 1).
        # np.lexsort aceita as chaves na ordem inversa (secundária, primária).
        sort_indices = np.lexsort((points[:, 1], points[:, 0]))
        sorted_data = points[sort_indices]

        # 2. Calcular a diferença percentual no eixo X
        x_values = sorted_data[:, 0]
        
        # diff[i] = x[i+1] - x[i]
        x_diff = np.abs(np.diff(x_values))
        
        # Evitar divisão por zero adicionando um epsilon minúsculo
        x_base = np.abs(x_values[:-1]) + 1e-10
        
        # Variação % = (delta_x / x_atual) * 100
        x_diff_percent = (x_diff / x_base) * 100

        # 3. Identificar índices onde a variação supera o limiar (ex: 0.6%)
        # np.where retorna os índices onde a condição é True.
        # Adicionamos +1 porque o diff reduz o array em 1 elemento e queremos 
        # o índice de início do *próximo* segmento.
        split_indices = np.where(x_diff_percent > threshold_percent)[0] + 1

        # 4. Dividir o array original nesses índices
        if len(split_indices) > 0:
            steps = np.split(sorted_data, split_indices)
        else:
            steps = [sorted_data]

        return steps