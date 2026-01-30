# -*- coding: utf-8 -*-
# _set_mesh.py

from ..utilitary    import *
from ..imports      import *

from ..geometry_setup import PartitionSetter

class MeshSetterSeed(LoggerMixin):
    def __init__(self):
        self.partition = PartitionSetter()

    def mesh(self, edge_set_name=None, num_elements=1):
        """
        Aplica seed em arestas usando um set existente.
        """
        edge_set = self.t_part.sets[edge_set_name]
        
        self.t_part.seedEdgeByNumber(
            constraint = FINER, 
            edges      = edge_set.edges, 
            number     = num_elements
        )
        
        print("Seed gerada com sucesso no set '{}'.".format(edge_set_name))