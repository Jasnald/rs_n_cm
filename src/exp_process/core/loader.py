from .parsers import parse_exp1_format, parse_exp2_simple

class DataLoader:
    def __init__(self, input_dir):
        self.input_dir = input_dir

    def load_surface_data(self, filename):
        # Delega a sujeira para o parser
        path = f"{self.input_dir}/{filename}"
        return parse_exp1_format(path)

    def load_curve_data(self, filename):
        path = f"{self.input_dir}/{filename}"
        return parse_exp2_simple(path)