# -*- coding: utf-8 -*-
# _test_cell_center.py

from ...utilitary import*
from ...imports   import*

class CellCenterTester(LoggerMixin):
    
    def test(self, R_Modulus):
        """
        Method: Center_Cell_Test
        What it does: Filters cells whose center is within the
        removal region bounds and returns them as a CellArray.
        """
        elems_between_x, bounds = R_Modulus

        Min_X, Min_Y, Min_Z, Max_X, Max_Y, Max_Z = bounds

        filtered_cells = []
        for cell in elems_between_x:
            center = cell.pointOn[0]
            if (Min_X <= center[0] <= Max_X and 
                Min_Y <= center[1] <= Max_Y and 
                Min_Z <= center[2] <= Max_Z):
                filtered_cells.append(cell)
    
        from part import CellArray
        return CellArray(filtered_cells)