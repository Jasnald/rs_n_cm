# -*- coding: utf-8 -*-
# _set_mesh_sc8r.py

from ..utilitary import *
from ..imports import *


class MeshSetterSC8R(LoggerMixin):
    def __init__(self):
        pass

    def set(self, cell_set_name):
        """
        """
        region_cells    = self.t_part.sets[cell_set_name]

        elem_type_sc8r  = mesh.ElemType(
            elemCode    = SC8R,
            elemLibrary = STANDARD)

        self.t_part.setElementType(
            regions     = region_cells,
            elemTypes   = (elem_type_sc8r,)
        )
        print("SC8R aplicado no set '{}'.".format(cell_set_name))