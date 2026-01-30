# -*- coding: utf-8 -*-
# _set_geometry.py

from ...utilitary   import *
from ...imports     import *


class GeometrySetterIV(LoggerMixin):
    def __init__(self):        
        self._draw  = PolygonDrawer()

    def _geometry(self, width=4.0, height=4.0 , depth=4.0):
        """
        Creates the Inverted T-Shape part based on the provided
        coordinates.
        """
        # Create model and sketch
        model_name  = 'Rectangular_Model'
        model       = mdb.Model(
                    name = model_name)
        sketch      = model.ConstrainedSketch(
                    name = 'Rectangle_Sketch',
                    sheetSize = 200.0)

        ofs = (25 - width)/2
        points = [
            (0.0, 0.0),
            (25, 0.0),
            (25, 10),
            (25 - ofs, 10),
            (25 - ofs, 10 + height),
            (ofs, 10 + height),
            (ofs, 10),
            (0.0, 10)
        ]

        self._draw.draw(sketch, points)

        # Create and extrude the part
        part_name   = 'Rectangular_Model'
        t_part      = model.Part(
            name            = part_name,
            dimensionality  = THREE_D,
            type            = DEFORMABLE_BODY)

        t_part.BaseSolidExtrude(
            sketch          = sketch,
            depth           = depth)

        print("Inverted T-Shape part created successfully in Abaqus!")
        return model, t_part