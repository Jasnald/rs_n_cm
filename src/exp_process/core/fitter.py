
from ..importations import *

class Fitter:
    """
    Provides static methods for polynomial fitting and evaluation in 1D and 2D.
    """

    @staticmethod
    def fit_1d_poly(x: np.ndarray, z: np.ndarray, degree: int) -> dict:
        """
        Fit a 1D polynomial to normalized x and z data.

        Args:
            x (np.ndarray): Input x values.
            z (np.ndarray): Input z values.
            degree (int): Degree of the polynomial.

        Returns:
            dict: Model dictionary with type, degree, coefficients, and normalization info.
        """

        coeffs = np.polyfit(x, z, degree)
        return {
            "type": "poly_1d",
            "degree": degree,
            "coeffs": coeffs.tolist(),
            "norm": {"mean": float(np.mean(x)), "std": float(np.std(x))}
        }

    @staticmethod
    def eval_1d_poly(x: float, model: dict) -> float:
        """
        Evaluate a fitted 1D polynomial model at a given x value.

        Args:
            x (float): Input x value.
            model (dict): Model dictionary from fit_1d_poly.

        Returns:
            float: Evaluated polynomial value at x.
        """
        coeffs = model["coeffs"]
        # np.polyval espera a mesma ordem do polyfit (Decrescente)
        return np.polyval(coeffs, x)

    @staticmethod
    def fit_2d_poly(x: np.ndarray, y: np.ndarray, z: np.ndarray, degree: int) -> dict:
        """
        Fit a 2D polynomial (separable in x and y) to data.

        Args:
            x (np.ndarray): Input x values.
            y (np.ndarray): Input y values.
            z (np.ndarray): Input z values.
            degree (int): Degree of the polynomial.

        Returns:
            dict: Model dictionary with type, degree, and coefficients.
        """
        A = []
        for i in range(len(x)):
            row = []
            for k in range(1, degree + 1):
                row.append(x[i]**k)
                row.append(y[i]**k)
            row.append(1.0)  # Add constant term
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
        """
        Evaluate a fitted 2D polynomial model at given x, y values.

        Args:
            x (np.ndarray): Input x values.
            y (np.ndarray): Input y values.
            model (dict): Model dictionary from fit_2d_poly.

        Returns:
            np.ndarray: Evaluated polynomial values at (x, y).
        """
        degree = model['degree']
        coeffs = model['coeffs']
        z = np.zeros_like(x, dtype=float)
        idx = 0
        for k in range(1, degree + 1):
            z += coeffs[idx] * (x**k)  # Add x^k term
            idx += 1
            z += coeffs[idx] * (y**k)  # Add y^k term
            idx += 1
        z += coeffs[-1]  # Add constant term
        return z