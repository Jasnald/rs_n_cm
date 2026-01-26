from importations import *

class ModelOps:

    @staticmethod
    def subtract_coeffs(model_a: dict, model_b: dict) -> dict:

        if model_a['type'] != model_b['type'] or model_a['degree'] != model_b['degree']:
            raise ValueError("Modelos incompatíveis para subtração direta.")

        coeffs_a = np.array(model_a['coeffs'])
        coeffs_b = np.array(model_b['coeffs'])
        
        return {
            "type": model_a['type'],
            "degree": model_a['degree'],
            "coeffs": (coeffs_a - coeffs_b).tolist(),
            "norm": model_a.get("norm")
        }

    @staticmethod
    def average_models(models: list) -> dict:

        if not models: return {}
        base = models[0]

        all_coeffs = np.vstack([np.array(m['coeffs']) for m in models])
        avg_coeffs = np.mean(all_coeffs, axis=0)
        
        return {
            "type": base['type'],
            "degree": base['degree'],
            "coeffs": avg_coeffs.tolist(),
            "norm": base.get("norm")
        }