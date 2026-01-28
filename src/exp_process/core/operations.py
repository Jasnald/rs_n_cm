
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

        if deg_l > deg_h:
            raise ValueError("First model must have degree >= second model.")

        coeffs_h = np.array(model_high['coeffs'])
        coeffs_l = np.array(model_low['coeffs'])

        len_h = len(coeffs_h)
        len_l = len(coeffs_l)

        coeffs_l_padded = np.zeros(len_h)  # Pad lower model to match length

        coeffs_l_padded[-1] = coeffs_l[-1]  # Always copy constant term

        terms_count = 2 * deg_l
        if terms_count > 0:
            coeffs_l_padded[0:terms_count] = coeffs_l[0:terms_count]  # Copy matching terms

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