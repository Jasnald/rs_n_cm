import numpy as np

class SurfaceOps:
    @staticmethod
    def calculate_residuals(x, y, z_measured, fit_model):
        """
        Calcula (Z_medido - Z_modelo). 
        Isso é essencial para encontrar a rugosidade/imperfeição da superfície.
        """
        # 1. Calcular Z teórico usando o modelo
        # (Idealmente chamar Fitter.predict, vou simular aqui)
        # z_model = Fitter.predict(x, y, fit_model)
        
        # Placeholder para z_model (assumindo que já temos ou calculamos)
        z_model = np.zeros_like(z_measured) 
        
        # 2. Subtrair
        residuals = z_measured - z_model
        
        # Métricas básicas
        metrics = {
            "max_peak": np.max(residuals),
            "max_valley": np.min(residuals),
            "rms": np.sqrt(np.mean(residuals**2))
        }
        
        return residuals, metrics

    @staticmethod
    def subtract_planes(plane_a_model, plane_b_model):
        """
        Subtrai matematicamente dois modelos de plano (Coef A - Coef B).
        Útil para remover o tilt (Plano grau 1) da superfície real (Plano grau N).
        """
        # Requer alinhamento dos graus dos coeficientes
        pass