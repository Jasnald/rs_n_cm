# -*- coding: utf-8 -*-
# _set_mesh.py

from ..utilitary import *
from ..imports import *


class MeshSetterSweep(LoggerMixin):
    def __init__(self):
        pass

    def set(self, cell_set_name):
        """
        Aplica SWEEP nas células de um Set específico.
        """
        # Pega as células do Set criado pelo CellSetCreator
        region_cells = self.t_part.sets[cell_set_name].cells

        self.t_part.setMeshControls(
            regions     = region_cells,
            technique   = SWEEP,
            algorithm   = ADVANCING_FRONT,
            allowMapped = False
        )
        print("Sweep aplicado no set '{}'.".format(cell_set_name))