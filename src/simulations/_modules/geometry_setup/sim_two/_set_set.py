# -*- coding: utf-8 -*-
# _set_set.py

from ...utilitary import*
from ...imports   import*
from ..base       import*
from _set_region  import*

class SetSetter(LoggerMixin):

    def __init__(self):
        self.cct = CellCenterTester()
        self.crr = RemovalRegionSetter()

    def set(self):
        """
        Method: create_sets
        What it does: Creates the 'Remove' set from the removal region and the 'AllCells' set for the part.
        """
        print("Creating sets...")
        part_ref = self.t_part

        part_ref.Set(
            cells = part_ref.cells,
            name  = "AllCells")

        region = self.cct.test(self.crr.set())

        part_ref.Set(
            cells = region,
            name  = "Remove")

        print("Sets 'Remove' and 'AllCells' have been created.")