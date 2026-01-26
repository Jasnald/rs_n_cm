from importations import *

class OutlierCleaner:
    @staticmethod
    def filter_iqr(data: np.ndarray, factors: dict) -> np.ndarray:
        """
        Aplica filtro IQR nas colunas especificadas.
        
        Args:
            data: Array Nx3 (x, y, z)
            factors: Dict com fatores por eixo. Ex: {'x': 1.5, 'z': 1.2}
                     Eixos mapeados por índice: x=0, y=1, z=2
        Returns:
            Array filtrado (subconjunto das linhas originais).
        """
        if data.size == 0:
            return data

        mask = np.ones(len(data), dtype=bool)
        
        # Mapeamento string -> índice coluna
        axis_map = {'x': 0, 'y': 1, 'z': 2}

        for axis_name, factor in factors.items():
            col_idx = axis_map.get(axis_name.lower())
            if col_idx is None:
                continue
                
            col_data = data[:, col_idx]
            q1, q3 = np.percentile(col_data, [25, 75])
            iqr = q3 - q1
            
            lower = q1 - factor * iqr
            upper = q3 + factor * iqr
            
            # Mantém apenas quem está DENTRO dos limites
            mask &= (col_data >= lower) & (col_data <= upper)

        return data[mask]