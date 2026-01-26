import numpy as np

class Fitter:
    """Centraliza algoritmos de ajuste de curvas e superfícies."""

    # --- Lógica 1D (Exp2) ---
    @staticmethod
    def fit_1d_poly(x: np.ndarray, z: np.ndarray, degree: int) -> dict:
        """
        Ajusta polinômio z = f(x).
        Retorna coeficientes e metadados de normalização para reproduzir o fit.
        """
        # Normalização Z-score para estabilidade numérica
        x_mean, x_std = np.mean(x), np.std(x)
        if x_std == 0: x_std = 1.0
        
        x_norm = (x - x_mean) / x_std
        
        # Ajuste
        coeffs = np.polyfit(x_norm, z, degree)
        
        return {
            "type": "poly_1d",
            "degree": degree,
            "coeffs": coeffs.tolist(),
            "norm": {"mean": float(x_mean), "std": float(x_std)}
        }

    @staticmethod
    def eval_1d_poly(x: float, model: dict) -> float:
        """Avalia um modelo 1D gerado pelo fit_1d_poly."""
        norm = model["norm"]
        coeffs = model["coeffs"]
        
        x_norm = (x - norm["mean"]) / norm["std"]
        return np.polyval(coeffs, x_norm)

    # --- Lógica 2D (Exp1) ---
    @staticmethod
    def fit_2d_poly(x: np.ndarray, y: np.ndarray, z: np.ndarray, degree: int) -> dict:
        """
        Ajusta superfície polinomial z = f(x, y) usando Mínimos Quadrados.
        Baseado na lógica de matriz de Vandermonde do código antigo.
        """
        # Cria matriz de design: [1, x, y, x^2, y^2, ...] (Depende da implementação exata desejada)
        # Aqui simplificado para a lógica padrão de potências independentes ou mistas
        # Vou manter a lógica "xy" (x^k e y^k) vista no s3_Plane_process.py
        
        A = []
        for i in range(len(x)):
            row = []
            for k in range(1, degree + 1):
                row.append(x[i]**k)
                row.append(y[i]**k)
            row.append(1.0) # Termo constante
            A.append(row)
            
        A = np.array(A)
        b = z
        
        coeffs, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
        
        return {
            "type": "poly_2d",
            "degree": degree,
            "coeffs": coeffs.tolist()
        }