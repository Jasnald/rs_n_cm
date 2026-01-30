# -*- coding: utf-8 -*-
# _set_mesh.py

from ..utilitary    import *
from ..imports      import *

from ..geometry_setup import PartitionSetter

class MeshDeleter(LoggerMixin):
    def __init__(self):
        self.partition = PartitionSetter()

    def dele(self):
        """
        mesh_part / (method)
        What it does:
        Generates a simple 3D mesh (using C3D8R elements) for the T-shaped part, after partitioning geometry and setting mesh controls.
        """
        # Primeiro, deletar qualquer malha existente
        try:
            self.t_part.deleteMesh(
                regions = self.t_part.cells.getSequenceFromMask(('[#1 ]',)))
            print("Malha existente removida.")
        except: print("Nenhuma malha existente para remover.")
        