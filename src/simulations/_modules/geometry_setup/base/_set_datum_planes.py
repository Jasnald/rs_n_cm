# -*- coding: utf-8 -*-
# _set_datum_planes.py

from ...utilitary import*
from ...imports   import*

class DatumSetter(LoggerMixin):
    def __init__(self):
        self.datum_plane_ids = {}

    def create_part(self, 
                         coord, 
                         datum_name         = None, 
                         coordinate_plane   = XZPLANE, 
                         create_partition   = True,
                         target_set         = None,
                    ):

        part = self.t_part

        datum_obj = part.DatumPlaneByPrincipalPlane(
            principalPlane  = coordinate_plane, 
            offset          = coord)
        
        self.datum_plane_ids[datum_name] = datum_obj.id
        all_cells = []

        if target_set is None:      all_cells = part.cells
        if target_set is not None:  all_cells = part.sets[target_set].cells
        
        if create_partition:
            part.PartitionCellByDatumPlane(
                cells       = all_cells, 
                datumPlane  = part.datums[datum_obj.id])
            print("Plano de datum criado:", datum_obj.name)

        elif not create_partition:
            print("Plano de datum criado, mas não foi feita a partição da célula.")

    def cut(self,coord=None, variable = None, target_set = None):

        var  = variable
        varc = None

        if var == 'XY': varc = XYPLANE
        if var == 'XZ': varc = XZPLANE
        if var == 'YZ': varc = YZPLANE

        if coord is None:     return
        if abs(coord) < 1e-6: return
        else: self.create_part(
            coord            = coord,
            datum_name       = '{}_{}'.format(var,coord),
            coordinate_plane = varc,
            target_set       = target_set,
        )

    def xy(self,coord=None, target_set = None):
        self.cut(coord,'XY',  target_set = target_set)
    def xz(self,coord=None, target_set = None):
        self.cut(coord,'XZ',  target_set = target_set)
    def yz(self,coord=None, target_set = None):
        self.cut(coord,'YZ',  target_set = target_set)

