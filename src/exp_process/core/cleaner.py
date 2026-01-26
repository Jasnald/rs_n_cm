from importations import *

class OutlierCleaner:
    @staticmethod
    def filter_iqr(data: np.ndarray, factors: dict) -> np.ndarray:

        if data.size == 0:
            return data

        mask = np.ones(len(data), dtype=bool)

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

            mask &= (col_data >= lower) & (col_data <= upper)

        return data[mask]