# -*- coding: utf-8 -*-
# Compatível com Python 2.6/2.7 e 3.x (Abaqus antigos e recentes)

import os
import sys

print("Importando pacote '_get_classes'...")

__all__ = []

# (Opcional) caminhos úteis
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
ROOT_DIR   = os.path.dirname(PARENT_DIR)
__all__ += ['BASE_DIR', 'PARENT_DIR', 'ROOT_DIR']

# Helper de import compatível (importlib quando houver; senão __import__)
try:   from importlib import import_module as _import_module
except Exception:
    def _import_module(name):
        return __import__(name, fromlist=['*'])

def _import_and_expose(mod_specs, pkg_name=None):
    """
    Importa silenciosamente símbolos de submódulos e os expõe no pacote.

    mod_specs: lista de tuplas (nome_do_modulo, (nomes,))
    pkg_name:  nome do pacote; se None, usa __name__.
    Retorna tupla com os nomes exportados.
    """
    if pkg_name is None: pkg_name = __name__
    exported = []
    for module_name, names in mod_specs:
        full = "%s.%s" % (pkg_name, module_name)
        
        try: m = _import_module(full)
        except Exception: continue
        
        for n in names:
            try: globals()[n] = getattr(m, n)
            except Exception: continue
            else: exported.append(n)
    
    seen = set(__all__) # evitar duplicados em __all__
    for n in exported:
        if n not in seen:
            __all__.append(n)
            seen.add(n)
    return tuple(exported)

# Catálogo de importação
_import_and_expose([
    ("_set_geometry",     ("GeometrySetter",)),
    ("_set_geometry2",    ("GeometrySetterTwo",)),
    ("_get_shape",        ("ShapeGetter",)),
    ("_get_shape2",       ("ShapeGetterTwo",)),
    ("_set_step",         ("StepSetter",)),
    ("_set_material",     ("MaterialSetter",)),
    ("_set_section",      ("SectionSetter",)),
    ("_set_instance",     ("InstanceSetter",)),
    ("_set_mesh",         ("MeshSetter",)),
    ("_set_job",          ("JobSetter",)),
    ("_set_partition",    ("PartitionSetter",)),
    ("_set_datum_planes", ("DatumSetter",)),
    ("_get_parameters",   ("_get_parameters",)),
])


# # Importação das classes do pacote 'assigment'
# from .assigment import (
#     InstanceSetter,
#     MaterialSetter,
#     SectionSetter,
#     SectionAssigner
# )

# # Importação das classes do pacote 'core'
# from .core import (
#     JobSetter,
#     MeshSetter,
#     StepSetter
# )

# # Importação das classes do pacote 'geometry' - sim_one
# from .geometry.sim_one import (
#     ShapeGetter,
#     GeometrySetter,
#     ModelMixin
# )

# # Importação das classes do pacote 'geometry' - sim_two
# from .geometry.sim_two import (
#     ShapeGetterTwo,
#     GeometrySetterTwo,
#     ModelMixinTwo
# )


# # Importação das classes do pacote 'geometry_setup'
# from .geometry_setup import (
#     DatumSetter,
#     PartitionSetter
# )

# # Importação das classes do pacote 'utils'
# from .utilitary import (
#     LoggerMixin,
#     PolygonDrawer,
#     ParametersGetter
# )

# from .imports import *

# __all__ = [
#     # Assigment classes
#     "InstanceSetter",
#     "MaterialSetter", 
#     "SectionSetter",
#     "SectionAssigner",
    
#     # Core classes
#     "JobSetter",
#     "MeshSetter",
#     "StepSetter",
    
#     # Geometry sim_one classes
#     "ShapeGetter",
#     "GeometrySetter", 
#     "ModelMixin",
    
#     # Geometry sim_two classes
#     "ShapeGetterTwo",
#     "GeometrySetterTwo",
#     "ModelMixinTwo",
    
#     # Geometry setup classes
#     "DatumSetter",
#     "PartitionSetter",
    
#     # Utility classes
#     "LoggerMixin",
#     "PolygonDrawer",
#     "ParametersGetter",

# ] + imports.__all__
