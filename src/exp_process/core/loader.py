from ..importations import *

from .parsers import parse_exp1_format, parse_exp2_simple

class DataLoader:
    
    def __init__(self, input_dir):
        self.input_dir = input_dir

    def load_surface_data(self, filename):
        path = os.path.join(self.input_dir, filename)
        
        # Tenta inferir a tag padrão pelo nome do arquivo
        default = None
        if 'bottom' in filename.lower():
            default = 'bottom'
        elif 'wall' in filename.lower():
            default = 'wall'
            
        return parse_exp1_format(path, default_tag=default)

    def load_curve_data(self, filename):
        path = os.path.join(self.input_dir, filename)
        return parse_exp2_simple(path)