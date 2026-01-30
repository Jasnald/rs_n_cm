# -*- coding: utf-8 -*-
# _set_partition_YZ.py

from ...imports         import *
from ...utilitary       import *
from ._set_datum_planes import DatumSetter

class PartitionYZSetter(LoggerMixin):

    def __init__(self, coord=None):
        self.datum = DatumSetter()
        self.coord = coord

    def set(self, coord=None):
        """
        partition_geometry / (method)
        What it does:
        ...
        """
        if coord is not None: self.coord = coord
        if self.coord is None or abs(self.coord) < 1e-6: return
        else: self.datum.create_part(
            coord            = self.coord, 
            datum_name       = 'YZ_{}'.format(self.coord), 
            coordinate_plane = YZPLANE)
