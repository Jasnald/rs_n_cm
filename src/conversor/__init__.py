# -*- coding: utf-8 -*-
import os, sys, inspect

print("Conversor is being imported...")

Type2Type_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(Type2Type_DIR)

# Insere só se ainda não existir
for p in (Type2Type_DIR, ROOT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)


__base_dir__   = Type2Type_DIR
__root_dir__   = ROOT_DIR

try:    from .Odb_Npz_Parameters import OdbBatchConverter, ODB2NPYParameters
except(ImportError,SyntaxError): pass

try:    from .Odb_Npz_Converter import OdbToNPYConverter
except(ImportError,SyntaxError): pass

try:    from .Npy_2_Xdmf import Npy2XdmfConverter, NPY2XDMFParameters, NpyBatchToXdmfConverter
except(ImportError,SyntaxError): pass

# Exporta caminhos se interessar a outros módulos
__all__ = [
        # Do ODB2NPZParameters
        'OdbBatchConverter', 'ODB2NPYParameters',

        # Do OdbToNPZConverter
        'OdbToNPYConverter',

        # Do Npy_2_Xdmf
        'Npy2XdmfConverter', 'NPY2XDMFParameters', 'NpyBatchToXdmfConverter',

        'Type2Type_DIR', 'ROOT_DIR']
