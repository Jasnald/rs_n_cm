from ..importations import *

class StepSegmenter:

    @staticmethod
    def find_steps(points: np.ndarray, threshold_percent: float = 0.6) -> list:

        if points is None or len(points) == 0:
            return []


        sort_indices = np.lexsort((points[:, 1], points[:, 0]))
        sorted_data = points[sort_indices]

        x_values = sorted_data[:, 0]

        x_diff = np.abs(np.diff(x_values))

        x_base = np.abs(x_values[:-1]) + 1e-10

        x_diff_percent = (x_diff / x_base) * 100

        split_indices = np.where(x_diff_percent > threshold_percent)[0] + 1

        if len(split_indices) > 0:
            steps = np.split(sorted_data, split_indices)
        else:
            steps = [sorted_data]

        return steps