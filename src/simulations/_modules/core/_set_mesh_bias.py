# -*- coding: utf-8 -*-
# _set_mesh.py

from ..utilitary    import *
from ..imports      import *

from ..geometry_setup import PartitionSetter

class MeshSetterBias(LoggerMixin):
    def __init__(self):
        self.partition = PartitionSetter()

    def mesh(self, edge_set_name=None, 
            maxS     = 1, 
            minS     = 10,
            method   = DOUBLE,
            flip     = False):
        """
        """
        edge_set = self.t_part.sets[edge_set_name]
        # Arestas com bias (refinamento progressivo)
        if method == SINGLE:
            self.t_part.seedEdgeByBias(
                biasMethod = SINGLE,
                end1Edges  = edge_set.edges,
                maxSize    = maxS,
                minSize    = minS
            )
        if flip == True and method == SINGLE:
            self.t_part.seedEdgeByBias(
                biasMethod = SINGLE,
                end2Edges  = edge_set.edges,
                maxSize    = maxS,
                minSize    = minS
            )
        if method == DOUBLE:
            self.t_part.seedEdgeByBias(
                biasMethod = DOUBLE,
                endEdges   = edge_set.edges,
                maxSize    = maxS,
                minSize    = minS
            )
        
        print("Seed gerada com sucesso.")
