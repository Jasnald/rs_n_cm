# -*- coding: utf-8 -*-
"""
ODB_2_XDMF.py
What it does:
Runs examples to convert Abaqus ODB files to XDMF+HDF5 format using batch conversion utilities. This script demonstrates how to set up and execute the conversion workflow for simulation results, making them compatible with visualization and post-processing tools.

Example of use:
    python ODB_2_XDMF.py
    # or, from another script:
    from Modules_CMA.ODB_2_XDMF import main
    main()
"""

import os
import sys
import inspect

import os, sys, inspect

sys.dont_write_bytecode = True
_here      = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
_parent_1  = os.path.dirname(_here)
_parent_2  = os.path.dirname(_parent_1)
for p in (_here, _parent_1, _parent_2):
    if p not in sys.path: sys.path.append(p)

from Conversor.Odb_Npz_Parameters import ODB2NPYParameters, OdbBatchConverter
from Conversor.Odb_Npz_Converter import OdbToNPYConverter


def main():
    """
    main / (function)
    What it does:
    Runs an example workflow to convert ODB files to XDMF+HDF5 format using 
    ODB2NPYParameters and OdbBatchConverter. Sets up parameters, 
    runs the batch conversion, and prepares results for visualization.
    """

    print("=== Exemplo 1: Contour Method ===")
    parameters = ODB2NPYParameters(
        method_type     = "Contour_Method", 
        method_type_dir = "CM_directory")
    Simulation_dir, XDMF_dir, conversion_params = parameters.run()
    
    converter = OdbBatchConverter(Simulation_dir, XDMF_dir, conversion_params)
    converter.convert_batch()
    
if __name__ == "__main__":
    main()