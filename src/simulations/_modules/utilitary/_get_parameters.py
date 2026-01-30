# -*- coding: utf-8 -*-
# _get_parameters.py

from ..imports import *
from mixin_logger import LoggerMixin

#class ParametersGetter(LoggerMixin):

def ParametersGetter():
    """
    get_parameters_from_environment / (function)
    What it does:
    Retrieves simulation parameters from environment variables, or returns default values if not found. Used for batch or automated runs.
    Returns:
        dict: Dictionary with parameters or default values.
    """
    try:
        # Tentar obter parâmetros do ambiente
        params_json = os.environ.get('SIMULATION_PARAMETERS')
        if params_json:
            parameters = json.loads(params_json)
            print("Parâmetros recebidos do ambiente:", parameters)
            return parameters
    except (json.JSONDecodeError, KeyError) as e:
        print("Erro ao decodificar parâmetros do ambiente:", e)
    
    # Valores padrão se não conseguir obter do ambiente
    default_params = {
        'mesh_size'     : 0.5,
        'comprimento'   : 10,
        'output_dir'    : os.path.join(
                            os.path.dirname(
                            os.path.abspath(
                            inspect.getfile(
                            inspect.currentframe())))),
        'initialInc'    : 0.01,
        'maxInc'        : 0.1,
        'maxNumInc'     : 100,
        'minInc'        : 0.001,
        'nlgeom'        : OFF,
        'time'          : 9.0
    }
    print("Usando parâmetros padrão:", default_params)
    return default_params

