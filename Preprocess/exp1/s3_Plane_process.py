# -*- coding: utf-8 -*-
"""
s3_Plane_process.py
What it does:
This module provides functions for fitting, evaluating, and comparing polynomial 
and Chebyshev surfaces to 3D measurement data. It includes utilities for loading 
and normalizing data, building regression matrices, calculating fitted values, 
and saving results. The module supports both standard and 
Chebyshev polynomial fitting, with detailed evaluation and comparison routines.

Example of use:
    Run this script directly to fit and compare polynomial surfaces for all available sides in the 'Sample_postprocess' directory.

    python Plane_process.py
"""

import os
import glob
import re
import json
import logging
from typing import List, Tuple, Dict, Any, Optional
import sys
import numpy as np

# Importa funções do módulo de utilitários
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import plane_data_utils

# Configuração básica de logging (ajuste conforme necessário)
logging.basicConfig(level=logging.INFO)


def find_latest_iteration_files(directory: str, pattern: str = "Side*_Modified*") -> Dict[str, str]:
    """
    find_latest_iteration_files / (function)
    What it does:
    Searches the directory for files matching the specified pattern, returning a dictionary mapping each 'SideX' to the file corresponding to its latest iteration.
    """
    all_files = glob.glob(os.path.join(directory, pattern))
    if not all_files:
        logging.warning("Nenhum arquivo encontrado com o padrão especificado.")
        return {}

    files_by_side = {}
    for path in all_files:
        name = os.path.basename(path)
        m = re.match(r"(Side\d+)_Modified", name, re.IGNORECASE)
        side = m.group(1) if m else "UnknownSide"
        files_by_side[side] = path

    return files_by_side


def load_points(file_path: str) -> List[Tuple[float, float, float]]:
    """
    load_points / (function)
    What it does:
    Loads 3D points from a JSON file using plane_data_utils. The JSON must contain a 'steps' key. Returns a list of (x, y, z) tuples.
    """
    steps_data = plane_data_utils.load_steps_data_from_json(file_path)
    if steps_data:
        X, Y, Z = plane_data_utils.extract_points_from_steps_data(steps_data)
        # Converte os arrays NumPy para lista de tuplas
        return list(zip(X.tolist(), Y.tolist(), Z.tolist()))
    else:
        return []


# ===== FUNÇÕES PARA AJUSTE POLINOMIAL PADRÃO =====

def build_regression_matrix_xy(points: List[Tuple[float, float, float]], degree: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    build_regression_matrix_xy / (function)
    What it does:
    Builds the regression matrix M and vector z for a standard polynomial fit using terms x^k, y^k (k from 1 to degree) and a constant term.
    """
    N = len(points)
    M = np.zeros((N, 2 * degree + 1))
    Z = np.zeros(N)

    for i, (x, y, z) in enumerate(points):
        col = 0
        for k in range(1, degree + 1):
            M[i, col] = x ** k
            col += 1
            M[i, col] = y ** k
            col += 1
        M[i, 2 * degree] = 1.0
        Z[i] = z

    return M, Z


def fit_polynomial_xy(points: List[Tuple[float, float, float]], degree: int) -> np.ndarray:
    """
    fit_polynomial_xy / (function)
    What it does:
    Fits a standard polynomial in x and y of the specified degree to the given points. Returns the fitted parameters as a NumPy array.
    """
    M, Z = build_regression_matrix_xy(points, degree)
    params, _, _, _ = np.linalg.lstsq(M, Z, rcond=None)
    return params


def calculate_z_polynomial(params: np.ndarray, x: float, y: float, degree: int) -> float:
    """
    Calcula Z usando os coeficientes ajustados.
    Detecta automaticamente se é um ajuste 1D (perfil) ou 2D (superfície).
    """
    # CASO 1: Polinômio 1D (Perfil Y-Z)
    # Se o número de parâmetros for exatamente (grau + 1), é um ajuste simples 1D.
    # Ex: Grau 2 -> [a0, a1, a2] (3 params)
    if params.size == degree + 1:
        # Assume variação em Y (Baseado no s2_Outline_gui que plota Y vs Z)
        # Se sua peça for orientada em X, mude 'y' para 'x' aqui.
        return float(np.polynomial.polynomial.polyval(y, params))

    # CASO 2: Polinômio 2D (Superfície X-Y)
    # Se tem mais parâmetros, usa a lógica original bivariada
    else:
        z_calc = 0.0
        idx = 0
        for k in range(1, degree + 1):
            # Proteção para não estourar índice se o array estiver incompleto
            if idx + 1 >= params.size:
                break

            a_k = params[idx]
            b_k = params[idx + 1]
            idx += 2
            z_calc += a_k * (x ** k) + b_k * (y ** k)

        # Adiciona termo constante
        # Nota: Usamos -1 para pegar o último elemento, que é o padrão robusto
        if params.size > 0:
            z_calc += params[-1]
        return float(z_calc)


def evaluate_polynomial_fit(points: List[Tuple[float, float, float]],
                            params: np.ndarray,
                            degree: int) -> Tuple[float, float, float]:
    """
    evaluate_polynomial_fit / (function)
    What it does:
    Calculates the residuals of the standard polynomial fit and returns the MSE, RMSE, and maximum error.
    """
    residuals = []
    for x, y, z in points:
        z_fit = calculate_z_polynomial(params, x, y, degree)
        residuals.append(z - z_fit)

    residuals_arr = np.array(residuals)
    mse = np.mean(residuals_arr ** 2)
    rmse = np.sqrt(mse)
    max_err = np.max(np.abs(residuals_arr))
    return mse, rmse, max_err


def build_equation_string(params: np.ndarray, degree: int) -> str:
    """
    build_equation_string / (function)
    What it does:
    Builds and formats a string representing the fitted standard polynomial equation.
    """
    parts = []
    idx = 0
    for k in range(1, degree + 1):
        a_k = params[idx]
        b_k = params[idx + 1]
        idx += 2
        parts.append(f"{a_k:.10f} * x^{k}")
        parts.append(f"{b_k:.10f} * y^{k}")
    c = params[-1]
    parts.append(f"{c:.10f}")

    equation = "z = " + parts[0]
    for p in parts[1:]:
        equation += "\n    + " + p
    return equation


# ===== FUNÇÕES PARA AJUSTE COM POLINÔMIOS DE CHEBYSHEV =====

def chebyshev_polynomial(n: int, x: np.ndarray) -> np.ndarray:
    """
    chebyshev_polynomial / (function)
    What it does:
    Computes the Chebyshev polynomial of the first kind Tn(x) using recurrence.
    """
    if n == 0:
        return np.ones_like(x)
    elif n == 1:
        return x

    T_nm2 = np.ones_like(x)
    T_nm1 = x
    for i in range(2, n + 1):
        T_n = 2 * x * T_nm1 - T_nm2
        T_nm2 = T_nm1
        T_nm1 = T_n
    return T_nm1


def build_chebyshev_matrix(points: List[Tuple[float, float, float]], degree: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    build_chebyshev_matrix / (function)
    What it does:
    Builds the regression matrix M and vector z for Chebyshev polynomial fitting in normalized variables (x_norm, y_norm).
    """
    N = len(points)
    num_features = (degree + 1) * (degree + 1)
    M = np.zeros((N, num_features))
    Z = np.zeros(N)

    for i, (x_norm, y_norm, z) in enumerate(points):
        col = 0
        for i_deg in range(degree + 1):
            T_i = chebyshev_polynomial(i_deg, np.array([x_norm]))[0]
            for j_deg in range(degree + 1):
                T_j = chebyshev_polynomial(j_deg, np.array([y_norm]))[0]
                M[i, col] = T_i * T_j
                col += 1
        Z[i] = z

    return M, Z


def normalize_data(points: List[Tuple[float, float, float]]) -> Tuple[List[Tuple[float, float, float]], Dict[str, float]]:
    """
    normalize_data / (function)
    What it does:
    Normalizes the x and y coordinates to the range [-1, 1]. Returns the normalized points and the parameters (min and max) used for normalization.
    """
    xyz = np.array(points)
    x = xyz[:, 0]
    y = xyz[:, 1]
    z = xyz[:, 2]

    x_min, x_max = np.min(x), np.max(x)
    y_min, y_max = np.min(y), np.max(y)

    x_norm = 2.0 * (x - x_min) / (x_max - x_min) - 1.0
    y_norm = 2.0 * (y - y_min) / (y_max - y_min) - 1.0

    normalized_points = [(x_norm[i], y_norm[i], z[i]) for i in range(len(z))]
    norm_params = {
        'x_min': x_min, 'x_max': x_max,
        'y_min': y_min, 'y_max': y_max
    }

    return normalized_points, norm_params


def fit_chebyshev_polynomial(points: List[Tuple[float, float, float]], degree: int) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    fit_chebyshev_polynomial / (function)
    What it does:
    Fits a Chebyshev polynomial (with prior normalization) to the (x, y, z) points. Returns the fitted coefficients and normalization parameters.
    """
    normalized_points, norm_params = normalize_data(points)
    M, Z = build_chebyshev_matrix(normalized_points, degree)
    params, _, _, _ = np.linalg.lstsq(M, Z, rcond=None)
    return params, norm_params


def calculate_z_chebyshev(params: np.ndarray, x: float, y: float, degree: int,
                           norm_params: Dict[str, float]) -> float:
    """
    calculate_z_chebyshev / (function)
    What it does:
    Calculates the z value for a point (x, y) using the fitted Chebyshev coefficients. Normalizes (x, y) based on norm_params.
    """
    x_norm = 2.0 * (x - norm_params['x_min']) / (norm_params['x_max'] - norm_params['x_min']) - 1.0
    y_norm = 2.0 * (y - norm_params['y_min']) / (norm_params['y_max'] - norm_params['y_min']) - 1.0

    z_calc = 0.0
    param_idx = 0
    for i_deg in range(degree + 1):
        T_i = chebyshev_polynomial(i_deg, np.array([x_norm]))[0]
        for j_deg in range(degree + 1):
            T_j = chebyshev_polynomial(j_deg, np.array([y_norm]))[0]
            z_calc += params[param_idx] * (T_i * T_j)
            param_idx += 1

    return z_calc


def evaluate_chebyshev_fit(points: List[Tuple[float, float, float]],
                           params: np.ndarray,
                           degree: int,
                           norm_params: Dict[str, float]) -> Tuple[float, float, float]:
    """
    evaluate_chebyshev_fit / (function)
    What it does:
    Calculates the residuals of the Chebyshev fit and returns the MSE, RMSE, and maximum error.
    """
    residuals = []
    for x, y, z in points:
        z_fit = calculate_z_chebyshev(params, x, y, degree, norm_params)
        residuals.append(z - z_fit)

    residuals_arr = np.array(residuals)
    mse = np.mean(residuals_arr ** 2)
    rmse = np.sqrt(mse)
    max_err = np.max(np.abs(residuals_arr))
    return mse, rmse, max_err


def build_chebyshev_equation_string(params: np.ndarray, degree: int) -> str:
    """
    build_chebyshev_equation_string / (function)
    What it does:
    Builds a string representing the equation obtained by fitting Chebyshev polynomials.
    """
    equation = "z = "
    terms = []
    param_idx = 0
    for i_deg in range(degree + 1):
        for j_deg in range(degree + 1):
            coef = params[param_idx]
            if abs(coef) > 1e-10:
                terms.append(f"{coef:.6f} * T_{i_deg}(x_norm) * T_{j_deg}(y_norm)")
            param_idx += 1

    if terms:
        equation += terms[0]
        for term in terms[1:]:
            if term.startswith('-'):
                equation += "\n    " + term
            else:
                equation += "\n    + " + term
    else:
        equation += "0.0"

    equation += "\n\nOnde T_n é o polinômio de Chebyshev de 1ª espécie."
    equation += "\n(x_norm, y_norm) são coordenadas normalizadas em [-1, 1]."
    return equation





# ===== FUNÇÃO EXPERIMENTAL UNIFICADA PARA OS DOIS MÉTODOS =====

def experiment_method(base_directory: str, max_degree: int, method: str) -> Dict[str, Any]:
    """
    experiment_method / (function)
    What it does:
    For each file (by side) found in the directory, fits polynomials of degree 1 to max_degree using the specified method ('Standard' or 'Chebyshev') and stores the results.
    """
    files_by_side = find_latest_iteration_files(base_directory)
    if not files_by_side:
        return {}

    final_results = {}

    for side, file_path in files_by_side.items():
        logging.info(f"\n=== Processando {side} com polinômios {method} ===")
        points = load_points(file_path)
        if not points:
            logging.warning(f"Nenhum ponto encontrado para {side}. Pulando.")
            continue

        best_degree = None
        best_rmse = float('inf')
        results_side = {}

        for degree in range(1, max_degree + 1):
            logging.info(f"Ajustando polinômio de grau {degree} para {side} usando {method}...")
            if method.lower() == "chebyshev":
                params, norm_params = fit_chebyshev_polynomial(points, degree)
                mse, rmse, max_err = evaluate_chebyshev_fit(points, params, degree, norm_params)
                eq_str = build_chebyshev_equation_string(params, degree)
                calc_func = calculate_z_chebyshev
            else:
                params = fit_polynomial_xy(points, degree)
                mse, rmse, max_err = evaluate_polynomial_fit(points, params, degree)
                eq_str = build_equation_string(params, degree)
                calc_func = calculate_z_polynomial
                norm_params = None

            logging.info(f"  MSE={mse:.6f}, RMSE={rmse:.6f}, MaxErr={max_err:.6f}")

            plane_data_utils.save_plane_data_json(
                side=side,
                points=points,
                params=params,
                degree=degree,
                method_name=method,
                eq_str=eq_str,
                base_directory=os.path.join(base_directory, "Planes_data"),
                calculate_z_func=calc_func,
                norm_params=norm_params
            )

            results_side[degree] = {
                'params': params.tolist(),
                'equation': eq_str,
                'mse': mse,
                'rmse': rmse,
                'max_err': max_err,
                'norm_params': norm_params
            }

            if rmse < best_rmse:
                best_rmse = rmse
                best_degree = degree

        final_results[side] = {
            'best_degree': best_degree,
            'best_rmse': best_rmse,
            'results_by_degree': results_side
        }

    return final_results


def compare_standard_vs_chebyshev(base_directory: str, max_degree: int = 10) -> Dict[str, Dict[str, Any]]:
    """
    compare_standard_vs_chebyshev / (function)
    What it does:
    Performs both standard and Chebyshev polynomial fitting and compares the results (RMSE) for each side. Logs the comparison and returns the results for both methods.
    """
    logging.info("\n=== COMPARAÇÃO: POLINÔMIO PADRÃO VS CHEBYSHEV ===")

    logging.info("\n=== AJUSTE PADRÃO ===")
    std_results = experiment_method(base_directory, max_degree, "Standard")

    logging.info("\n=== AJUSTE CHEBYSHEV ===")
    cheb_results = experiment_method(base_directory, max_degree, "Chebyshev")

    logging.info("\n=== COMPARAÇÃO DOS RESULTADOS ===")
    for side in std_results.keys():
        if side in cheb_results:
            std_best = std_results[side]['best_degree']
            std_rmse = std_results[side]['best_rmse']
            cheb_best = cheb_results[side]['best_degree']
            cheb_rmse = cheb_results[side]['best_rmse']

            logging.info(f"\nSide: {side}")
            logging.info(f"  Padrão: Grau ótimo = {std_best}, RMSE = {std_rmse:.6f}")
            logging.info(f"  Chebyshev: Grau ótimo = {cheb_best}, RMSE = {cheb_rmse:.6f}")

            if cheb_rmse < std_rmse:
                improvement = (1 - cheb_rmse / std_rmse) * 100
                logging.info(f"  Melhoria com Chebyshev: {improvement:.2f}%")
            else:
                degradation = (cheb_rmse / std_rmse - 1) * 100
                logging.info(f"  Padrão melhor por: {degradation:.2f}%")

    return {'standard': std_results, 'chebyshev': cheb_results}


def main() -> None:
    """
    main / (function)
    What it does:
    Main execution function. Searches for files in 'Sample_postprocess', fits standard and Chebyshev polynomials (up to degree 10), compares the results, and prints a summary.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "Sample_postprocess")

    maximum_degree = 10
    results = compare_standard_vs_chebyshev(input_dir, max_degree=maximum_degree)

    logging.info("\n=== Resumo Final ===")
    for method, method_results in results.items():
        logging.info(f"\nMétodo: {method.upper()}")
        for side, side_data in method_results.items():
            logging.info(f"  Side: {side}")
            logging.info(f"    Grau ótimo: {side_data['best_degree']}")
            logging.info(f"    Melhor RMSE: {side_data['best_rmse']:.6f}")


if __name__ == "__main__":
    main()