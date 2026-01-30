# -*- coding: utf-8 -*-
# _set_region.py

from ...utilitary        import*
from ...imports          import*
from ...geometry.sim_two import* 

class RemovalRegionSetter(LoggerMixin):
    def __init__(self):
        self.sgt = ShapeGetterTwo()
        self.remove_region = (0.0, 0.0)
        self.ZX            = 0.0
        self.ZY            = 0.0

    def set(self):
        """
        Define a região a ser removida para o novo blank retangular.
        Continua devolvendo (elems_between_x, bounds).
        """
        part_ref = self.t_part

        # Dimensões médias do retângulo
        r_dims = self.sgt.shape()
        print("r_dims:", r_dims)
        
        # Validar se r_dims contém valores válidos
        if not r_dims or any(v is None for v in [
            r_dims.get('avg_lenth'), 
            r_dims.get('avg_width'), 
            r_dims.get('avg_height')
        ]):
            raise ValueError("ShapeGetterTwo returned invalid dimensions: {}".format(r_dims))
        
        # Z (comprimento da peça)
        Min_Z = 0.0
        Max_Z = float(r_dims['avg_lenth'])

        # X e Y (seção transversal retangular completa)
        Min_X = 0.0
        Max_X = float(r_dims['avg_width'])
        Min_Y = 0.0
        Max_Y = float(r_dims['avg_height'])

        # Validar ZX e ZY
        if self.ZX is None:
            print("ZX is None, defaulting to 0.0")
            self.ZX = 0.0
        if self.ZY is None:
            print("ZY is None, defaulting to 0.0")
            self.ZY = 0.0

        # Ponto selecionado pelo usuário
        ponto_x, _ = self.remove_region
        print("remove_region:", self.remove_region)
        print("ZX:", self.ZX)
        print("ZY:", self.ZY)

        # Converter para float explicitamente
        ZX = float(self.ZX)
        ZY = float(self.ZY)

        # Corte pelo plano ZY
        if ponto_x < ZY:
            Max_X = ZY
        elif ponto_x > ZY:
            Min_X = ZY
        else:
            print("Plane not selected correctly, using default bounds")

        # Corte pelo plano ZX
        Min_Y = ZX

        # Log final dos bounds antes de chamar getByBoundingBox
        print("Bounding box: ({}, {}, {}, {}, {}, {})".format(
            Min_X, Min_Y, Min_Z, Max_X, Max_Y, Max_Z
        ))

        elems_between_x = part_ref.cells.getByBoundingBox(
            float(Min_X), float(Min_Y), float(Min_Z),
            float(Max_X), float(Max_Y), float(Max_Z)
        )
        
        bounds = (Min_X, Min_Y, Min_Z, Max_X, Max_Y, Max_Z)
        return elems_between_x, bounds