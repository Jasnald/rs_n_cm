
from ..importations import *

class Fitter:
    """
    Provides static methods for polynomial fitting and evaluation in 1D and 2D.
    """

    @staticmethod
    def _compose_linear_substitution(coef_t: np.ndarray, a: float, b: float) -> np.ndarray:
        """
        Recebe coeficientes em t (ordem crescente) e devolve coeficientes em x
        onde t = a*x + b, ou seja, p(a x + b).
        """
        out = np.zeros(1)
        linear = np.array([b, a])  # (b + a*x) em ordem crescente
        for c in coef_t[::-1]:  # Horner com ordem crescente
            out = np.polynomial.polynomial.polymul(out, linear)
            out[0] += c
        return out

    @staticmethod
    def fit_1d_poly(
        x: np.ndarray,
        z: np.ndarray,
        degree: int,
        normalize_x: bool = False,
        ridge_alpha: float = 0.0,
    ) -> dict:
        """
        Fit a 1D polynomial to x and z data.

        Args:
            x (np.ndarray): Input x values.
            z (np.ndarray): Input z values.
            degree (int): Degree of the polynomial.
            normalize_x (bool): Normalize x to [-1, 1] before fitting.
            ridge_alpha (float): Ridge regularization factor (0 for least squares).

        Returns:
            dict: Model dictionary with type, degree, coefficients, and normalization info.
        """

        x = np.asarray(x, dtype=float)
        z = np.asarray(z, dtype=float)

        if normalize_x:
            xmin, xmax = float(x.min()), float(x.max())
            if xmax == xmin:
                raise ValueError("Todos os x são iguais; não é possível normalizar.")
            a_lin = 2.0 / (xmax - xmin)
            b_lin = -(xmax + xmin) / (xmax - xmin)
            x_fit = a_lin * x + b_lin
        else:
            a_lin, b_lin = 1.0, 0.0
            x_fit = x

        X = np.column_stack([x_fit ** k for k in range(degree + 1)])
        if ridge_alpha > 0:
            xtx = X.T @ X
            xtx += ridge_alpha * np.eye(degree + 1)
            coeffs_fit = np.linalg.solve(xtx, X.T @ z)
        else:
            coeffs_fit, *_ = np.linalg.lstsq(X, z, rcond=None)

        if normalize_x:
            coeffs_inc = Fitter._compose_linear_substitution(coeffs_fit, a_lin, b_lin)
        else:
            coeffs_inc = coeffs_fit

        coeffs = coeffs_inc[::-1]

        return {
            "type": "poly_1d",
            "degree": degree,
            "coeffs": coeffs.tolist(),
            "norm": {
                "mean": float(np.mean(x)),
                "std": float(np.std(x)),
                "scale": a_lin,
                "shift": b_lin,
            },
            "fit": {
                "normalize_x": normalize_x,
                "ridge_alpha": float(ridge_alpha),
            },
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
