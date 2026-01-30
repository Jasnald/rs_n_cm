# -*- coding: utf-8 -*-
# _set_geometry.py

from ...utilitary   import *
from ...imports     import *
from _get_shape     import ShapeGetterI

class GeometrySetter(LoggerMixin):
    def __init__(self):        
        self._draw  = PolygonDrawer()
        self._shape = ShapeGetterI()

    def _geometry(self, depth=10.0):
        """
        create_t_shape_abaqus / (method)
        What it does:
        Creates a T-shaped part in Abaqus using the retrieved dimensions and extrudes it to the specified depth. Returns the model and part objects.
        """
        t_dims = self._shape.t_shape()
        
        # Criar modelo e sketch
        model_name  = 'T_Shape_Model'
        model       = mdb.Model(
                    name=model_name)
        sketch      = model.ConstrainedSketch(
                    name='T_Shape_Sketch', 
                    sheetSize=200.0)
        
        # Calcular posições principais
        h_width     = t_dims['h_width']
        h_thickness = t_dims['h_thickness']
        v_width     = t_dims['v_width']
        v_height    = t_dims['v_height']
        v_pos_x     = t_dims['offset_1']
        
        # Definir pontos do contorno T em sentido anti-horário
        points = [
            (0.0, 0.0),  # base esquerda
            (h_width, 0.0),  # base direita
            (h_width, h_thickness),  # fim barra horizontal direita
            (v_pos_x + v_width, h_thickness),  # base direita barra vertical
            (v_pos_x + v_width, h_thickness + v_height),  # topo direita barra vertical
            (v_pos_x, h_thickness + v_height),  # topo esquerda barra vertical
            (v_pos_x, h_thickness),  # base esquerda barra vertical
            (0.0, h_thickness),  # fim barra horizontal esquerda
        ]
        
        # Desenhar o contorno
        self._draw.draw(sketch, points)
        
        # Criar e extrudar a peça
        part_name = 'T_Shape_Part'
        t_part = model.Part(
            name            = part_name, 
            dimensionality  = THREE_D, 
            type            = DEFORMABLE_BODY)
        t_part.BaseSolidExtrude(
            sketch  = sketch, 
            depth   = depth)
        
        print("Forma T 3D criada com sucesso no Abaqus!")
        return model, t_part