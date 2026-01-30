# -*- coding: utf-8 -*-
"""
Pacote _get_classes

Este pacote agrega as classes necessárias para configurar
e manipular funcionalidades do ABAQUS.
"""

print("Importando pacote '_get_classes'...")

from . import (
    assigment,
    core,
    geometry,
    geometry_setup,
    utilitary,
    imports
)


from .assigment      import *
from .core           import *
from .geometry       import *
from .geometry_setup import *
from .utilitary      import *
from .imports        import *

SERVICE_CATALOG = {}

try: SERVICE_CATALOG.update(assigment.Catalog)
except AttributeError: pass

try: SERVICE_CATALOG.update(core.Catalog)
except AttributeError: pass

try: SERVICE_CATALOG.update(geometry_setup.Catalog)
except AttributeError: pass

try: SERVICE_CATALOG.update(utilitary.Catalog)
except AttributeError: pass

__all__ = (
      assigment.__all__ 
    + imports.__all__ 
    + core.__all__ 
    + geometry.__all__ 
    + geometry_setup.__all__ 
    + utilitary.__all__)