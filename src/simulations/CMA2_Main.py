"""
CM_Main.py
What it does:
This module orchestrates the workflow for running parameterized simulation batches using Abaqus and post-processing the results. It loads configuration data from JSON, generates parameter combinations for mesh and material properties, manages simulation directories, executes simulation scripts, and handles batch post-processing and conversion of results for visualization. The workflow is designed to automate the setup, execution, and conversion of multiple simulation cases, making it easier to manage large-scale computational studies.

Example of use:
    python CM_Main.py
    # or, from another script:
    from Modules_CMA.CM_Main import main
    main(default_process=True, convertion_process=True)
"""
# -*- coding: utf-8 -*-
import os
import inspect
import subprocess
import sys
import json
import numpy as np
import shutil
import glob
import meshio
import customtkinter
import h5py
import plotly
import narwhals
import pkgutil

sys.dont_write_bytecode = True
_here       = os.path.abspath(__file__)
_u_one      = os.path.dirname(_here)
_u_two      = os.path.dirname(_u_one)


sys.path.append(_here)
sys.path.append(_u_one)
sys.path.append(_u_two)


from cma2 import *

from src.Exp_Data.s1_exp.write_input    import AbaqusParameters
from cma.INP_Runner                     import INP_Runner
from cma.Clear_directory                import clear_directory


from cma.CM_Main import (generate_parameter_combinations, 
                                 run_script, 
                                 run_simulation_batch,
                                 load_configuration,
                                 #print_configuration_summary
                         )

from Conversor import NPY2XDMFParameters,NpyBatchToXdmfConverter

def _run_default_cma(clear=True):
    """
    _run_default_cma / (function)
    What it does:
    Runs the default Contour Method Analysis (CMA) workflow: 
    loads configuration, optionally clears the simulation directory, 
    generates parameter combinations, runs all simulations, 
    and post-processes results using batch processors and runners. 
    This function automates the full simulation and post-processing pipeline.
    """
    config_data, params = load_configuration()
    
    # Imprimir resumo da configuração
    # print_configuration_summary(config_data)
    
    # Obter parâmetros da configuração
    e_modulus       = config_data.get(
                    "material_properties", {}).get("elastic_modulus")
    poisson         = config_data.get(
                    "material_properties", {}).get("poisson_ratio", 0.0)
    abaqus_params   = config_data.get(
                    "abaqus_parameters", {})
    
    # Configurar diretórios
    CM_simulation_dir = config_data.get("directories", {}).get("CM_directory")
    if clear:
        clear_directory(CM_simulation_dir)
        print(f"Diretório {CM_simulation_dir} foi limpo.")
    elif not clear:
        print(f"Diretório {CM_simulation_dir} não foi limpo.")
    clear_directory(CM_simulation_dir)
    
    sample_surface_script = os.path.join(M_CMA2_DIR, "ContourAnalysis.py")
    sample_surface_script = os.path.join(M_CMA2_DIR, "attempt2_copy.py")

    # Gerar combinações de parâmetros usando JSON (agora inclui parâmetros Abaqus)
    pl_sample_surface = generate_parameter_combinations(config_data)
    
    print(f"\nTotal de simulações a serem executadas: {len(pl_sample_surface)}")
    
    # Mostrar primeira combinação como exemplo
    if pl_sample_surface:
        print("\nExemplo da primeira combinação de parâmetros:")
        first_combo = pl_sample_surface[0]
        for key, value in first_combo.items():
            print(f"  - {key}: {value}")
    
    # Executar simulações
    run_simulation_batch(pl_sample_surface, CM_simulation_dir, sample_surface_script)
    
    # Cria e executa o processador
    batch_processor = BatchINPProcessor(
        base_dir        = CM_simulation_dir,
        e_modulus       = e_modulus,
        poisson         = poisson,
        abaqus_params   = abaqus_params)
    
    batch_processor.run_all()

    # Executar simulações
    runner = INP_Runner(CM_simulation_dir)
    runner.run_all_simulations()

def _run_convertion_process(
        method_type     = "Contour_Method",
        method_type_dir = "CM_directory",
        cwd             = None):
    
    T2T_str = 'ODB_2_XDMF'
    cmd = f"abaqus python {T2T_str}.py"
    subprocess.run(cmd, shell=True, cwd=cwd)

    params_loader = NPY2XDMFParameters(
        method_type     = method_type,
        method_type_dir = method_type_dir)
    
    npy_root, out_dir, opts = params_loader.run()
    npy_root = os.path.join(npy_root, "npy_files")
    # 2) Converte em batch
    batch = NpyBatchToXdmfConverter(npy_root, out_dir, opts)
    batch.convert_all()

    print(45*"=" + "\n" + 10*"=" + " WORKFLOW DE SIMULAÇÃO CONCLUÍDO COM SUCESSO! " + "\n"+ 45*"="+ "\n")

def main(default_process=True, convertion_process=True):
    """
    main / (function)
    What it does:
    Main entry point for the simulation workflow. Runs the default
    simulation process and/or the conversion process depending on
    the provided flags. Intended to be called as a script or
    imported and called from another module.
    """
    print("INICIANDO WORKFLOW DE SIMULAÇÃO ABAQUS")
    # processo padrão completo
    if default_process      : _run_default_cma          (clear=True)
    if convertion_process   : _run_convertion_process   (cwd=M_CMA2_DIR)
    

if __name__ == "__main__":
    main(default_process    = True, 
         convertion_process = True)