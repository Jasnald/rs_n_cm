from ..importations import *

class OutlierCleaner:
    """
    Provides static methods for removing outliers from data arrays.
    """

    @staticmethod
    def filter_iqr(data: np.ndarray, factors: dict) -> np.ndarray:
        """
        Remove outliers from data using the IQR method for each axis.

        Args:
            data (np.ndarray): Input data array (N, 3) for x, y, z.
            factors (dict): Outlier factors for each axis, e.g., {'x': 1.5, 'y': 1.5}.

        Returns:
            np.ndarray: Data array with outliers removed.
        """
        if data.size == 0:
            return data  # No data to filter

        mask = np.ones(len(data), dtype=bool)  # Start with all data included

        axis_map = {'x': 0, 'y': 1, 'z': 2}

        for axis_name, factor in factors.items():
            col_idx = axis_map.get(axis_name.lower())
            if col_idx is None:
                continue  # Skip unknown axis

            col_data = data[:, col_idx]
            q1, q3 = np.percentile(col_data, [25, 75])
            iqr = q3 - q1

            lower = q1 - factor * iqr
            upper = q3 + factor * iqr

            mask &= (col_data >= lower) & (col_data <= upper)  # Keep only inliers

        return data[mask]