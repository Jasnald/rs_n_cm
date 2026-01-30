# -*- coding: utf-8 -*-
# _build_node_bc.py

from ...utilitary import*
from ...imports   import*
from ..base       import *

class RemoveDatumSetter(LoggerMixin):
    
    def __init__(self):
        self.parXZ = PartitionXZSetter()
        self.parYZ = PartitionYZSetter()

    def set(self):
        """
        Method: create_datum_planes
        What it does: Creates additional datum planes (ZX/ZY) using coordinates 
        from the loaded JSON settings.
        """
        try:
            self.parXZ.coord = self.ZX
            self.parXZ.set()
            self.parYZ.coord = self.ZY
            self.parYZ.set()
        except Exception as e:
            print("Error creating datum planes:", e)
            traceback.print_exc()
