# -*- coding: utf-8 -*-
import os, sys

class ExpProcessor(object):
    
    @staticmethod
    def get_average(values):

        if not values: return 0.0
        return sum(values) / float(len(values))

    @staticmethod
    def process_t_shape(raw_data):

        meas = raw_data.get('measurements', {})

        avg = {}
        for key, vals in meas.items():
            avg[key] = ExpProcessor.get_average(vals)

        base_thick = (avg.get('bottom_thickness_left', 0) + 
                      avg.get('bottom_thickness_right', 0)) / 2.0
        
        v_height = avg.get('total_height', 0) - base_thick
        
        return {
            'h_width': avg.get('bottom_width', 0),
            'h_thickness': base_thick,
            'v_width': avg.get('wall_width', 0),
            'v_height': v_height,
            'offset_1': avg.get('flange_left', 0)
        }
    
    @staticmethod
    def process_block_shape(raw_data):

        meas = raw_data.get('measurements', {})

        avg = {}
        for key, vals in meas.items():
            avg[key] = ExpProcessor.get_average(vals)

        return {
            "avg_lenth":  avg.get("lenth", 0),
            "avg_width":  avg.get("width", 0),
            "avg_height": avg.get("height", 0),
            "avg_cut":    avg.get("cut", 0)
        }
    
    @staticmethod
    def process(filepath):
        """Método que faltava: Carrega o arquivo e chama o processador correto."""
        data = ExpProcessor.load_data_module(filepath)
        if not data:
            return {}
            
        dtype = data.get("type")
        
        if dtype == "t_shape":
            return ExpProcessor.process_t_shape(data)
        elif dtype == "block_shape":
            return ExpProcessor.process_block_shape(data)
        else:
            print("Tipo desconhecido: %s" % dtype)
            return {}
        
    @staticmethod
    def load_data_module(filepath):
        """Carrega o arquivo .py como um módulo e extrai 'data'."""
        if not os.path.exists(filepath):
            print("ERRO: Arquivo nao encontrado: %s" % filepath)
            return None

        folder = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        module_name = filename.replace('.py', '')

        if folder not in sys.path:
            sys.path.append(folder)

        try:
            mod = __import__(module_name)
            # Garante reload para pegar alterações recentes
            if sys.version_info[0] >= 3:
                import importlib
                importlib.reload(mod)
            else:
                reload(mod)
            return getattr(mod, 'data', None)
        except Exception as e:
            print("Erro ao carregar modulo %s: %s" % (filepath, str(e)))
            return None