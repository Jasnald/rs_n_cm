#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Rebuild.py
What it does:
This script reconstructs a T-shaped region by generating a grid of points, updating their Z values using polynomial parameters from a JSON file, and saving the result in a compatible format for further analysis or simulation. It uses Shapely for geometric operations and supports flexible mesh density and parameter loading.

Example of use:
    Run this script directly to generate a rebuilt plane for the T-shape using parameters from 'Final_Average__5_average_subtraction.json'.

    python Rebuild.py
"""

import os
import json
import numpy as np

# --------------------------------------------------------------------
# 1. Importações Shapely
from shapely.geometry import Polygon, Point

# 2. Obtenção de dimensões (ajuste o import se precisar)
from Exp_Data.s1_exp.mean_dim import DimOne
# 3. Cálculo de z (conforme seu polinômio)
from exp1.s3_Plane_process import calculate_z_polynomial as calculate_z_func

# 4. Função para salvar dados (ajuste o import se precisar)
from plane_data_utils import save_plane_data_json

# --------------------------------------------------------------------
# Nova função: cria o polígono em T via Shapely para evitar "pontas" indesejadas
def create_t_polygon_shapely(t_dims):
    """
    create_t_polygon_shapely / (function)
    What it does:
    Returns a Shapely polygon representing the T-shape, constructed by uniting two rectangles (horizontal and vertical bars) based on the provided dimensions.
    """
    # Retângulo da barra horizontal
    horizontal_bar = Polygon([
        (0.0, 0.0),
        (t_dims['h_width'], 0.0),
        (t_dims['h_width'], t_dims['h_thickness']),
        (0.0, t_dims['h_thickness'])
    ])

    # Retângulo da barra vertical
    v_pos_x = t_dims['h_width'] - t_dims['offset_1'] - t_dims['offset_2']
    vertical_bar = Polygon([
        (v_pos_x, t_dims['h_thickness']),
        (v_pos_x + t_dims['v_width'], t_dims['h_thickness']),
        (v_pos_x + t_dims['v_width'], t_dims['h_thickness'] + t_dims['v_height']),
        (v_pos_x, t_dims['h_thickness'] + t_dims['v_height'])
    ])

    # União das duas barras em um único polígono
    t_polygon = horizontal_bar.union(vertical_bar)
    return t_polygon

# --------------------------------------------------------------------
# Geração de pontos dentro do polígono usando Shapely

def generate_points_in_shape_via_divisions(t_dims, Nx_h=10, Ny_h=5, Nx_v=5, Ny_v=10):

    """
    generate_points_in_shape_via_divisions / (function)
    What it does:
    Generates a grid of points inside the T-shaped region by subdividing the horizontal and vertical bars according to the specified mesh density. Removes duplicates and returns a list of unique (x, y, z) points.
    """

    # 1) Coordenadas da barra horizontal (retângulo)
    h_x_min = 0.0
    h_x_max = t_dims['h_width']
    h_y_min = 0.0
    h_y_max = t_dims['h_thickness']
    
    # 2) Coordenadas da barra vertical (retângulo)
    v_x_min = t_dims['h_width'] - t_dims['offset_1'] - t_dims['offset_2']
    v_x_max = v_x_min + t_dims['v_width']
    v_y_min = t_dims['h_thickness']
    v_y_max = v_y_min + t_dims['v_height']
    
    def subdivide_rectangle(x_min, x_max, y_min, y_max, Nx, Ny):
        """
        Gera Nx+1 pontos ao longo do eixo X e Ny+1 alongo do eixo Y,
        totalizando (Nx+1)*(Ny+1) pontos, inclusive as bordas.
        """
        rect_points = []
        for i in range(Nx + 1):
            # fração [0..1]
            frac_x = i / Nx  
            x = x_min + frac_x * (x_max - x_min)
            for j in range(Ny + 1):
                frac_y = j / Ny
                y = y_min + frac_y * (y_max - y_min)
                rect_points.append((x, y, 0.0))
        return rect_points
    
    # 3) Malha da barra horizontal e barra vertical
    h_mesh = subdivide_rectangle(h_x_min, h_x_max, h_y_min, h_y_max, Nx_h, Ny_h)
    v_mesh = subdivide_rectangle(v_x_min, v_x_max, v_y_min, v_y_max, Nx_v, Ny_v)
    
    # 4) Combina os pontos
    all_points = h_mesh + v_mesh
    
    # 5) (Opcional) remove duplicatas exatas (no caso de sobreposição de retângulos)
    #    Para evitar problemas de float, arredondamos as coordenadas antes de criar o set
    unique_points = set((round(px, 8), round(py, 8), round(pz, 8)) for (px, py, pz) in all_points)
    
    # Converte de volta para float padrão
    unique_points = [(float(px), float(py), float(pz)) for (px, py, pz) in unique_points]
    pontos = unique_points 
   
    return pontos

# --------------------------------------------------------------------
# Função que lê parâmetros de um JSON (conforme seu código preexistente)
def read_parameters_from_file(base_dir):
    """
    read_parameters_from_file / (function)
    What it does:
    Reads polynomial parameters and degree from a specified JSON file in the postprocess directory. Raises an error if required keys are missing.
    """
    params_folder = os.path.join(base_dir, "Sample_postprocess", "Choosed_plane")
    file_name = "Final_Average__5_average_subtraction.json"  # adjust if needed
    file_path = os.path.join(params_folder, file_name)

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    parameters = data.get("parameters")
    if parameters is None:
        raise ValueError(f"Key 'parameters' not found in {file_path}")
    
    degree = data.get("degree")
    if degree is None:
        raise ValueError(f"Key 'degree' not found in {file_path}")
    
    return parameters, degree

# --------------------------------------------------------------------
# Atualiza cada ponto (x,y,0) com o valor de z calculado a partir do polinômio
def update_points_with_parameters(points, parameters, degree):
    """
    update_points_with_parameters / (function)
    What it does:
    Updates a list of (x, y, 0) points by calculating the Z value using the provided polynomial parameters and degree. Converts Z to millimeters and returns the updated list.
    """
    updated_points = []
    for (x, y, _) in points:
        z_calc = calculate_z_func(parameters, x, y, degree)  # polynomial
        z_mm = z_calc * 100  # Convert to millimeters if needed
        updated_points.append((x, y, z_mm))
    return updated_points

# --------------------------------------------------------------------
def main():
    """
    main / (function)
    What it does:
    Main execution function. Generates a T-shaped grid, loads polynomial parameters, updates Z values, and saves the rebuilt plane as a JSON file for further use.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1) Obter as dimensões do T (dicionário)
    t_dims = DimOne()
    
    # 2) Cria o polígono T via Shapely (opcional, se precisar para outras operações)
    t_polygon = create_t_polygon_shapely(t_dims)

    # 3) Gera os pontos no interior do polígono usando as dimensões do dicionário
    n_factor = 1  # fator de aumento para aumentar a densidade de pontos
    pontos_internos = generate_points_in_shape_via_divisions(t_dims, 
                                                             Nx_h = 20*n_factor, 
                                                             Ny_h = 10*n_factor,
                                                             Nx_v = 20*n_factor, 
                                                             Ny_v = 50*n_factor)

    # 4) Lê os parâmetros do polinômio (se existirem) e atualiza z
    try:
        parameters, degree = read_parameters_from_file(base_dir)
        pontos_atualizados = update_points_with_parameters(pontos_internos, parameters, degree)
    except Exception as e:
        print("Não foi possível ler parâmetros do arquivo, pontos ficarão com z=0:")
        print(e)
        pontos_atualizados = pontos_internos

    # 5) Salva em JSON, usando a mesma estrutura que você já tinha
    side = "Avearege"
    method_name = "Rebuild"
    eq_str = "z = poly(...)"
    save_plane_data_json(
        side, 
        pontos_atualizados, 
        np.array(parameters) if 'parameters' in locals() else None, 
        degree if 'degree' in locals() else None, 
        method_name, 
        eq_str, 
        os.path.join(base_dir, "Sample_postprocess", "Choosed_plane"), 
        calculate_z_func
    )

    print("Processo finalizado com sucesso!")

# --------------------------------------------------------------------
if __name__ == "__main__":
    main()