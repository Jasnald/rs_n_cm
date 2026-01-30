# -*- coding: utf-8 -*-
# _set_partition.py

from ...utilitary import*
from ...imports   import*

from ...geometry.sim_one     import ShapeGetter
from ..base                  import DatumSetter

class PartitionSetter(LoggerMixin):
    def __init__(self):
        self._shape = ShapeGetter()
        self._datum = DatumSetter()

    def partition(self):
        """
        partition_geometry / (method)
        What it does:
        Partitions the geometry of the T-shaped part to improve mesh control by creating datum planes at key locations.
        """
        t_dims = self._shape.t_shape()

        coord = t_dims['h_thickness']
        self._datum.create_part(
            coord            = coord, 
            datum_name       = 'ZX1', 
            coordinate_plane = XZPLANE)

        coord2 = t_dims['h_thickness']/2
        self._datum.create_part(
            coord            = coord2, 
            datum_name       = 'ZX2', 
            coordinate_plane = XZPLANE)

