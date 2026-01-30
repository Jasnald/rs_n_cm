# -*- coding: utf-8 -*-
# _get_shape.py

from ...utilitary import*
from Exp_Data.s1_exp.mean_dim import DimOne

class ShapeGetter(LoggerMixin):
    def t_shape(self):
        """
        get_t_shape / (method)
        What it does:
        Retrieves the mean dimensions for the T-shaped workpiece from the Mean_dim_workpiece utility.
        """
        dimensions = DimOne()
        # print("Dimensões obtidas:", dimensions)
        return dimensions