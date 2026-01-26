"""
Choosed_plane.py
What it does:
This module provides tools to subtract fitted planes 
(using polynomial or Chebyshev methods) from measurement data, 
and to compute the average of such subtracted planes. 
It loads plane data from JSON files, fits new surfaces to the difference 
between two planes, and saves the resulting difference and 
average planes for further analysis. The script is designed to work with 
measurement data from two sides or conditions, and supports both standard 
polynomial and Chebyshev polynomial fitting.

Example of use:
    Run this script directly to process sample data in the "Sample_postprocess" directory, subtracting planes of specified degrees for each side, and computing the average of the resulting difference planes.

    python Choosed_plane.py
"""
import os
import numpy as np
import logging
from typing import Dict, Any, List

# Imports de plane_process
from exp1.s3_Plane_process import (
    calculate_z_polynomial,
    calculate_z_chebyshev,
    fit_polynomial_xy,
    fit_chebyshev_polynomial,
    build_equation_string,
    build_chebyshev_equation_string
)

# Imports de utilitários de dados
from plane_data_utils import (
    load_plane_data_from_json,
    extract_points_from_plane_data,
    save_plane_data_json
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def subtract_planes( plane1_data: Dict[str, Any], plane2_data: Dict[str, Any],
    side: str, base_directory: str ) -> Dict[str, Any]:
    """
    subtract_planes / (function)
    What it does:
    Subtracts the fitted values of two planes (plane1_data - plane2_data), fits a new polynomial or Chebyshev surface to the difference, and saves the resulting difference plane as a JSON file. Returns a dictionary with the new parameters and points.
    """

    # 1) Verifica método e grau de cada plano
    method1 = plane1_data.get('method_name', 'standard').lower()
    method2 = plane2_data.get('method_name', 'standard').lower()
    if method1 != method2:
        logging.warning(f"Métodos diferentes (plane1={method1}, plane2={method2}). Usaremos o do primeiro.")
    method_name = method1  # ou defina como preferir

    degree1 = plane1_data.get('degree', 1)
    degree2 = plane2_data.get('degree', 1)
    # Podemos adotar o maior grau como 'grau do plano de diferença'
    result_degree = max(degree1, degree2)

    # 2) Extrai pontos e valores ajustados z_fit1 e z_fit2
    X1, Y1, Z_orig1, Z_fit1, _ = extract_points_from_plane_data(plane1_data)
    X2, Y2, Z_orig2, Z_fit2, _ = extract_points_from_plane_data(plane2_data)

    # -- Verificação simples se as listas de pontos batem:
    #    (depende da sua aplicação, aqui assumimos que X1==X2, Y1==Y2, etc.)
    if len(X1) != len(X2):
        logging.error(f"Tamanho diferente de pontos: {len(X1)} vs {len(X2)}. Não dá para subtrair!")
        return {}

    # 3) Calcula a diferença de dados: z_diff
    z_diff = Z_fit1 - Z_fit2
    # Monta pontos = (x, y, z_diff)
    points_diff = [(X1[i], Y1[i], z_diff[i]) for i in range(len(X1))]

    # 4) Faz um novo ajuste polinomial ou Chebyshev para 'points_diff'
    if method_name == "chebyshev":
        # Ajusta Chebyshev
        new_params, new_norm_params = fit_chebyshev_polynomial(points_diff, result_degree)
        eq_str = build_chebyshev_equation_string(new_params, result_degree)
        calc_func = calculate_z_chebyshev
    else:
        # Ajusta polinômio padrão
        new_params = fit_polynomial_xy(points_diff, result_degree)
        new_norm_params = None
        eq_str = build_equation_string(new_params, result_degree)
        calc_func = calculate_z_polynomial

    # 5) Salva o "plano de diferença" como JSON, usando a função centralizada
    #    (equation, parâmetros, etc.).
    output_dir = os.path.join(base_directory, "Choosed_plane")
    save_plane_data_json( side=side, points=points_diff, params=new_params,
        degree=result_degree, method_name="subtraction", eq_str="Plano de diferença: " + eq_str,
        base_directory=output_dir, calculate_z_func=calc_func, norm_params=new_norm_params )

    # 6) Retorna um dicionário básico, se precisar
    return { "side": side, "method_name": "subtraction", "degree": result_degree,
        "parameters": new_params.tolist(), "normalization_parameters": new_norm_params,
        "equation": eq_str, "points": points_diff }


def find_plane_files(base_directory: str, side: str, degrees: List[int], method: str = "standard") -> Dict[int, str]:
    """
    find_plane_files / (function)
    What it does:
    Locates plane data files for a specific side and a list of degrees, returning a dictionary mapping degree to file path. Logs warnings if files are missing.
    """
    planes_data_dir = os.path.join(base_directory, "Planes_data")
    if not os.path.exists(planes_data_dir):
        logging.error(f"Diretório não encontrado: {planes_data_dir}")
        return {}
    
    result = {}
    for degree in degrees:
        file_name = f"{side}__{degree}_{method.lower()}.json"
        file_path = os.path.join(planes_data_dir, file_name)
        if os.path.exists(file_path):
            result[degree] = file_path
        else:
            logging.warning(f"Arquivo não encontrado: {file_path}")
    return result

def calculate_average_planes(subtracted_planes: List[Dict[str, Any]], base_directory: str) -> Dict[str, Any]:
    """
    calculate_average_planes / (function)
    What it does:
    Computes the average of the parameters from a list of subtracted planes, recalculates the fitted surface using the average parameters, and saves the resulting average plane as a JSON file. Returns a dictionary with the average parameters and recalculated points.
    """
    if not subtracted_planes:
        logging.error("Nenhum plano fornecido para calcular a média.")
        return {}
    
    method = subtracted_planes[0].get('method_name', 'standard').lower()
    degree = subtracted_planes[0].get('degree', 1)
    all_params = []
    norm_params_result = None
    
    for plane in subtracted_planes:
        p = plane.get('parameters', [])
        all_params.append(np.array(p, dtype=float))
        # Se for Chebyshev, guardamos a normalização do primeiro
        if 'normalization_parameters' in plane:
            norm_params_result = plane['normalization_parameters']
    
    if not all_params:
        logging.error("Não há parâmetros para calcular a média.")
        return {}
    
    # Aqui, de fato calculamos a média dos parâmetros
    avg_params = np.mean(all_params, axis=0)
    eq_str = f"Average of {len(subtracted_planes)} subtracted planes"
    
    # Seleciona a função de cálculo
    if method == 'chebyshev':
        calc_func = calculate_z_chebyshev
    else:
        calc_func = calculate_z_polynomial
    
    # Obter os (x, y) de algum dos sub-planes.
    # Normalmente assumimos que todos têm a mesma malha/pontos. 
    # Mas NUNCA reaproveitamos z direto.
    if 'points' in subtracted_planes[0]:
        base_points = subtracted_planes[0]['points']  # [(x1, y1, z...)...]
    else:
        logging.error("Pontos não encontrados nos planos subtraídos.")
        return {}

    # Recalcular z com os parâmetros médios
    recalculated_points = []
    for (x, y, _) in base_points:
        if method == 'chebyshev' and norm_params_result is not None:
            z_val = calculate_z_chebyshev( np.array(avg_params, dtype=float), x, y, degree, norm_params_result )
        else:
            z_val = calculate_z_polynomial( np.array(avg_params, dtype=float), x, y, degree )
        recalculated_points.append((x, y, z_val))

    # Salvar o novo "plano de média" com esses z recalculados
    output_dir = os.path.join(base_directory, "Choosed_plane")
    save_plane_data_json( side="Final_Average", points=recalculated_points, params=avg_params, 
                         degree=degree, method_name="average_subtraction", eq_str=eq_str, 
                         base_directory=output_dir, calculate_z_func=calc_func, norm_params=norm_params_result )
    
    average_data = { "method": "average_subtraction", "degree": degree, "parameters": avg_params.tolist(), "equation": eq_str, "points": recalculated_points }
    if norm_params_result:
        average_data["normalization_parameters"] = norm_params_result
    
    logging.info("Média dos planos subtraídos salva com sucesso.")
    return average_data

def main():
    """
    main / (function)
    What it does:
    Main execution function. Processes sample data by locating plane files, performing subtraction between planes of different degrees for each side, and computing the average of the resulting difference planes. Logs progress and errors.
    """

    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "Sample_postprocess")
    
    degrees_to_use = [1, 5]
    sides = ["Side1", "Side2"]
    method = "standard"
    
    subtracted_data_list = []
    for side in sides:
        logging.info(f"Processando {side}...")
        plane_files = find_plane_files(input_dir, side, degrees_to_use, method)
        if len(plane_files) != len(degrees_to_use):
            logging.warning(f"Alguns arquivos não foram encontrados para {side}: {plane_files.keys()}")
            continue
        
        # Carrega dados
        plane_data = {}
        for deg, filepath in plane_files.items():
            data = load_plane_data_from_json(filepath)
            if data:
                plane_data[deg] = data
            else:
                logging.error(f"Erro ao carregar plano para {side}, grau {deg}")
        
        # Se tudo certo, subtrai (grau 6 - grau 1)
        if len(plane_data) == len(degrees_to_use):
            sub_data = subtract_planes( plane_data[degrees_to_use[1]], 
                                       plane_data[degrees_to_use[0]], side, input_dir )
            subtracted_data_list.append(sub_data)
    
    # Se gerou alguma subtração, faz a média das subtrações
    if subtracted_data_list:
        avg_result = calculate_average_planes(subtracted_data_list, input_dir)
        logging.info("Processamento completo! Resultado médio:")
        #logging.info(avg_result)
    else:
        logging.error("Nenhum dado de subtração foi gerado; verifique se os arquivos existem.")


if __name__ == "__main__":
    main()