#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Choosed_curve.py
Subtrai curvas ajustadas e calcula médias.
Adaptado para trabalhar com curvas 1D do s3_Curve_process.py
"""

import os
import json
import logging
import numpy as np
from typing import Dict, Any, List

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from set_dir import _set_dir
current_dir, root_dir = _set_dir()

# logger (use seu setup_logger ou logging padrão)
from utils import *

logging = setup_logger(__name__, clear=False)


def load_curve_data(json_path: str) -> Dict[str, Any]:
    """Carrega dados de curva de um JSON."""
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Erro ao carregar {json_path}: {e}")
        return {}

def evaluate_curve(params: List[float], x: float) -> float:
    """Avalia polinômio 1D: z = a0 + a1*x + a2*x^2 + ..."""
    return sum(params[j] * (x**j) for j in range(len(params)))

def fit_curve_1d(points: List[tuple], degree: int) -> np.ndarray:
    """Ajusta polinômio 1D aos pontos (x, z)."""
    N = len(points)
    M = np.zeros((N, degree+1))
    Z = np.zeros(N)
    
    for i, (x, z) in enumerate(points):
        Z[i] = z
        for j in range(degree+1):
            M[i, j] = x**j
    
    params, *_ = np.linalg.lstsq(M, Z, rcond=None)
    return params

def build_equation_string(params: List[float]) -> str:
    """Constrói string da equação."""
    terms = []
    for j, a in enumerate(params):
        if j == 0:
            terms.append(f"{a:.6f}")
        else:
            sign = "+" if a >= 0 else "-"
            terms.append(f" {sign} {abs(a):.6f}*x^{j}")
    return "z = " + "".join(terms)

def subtract_curves(curve1_data: Dict, curve2_data: Dict, sample_name: str, curves_dir: str) -> Dict:
    """Subtrai curve1 - curve2 e salva resultado."""
    
    # Extrai parâmetros
    params1 = curve1_data.get('params', [])
    params2 = curve2_data.get('params', [])
    degree1 = curve1_data.get('degree', len(params1)-1)
    degree2 = curve2_data.get('degree', len(params2)-1)
    
    # Simula pontos x para avaliar as curvas (assumindo range comum)
    x_points = np.linspace(-10, 10, 100)  # ajuste conforme necessário
    
    # Calcula diferença z1(x) - z2(x)
    diff_points = []
    for x in x_points:
        z1 = evaluate_curve(params1, x)
        z2 = evaluate_curve(params2, x)
        diff_points.append((x, z1 - z2))
    
    # Ajusta nova curva à diferença
    result_degree = max(degree1, degree2)
    new_params = fit_curve_1d(diff_points, result_degree)
    eq_str = build_equation_string(new_params.tolist())
    
    # Salva resultado
    result_data = {
        "sample": sample_name,
        "method": "subtraction",
        "degree": result_degree,
        "params": new_params.tolist(),
        "equation": eq_str,
        "original_degrees": [degree1, degree2]
    }
    
    output_path = os.path.join(curves_dir, f"{sample_name}_Subtraction.json")
    with open(output_path, 'w') as f:
        json.dump(result_data, f, indent=2)
    
    logging.info(f"Subtração salva: {output_path}")
    return result_data

def calculate_average_curves(subtracted_curves: List[Dict], curves_dir: str) -> Dict:
    """Calcula média dos parâmetros das curvas subtraídas."""
    
    if not subtracted_curves:
        return {}
    
    # Coleta parâmetros
    all_params = []
    degree = subtracted_curves[0].get('degree', 1)
    
    for curve in subtracted_curves:
        params = curve.get('params', [])
        all_params.append(np.array(params))
    
    # Calcula média
    avg_params = np.mean(all_params, axis=0)
    eq_str = build_equation_string(avg_params.tolist())
    
    # Salva média
    avg_data = {
        "method": "average_subtraction",
        "degree": degree,
        "params": avg_params.tolist(),
        "equation": eq_str,
        "num_curves_averaged": len(subtracted_curves)
    }
    
    output_path = os.path.join(curves_dir, "Average_Subtraction.json")
    with open(output_path, 'w') as f:
        json.dump(avg_data, f, indent=2)
    
    logging.info(f"Média salva: {output_path}")
    return avg_data

def main():
    """Processa curvas: subtrai graus especificados e calcula média."""
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    post_dir = os.path.join(base_dir, "Sample_postprocess")
    curves_input = os.path.join(post_dir, "Curves")
    curves_output = os.path.join(post_dir, "Choosed_curve")
    
    os.makedirs(curves_output, exist_ok=True)
    
    # Configuração: graus a subtrair
    deg_high = 2
    deg_low = 1
    
    subtracted_results = []
    
    # Processa cada sample
    for sample_num in range(1, 10):  # ajuste range conforme necessário
        sample_name = f"Sample{sample_num}"
        
        # Busca arquivos de grau alto e baixo
        file_high = os.path.join(curves_input, f"{sample_name}_Curve_deg{deg_high}.json")
        file_low = os.path.join(curves_input, f"{sample_name}_Curve_deg{deg_low}.json")
        
        if not (os.path.exists(file_high) and os.path.exists(file_low)):
            continue
        
        # Carrega dados
        curve_high = load_curve_data(file_high)
        curve_low = load_curve_data(file_low)
        
        if not (curve_high and curve_low):
            continue
        
        # Subtrai e salva
        result = subtract_curves(curve_high, curve_low, sample_name, curves_output)
        if result:
            subtracted_results.append(result)
    
    # Calcula e salva média
    if subtracted_results:
        calculate_average_curves(subtracted_results, curves_output)
        logging.info(f"Processamento completo! {len(subtracted_results)} curvas processadas.")
    else:
        logging.warning("Nenhuma curva foi processada.")

if __name__ == "__main__":
    main()