
from ..importations import *

class ModelOps:
    """
    Provides static methods for operations on polynomial model dictionaries.
    """

    @staticmethod
    def subtract_coeffs(model_high: dict, model_low: dict) -> dict:
        """
        Subtract the coefficients of two polynomial models, padding as needed.

        Args:
            model_high (dict): Model with higher or equal degree.
            model_low (dict): Model with lower or equal degree.

        Returns:
            dict: Model dictionary with subtracted coefficients.
        """
        deg_h = model_high['degree']
        deg_l = model_low['degree']
        
        coeffs_h = np.array(model_high['coeffs'])
        coeffs_l = np.array(model_low['coeffs'])
        
        # --- LÓGICA NOVA PARA 1D (Exp2) ---
        if model_high.get('type') == 'poly_1d':
            # Em 1D (numpy), a ordem é [x^N, x^N-1, ..., x^0]
            # Precisamos alinhar pelo final (x^0).
            # Ex: High(Len 6) - Low(Len 2). Low deve ser [0,0,0,0, b1, b0]
            
            diff_len = len(coeffs_h) - len(coeffs_l)
            if diff_len < 0:
                raise ValueError("Modelo High deve ter grau maior ou igual ao Low")
                
            # Preenche com zeros à ESQUERDA
            coeffs_l_padded = np.pad(coeffs_l, (diff_len, 0), 'constant')
            
            diff_coeffs = coeffs_h - coeffs_l_padded
            
        # --- LÓGICA ANTIGA PARA 2D (Exp1) ---
        else:
            # Estrutura Customizada: [x, y, x^2..., Bias]
            # O bias é o último. O resto cresce do índice 0.
            len_h = len(coeffs_h)
            coeffs_l_padded = np.zeros(len_h)
            
            # Copia Bias (último)
            coeffs_l_padded[-1] = coeffs_l[-1]
            
            # Copia termos crescentes
            terms_count = 2 * deg_l
            if terms_count > 0:
                coeffs_l_padded[0:terms_count] = coeffs_l[0:terms_count]
                
            diff_coeffs = coeffs_h - coeffs_l_padded
        
        return {
            "type": model_high['type'],
            "degree": deg_h,
            "coeffs": diff_coeffs.tolist(),
            "norm": model_high.get("norm")
        }

    @staticmethod
    def average_models(models: list) -> dict:
        """
        Compute the average of multiple polynomial models of the same degree.

        Args:
            models (list): List of model dictionaries (same degree required).

        Returns:
            dict: Model dictionary with averaged coefficients, or empty dict if input is empty.
        """
        if not models:
            return {}  # No models to average
        base = models[0]

        base_deg = base['degree']
        for m in models:
            if m['degree'] != base_deg:
                raise ValueError("All models must have the same degree for averaging.")

        all_coeffs = np.vstack([np.array(m['coeffs']) for m in models])
        avg_coeffs = np.mean(all_coeffs, axis=0)

        return {
            "type": base['type'],
            "degree": base['degree'],
            "coeffs": avg_coeffs.tolist(),
            "norm": base.get("norm")
        }