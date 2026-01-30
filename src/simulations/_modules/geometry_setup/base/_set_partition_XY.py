# -*- coding: utf-8 -*-
# _set_partition_XY.py

from ...imports         import *
from ...utilitary       import *
from ._set_datum_planes import DatumSetter

class PartitionXYSetter(LoggerMixin):
    def __init__(self):
        self.datum = DatumSetter()
    def set(self,coord=None):
        """
        partition_geometry / (method)
        What it does:
        ...
        """
        if coord is None:     return
        if abs(coord) < 1e-6: return
        else: self.datum.create_part(
            coord            = coord, 
            datum_name       = 'XY_{}'.format(coord), 
            coordinate_plane = XYPLANE)


