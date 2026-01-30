# -*- coding: utf-8 -*-
# _set_geometry2.py

from ...utilitary   import *
from ...imports     import *
from _get_shape2    import ShapeGetterTwo

class GeometrySetterTwo(LoggerMixin):
    def __init__(self):    
        self._draw  = PolygonDrawer()
        self._shape = ShapeGetterTwo()

    def _geometry(self, depth=10.0):
        """
        create_t_shape_abaqus / (method)
        What it does:
        Creates a T-shaped part in Abaqus using the retrieved dimensions and 
        extrudes it to the specified depth. Returns the model and part objects.
        """
        t_dims = self._shape.shape()
        
        # Criar modelo e sketch
        model_name =    'T_Shape_Model'
        model =         mdb.Model(
                        name = model_name)
        sketch =        model.ConstrainedSketch(
                        name = 'T_Shape_Sketch', 
                        sheetSize = 200.0)
        
        # Calcular posições principais
        width =     t_dims['avg_width']
        height =    t_dims['avg_height']
        
        # Definir pontos do contorno T em sentido anti-horário
        points = [
            (0.0, 0.0),  # base esquerda
            (width, 0.0),  # base direita
            (width, height),  # fim barra horizontal direita
            (0.0, height),  # fim barra horizontal esquerda
        ]
        
        # Desenhar o contorno
        self._draw.draw(sketch, points)
        
        # Criar e extrudar a peça
        part_name = 'T_Shape_Part'
        t_part = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
        t_part.BaseSolidExtrude(sketch=sketch, depth=depth)
        
        print("Forma T 3D criada com sucesso no Abaqus!")
        return model, t_part