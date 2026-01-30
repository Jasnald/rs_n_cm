# -*- coding: utf-8 -*-
# _set_mesh.py

from ..utilitary    import *
from ..imports      import *

from ..geometry_setup import PartitionSetter

class MeshSetter(LoggerMixin):
    def __init__(self):
        self.partition = PartitionSetter()

    def mesh(self):
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
        
        # Configurar semente da malha
        self.t_part.seedPart(
            size            = self.mesh_size, 
            deviationFactor = 0.001, 
            minSizeFactor   = 0.001)
        
        # Definir tipo de elemento
        elem_type = mesh.ElemType(
            elemCode    = C3D8R, 
            elemLibrary = STANDARD)
        
        all_cells_region = (self.t_part.cells,)
        
        self.t_part.setElementType(
            regions     = all_cells_region, 
            elemTypes   = (elem_type,))
        
        # Gerar malha
        self.t_part.generateMesh()
        print("Malha gerada com sucesso.")