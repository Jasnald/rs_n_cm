from importations import *

class Fitter:

    @staticmethod
    def fit_1d_poly(x: np.ndarray, z: np.ndarray, degree: int) -> dict:

        x_mean, x_std = np.mean(x), np.std(x)
        if x_std == 0: x_std = 1.0
        
        x_norm = (x - x_mean) / x_std

        coeffs = np.polyfit(x_norm, z, degree)
        
        return {
            "type": "poly_1d",
            "degree": degree,
            "coeffs": coeffs.tolist(),
            "norm": {"mean": float(x_mean), "std": float(x_std)}
        }

    @staticmethod
    def eval_1d_poly(x: float, model: dict) -> float:

        norm = model["norm"]
        coeffs = model["coeffs"]
        
        x_norm = (x - norm["mean"]) / norm["std"]
        return np.polyval(coeffs, x_norm)

    @staticmethod
    def fit_2d_poly(x: np.ndarray, y: np.ndarray, z: np.ndarray, degree: int) -> dict:

        A = []
        for i in range(len(x)):
            row = []
            for k in range(1, degree + 1):
                row.append(x[i]**k)
                row.append(y[i]**k)
            row.append(1.0) 
            A.append(row)
            
        A = np.array(A)
        b = z
        
        coeffs, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
        
        return {
            "type": "poly_2d",
            "degree": degree,
            "coeffs": coeffs.tolist()
        }

    @staticmethod
    def eval_2d_poly(x: np.ndarray, y: np.ndarray, model: dict) -> np.ndarray:

        degree = model['degree']
        coeffs = model['coeffs']
        
        z = np.zeros_like(x, dtype=float)

        idx = 0
        for k in range(1, degree + 1):
            z += coeffs[idx] * (x**k)
            idx += 1
            z += coeffs[idx] * (y**k)
            idx += 1

        z += coeffs[-1]
        
        return z