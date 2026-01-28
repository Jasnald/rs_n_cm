from ..importations import *

from .parsers import parse_exp1_format, parse_exp2_simple

class DataLoader:
    """
    Loads experimental surface and curve data from files in a given directory.
    """

    def __init__(self, input_dir):
        """
        Initialize DataLoader with input directory.

        Args:
            input_dir (str): Path to the input data directory.
        """
        self.input_dir = input_dir

    def load_surface_data(self, filename):
        """
        Load surface data from a file, inferring tag if possible.

        Args:
            filename (str): Name of the file to load.

        Returns:
            np.ndarray or object: Parsed surface data from file.
        """
        path = os.path.join(self.input_dir, filename)

        # Infer default tag from filename for downstream parsing
        default = None
        if 'bottom' in filename.lower():
            default = 'bottom'
        elif 'wall' in filename.lower():
            default = 'wall'

        return parse_exp1_format(path, default_tag=default)

    def load_curve_data(self, filename):
        """
        Load curve data from a file.

        Args:
            filename (str): Name of the file to load.

        Returns:
            np.ndarray or object: Parsed curve data from file.
        """
        path = os.path.join(self.input_dir, filename)
        return parse_exp2_simple(path)