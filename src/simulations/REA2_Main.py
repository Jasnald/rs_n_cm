"""
REA_Main.py
What it does:
This module manages the workflow for Residual Stresses Analysis (RSA) simulations, including configuration loading, parameter combination generation, simulation execution, post-processing, and conversion of results for visualization. It automates the setup and execution of multiple simulation cases, as well as the integration with Contour Method Analysis (CMA) workflows when needed.

Example of use:
    python REA_Main.py
    # or, from another script:
    from Modules_RSA.REA_Main import main
    main(run_cma=True, run_rsa=True, convertion_process_rsa=True)
"""
import subprocess
import os
import sys
import numpy as np
import inspect
import json
import pandas as pd
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
# Importar scripts do projeto

from rsa2 import *


from Exp_Data.s1_exp.write_input import AbaqusParameters
from cma.Clear_directory import clear_directory
from cma.CM_Main import (generate_parameter_combinations,
                                          run_script,
                                          run_simulation_batch,
                                          load_configuration,
                                          _run_convertion_process)
from cma.INP_Runner import INP_Runner
from rsa2.Set_Creator_Inp import BatchInpStressUpdaterFI    

from Simulations.CMA2_Main import (
    _run_default_cma,
    main as cm_main)

def _run_default_rsa(clear=True):
    """
    _run_default_rsa / (function)
    What it does:
    Runs the default Residual Stresses Analysis (RSA) workflow: 
    loads configuration, optionally clears the simulation directory, 
    generates parameter combinations, runs all simulations, 
    post-processes results, updates INP files, and executes all simulation runs. 
    Integrates with other modules for node extraction and stress processing.
    """
    # Carregar configuração
    config_data, params = load_configuration()

    # Obter parâmetros da configuração
    e_modulus       = config_data.get(
                    "material_properties", {}).get("elastic_modulus")
    poisson         = config_data.get(
                    "material_properties", {}).get("poisson_ratio", 0.0)
    abaqus_params   = config_data.get(
                    "abaqus_parameters", {})

    # Configurar diretórios
    REA_simulation_dir = config_data.get("directories", {}).get("REA_directory")
    if clear:
        clear_directory(REA_simulation_dir)
        print(f"Diretório {REA_simulation_dir} foi limpo.")
    elif not clear:
        print(f"Diretório {REA_simulation_dir} não foi limpo.")

    REA_Model_dir = os.path.join(BASE_DIR,  "REA_Extended2.py")
    #REA_Model_dir = r"V:\02_SHK\05_dgl_gm\08_Project\Mudules_abaqus\attempt\REA_Extended.py"

    pl_sample_surface = generate_parameter_combinations(config_data)

    print(f"Total de simulações a serem executadas: {len(pl_sample_surface)}")

    # Executar simulações
    run_simulation_batch(pl_sample_surface, REA_simulation_dir, REA_Model_dir)

    from ElementProcess.Elements_main import Nodes_main
    Nodes_main(
        REA_simulation_dir, 
        use_s1 = True, 
        use_s2 = False, 
        use_s3 = False)

    from ElementProcess.s2_RE_ExnCon2 import StressProcessorBatch
    CM_simulation_dir   = config_data.get("directories", {}).get("CM_directory")
    CM_hdf5_dir         = os.path.join(CM_simulation_dir, "xdmf_hdf5_files")

    processor = StressProcessorBatch(
        REA_simulation_dir, 
        tolerance   = 5e-2, 
        chunk_size  = 10000)
    
    processor.process_all_simulations(CM_hdf5_dir)


    # Processar arquivos INP
    instance_name = "T_SHAPE_PART-1"
    batch_updater = BatchInpStressUpdaterFI(
        base_dir        = REA_simulation_dir, 
        instance_name   = instance_name,
        e_modulus       = e_modulus,
        poisson         = poisson,
        abaqus_params   = abaqus_params)

    batch_updater.run_all()

    # Executar simulações
    runner = INP_Runner(REA_simulation_dir)
    runner.run_all_simulations()

def main(run_cma = True, 
         run_rsa = True, 
         convertion_process_rsa = True):
    """
    main / (function)
    What it does:
    Main entry point for the RSA workflow. Runs the CMA and/or RSA simulation processes
    and the conversion process depending on the provided flags. Intended to be called
    as a script or imported and called from another module.
    """
    if run_cma: cm_main(
        default_process     = True, 
        convertion_process  = True)

    if run_rsa: _run_default_rsa(clear=True)

    if convertion_process_rsa:
        _run_convertion_process(
            method_type     = "Residual_Stresses_Analysis", 
            method_type_dir = "REA_directory",
            cwd             = BASE_DIR)

if __name__ == "__main__":
    main(run_cma = True,
         run_rsa = True, 
         convertion_process_rsa = True)


