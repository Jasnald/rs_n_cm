# -*- coding: utf-8 -*-
# _get_shape2.py

from ...utilitary import *
from Exp_Data.s2_exp.mean_dim_2 import DimTwo

class ShapeGetterTwo(LoggerMixin):

    def shape(self):
        """
        get_t_shape / (method)
        What it does:
        Retrieves the mean dimensions for the T-shaped workpiece from the Mean_dim_workpiece utility.
        """
        dimensions = DimTwo()
        # print("Dimensões obtidas:", dimensions)
        return dimensions