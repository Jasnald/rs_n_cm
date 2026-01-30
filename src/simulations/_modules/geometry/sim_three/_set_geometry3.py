# -*- coding: utf-8 -*-
# _set_geometry.py

from ...utilitary   import *
from ...imports     import *


class GeometrySetterThree(LoggerMixin):
    def __init__(self):        
        self._draw  = PolygonDrawer()

    def _geometry(self, width=4.0, height=4.0 , depth=4.0):
        """
        create_rectangular_part / (method)
        What it does:
        Creates a rectangular part in Abaqus with the specified dimensions and 
        extrudes it to the specified depth. Returns the model and part objects.
        :rtype: tuple[Any, Any]

        """
        # Create model and sketch
        model_name  = 'Rectangular_Model'
        model       = mdb.Model(
                    name = model_name)
        sketch      = model.ConstrainedSketch(
                    name = 'Rectangle_Sketch', 
                    sheetSize = 200.0)
        
        # Define rectangle points in counter-clockwise order
        points = [
            (0.0, 0.0),      # bottom left
            (width, 0.0),    # bottom right
            (width, height), # top right
            (0.0, height),   # top left
        ]
        
        # Draw the contour
        self._draw.draw(sketch, points)
        
        # Criar e extrudar a peça
        part_name = 'Rectangular_Model'
        t_part = model.Part(
            name            = part_name, 
            dimensionality  = THREE_D, 
            type            = DEFORMABLE_BODY)
        t_part.BaseSolidExtrude(
            sketch          = sketch, 
            depth           = depth)
            #depth           = 1)
        
        
        print("Rectangular 3D part created successfully in Abaqus!")
        return model, t_part