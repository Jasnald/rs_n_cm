#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rebuild_from_curve.py - Refatorado
Reconstrói um plano a partir dos parâmetros 1-D (curva) gerados por Choosed_curve.py.
"""

import os
import json
import numpy as np
import glob
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from set_dir import _set_dir
current_dir, root_dir = _set_dir()

from Modules_Exp_Data.s2_exp.Mean_dim_workpiece import Mean_dim_workpiece
from plane_data_utils import save_plane_data_json


def evaluate_curve(params: np.ndarray, x: float) -> float:
    return np.polynomial.polynomial.polyval(x, params)


def pega_parametros_e_degree(json_path):
    """Pega os parâmetros e degree do arquivo JSON"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    params = data.get("params")
    degree = data.get("degree")
    
    if params is None or degree is None:
        raise ValueError(f"Campos 'params' ou 'degree' ausentes em {json_path}")
    
    return np.array(params), degree

def calcula_z_da_curva(params, x):
    """Função que consegue pegar os parâmetros e com valores de x retorna z"""
    return evaluate_curve(params, x) 

def cria_malha_extrudada(dims, params, Nx=200, Ny=10):
    """Cria a malha do tamanho W,H com valores de z calculados da curva"""
    W, H = dims['avg_height'] , dims['avg_width']
    pontos = []
    
    for i in range(Nx + 1):
        x = i / Nx * W
        z = calcula_z_da_curva(params, x) 
        
        for j in range(Ny + 1):
            y = j / Ny * H
            pontos.append((x, y, z))  # Mesmo Z para todos os Y (extrusão)
    
    return pontos

def escreve_json_reconstruido(sample_name, pontos, params, degree, out_dir):
    """Escreve o JSON com a chamada da save_plane_data_json"""
    
    def calc_z_wrapper(params_arg, x, y, degree_arg):
        """Wrapper para compatibilidade com save_plane_data_json"""
        return calcula_z_da_curva(params_arg, x)   # Volta para escala original
    
    save_plane_data_json(
        sample_name,              # side
        pontos,                   # pontos
        params,                   # coeficientes
        degree,                   # grau
        "Rebuild_from_curve",     # método
        "z = Σ a_j x^j",         # string da equação
        out_dir,                  # pasta de destino
        calc_z_wrapper            # função de cálculo
    )

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    curve_dir = os.path.join(base_dir, "Sample_postprocess", "Choosed_curve")
    out_dir = os.path.join(base_dir, "Sample_postprocess", "Choosed_plane")
    os.makedirs(out_dir, exist_ok=True)

    dims = Mean_dim_workpiece()
    
    pattern = os.path.join(curve_dir, "Sample*_Subtraction.json")
    files = sorted(glob.glob(pattern))
    
    if not files:
        print("Nenhum arquivo *_Subtraction.json encontrado.")
        return

    for json_file in files:
        try:
            # 1. Pega parâmetros e degree
            params, degree = pega_parametros_e_degree(json_file)
            
            # 2. Cria malha extrudada
            pontos = cria_malha_extrudada(dims, params, Nx=100, Ny=100)
            
            # 3. Nome do sample
            sample_name = os.path.splitext(os.path.basename(json_file))[0].replace("_Subtraction", "")
            
            # 4. Escreve JSON
            escreve_json_reconstruido(sample_name, pontos, params, degree, out_dir)
            
            print(f"{sample_name}: superfície reconstruída e salva.")
            
        except Exception as e:
            print(f"Erro processando {json_file}: {e}")

    print(f"Reconstrução concluída para {len(files)} arquivos.")

if __name__ == "__main__":
    main()