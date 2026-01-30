# -*- coding: utf-8 -*-
# Compatível com Python 2.6/2.7 e 3.x (Abaqus antigos e recentes)
from gettext import Catalog

print("Importing package 'core'...")

from ._set_job        import JobSetter
from ._set_mesh       import MeshSetter
from ._set_step       import StepSetter
from ._set_mesh_seed  import MeshSetterSeed
from ._set_mesh_bias  import MeshSetterBias
from ._set_mesh_del   import MeshDeleter
from ._set_mesh_sweep import MeshSetterSweep
from ._set_mesh_sc8r  import MeshSetterSC8R
from ._set_mesh_stack import MeshSetterStack

Catalog = {
    '_job':     JobSetter,
    '_mesh':    MeshSetter,
    '_step':    StepSetter,
    '_m_seed':  MeshSetterSeed,
    '_m_bias':  MeshSetterBias,
    '_m_del':   MeshDeleter,
    '_m_sweep': MeshSetterSweep,
    '_m_SC8R':  MeshSetterSC8R,
    '_m_stack': MeshSetterStack,
}

__all__ = [
    "JobSetter",
    "MeshSetter",  
    "StepSetter",
    "MeshSetterSeed",
    "MeshSetterBias",
    "MeshDeleter",
    "MeshSetterSweep",
    "MeshSetterSC8R",
    "MeshSetterStack",
    "Catalog",
]
