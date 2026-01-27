# Arquivo: src/exp_process/core/operations.py
from ..importations import *

class ModelOps:

    @staticmethod
    def subtract_coeffs(model_high: dict, model_low: dict) -> dict:
        """
        Subtrai os coeficientes de dois modelos. 
        Suporta graus diferentes (ex: Grau 4 - Grau 1) preenchendo com zeros.
        """
        deg_h = model_high['degree']
        deg_l = model_low['degree']
        
        # Garante que model_high é o de maior grau
        if deg_l > deg_h:
            raise ValueError("O primeiro modelo deve ter grau maior ou igual ao segundo.")

        coeffs_h = np.array(model_high['coeffs'])
        coeffs_l = np.array(model_low['coeffs'])
        
        # Estrutura dos coeficientes: [x, y, x^2, y^2, ..., x^n, y^n, Bias]
        # Tamanho do vetor = 2*grau + 1
        
        len_h = len(coeffs_h)
        len_l = len(coeffs_l)
        
        # Cria vetor de zeros do tamanho do maior grau
        coeffs_l_padded = np.zeros(len_h)
        
        # O termo de Bias (constante) é sempre o último
        coeffs_l_padded[-1] = coeffs_l[-1]
        
        # Os termos x^k, y^k ocupam os índices 0 até (2*deg_l)
        # Ex: Grau 1 (len 3): [x, y, Bias] -> copia [0:2]
        terms_count = 2 * deg_l
        if terms_count > 0:
            coeffs_l_padded[0:terms_count] = coeffs_l[0:terms_count]
            
        # Agora podemos subtrair diretamente
        diff_coeffs = coeffs_h - coeffs_l_padded
        
        return {
            "type": model_high['type'],
            "degree": deg_h, # Mantém o grau maior
            "coeffs": diff_coeffs.tolist(),
            "norm": model_high.get("norm")
        }

    @staticmethod
    def average_models(models: list) -> dict:
        if not models: return {}
        base = models[0]

        # Verifica se todos têm o mesmo grau para média
        base_deg = base['degree']
        for m in models:
            if m['degree'] != base_deg:
                 raise ValueError("Para média, todos os modelos devem ter o mesmo grau.")

        all_coeffs = np.vstack([np.array(m['coeffs']) for m in models])
        avg_coeffs = np.mean(all_coeffs, axis=0)
        
        return {
            "type": base['type'],
            "degree": base['degree'],
            "coeffs": avg_coeffs.tolist(),
            "norm": base.get("norm")
        }