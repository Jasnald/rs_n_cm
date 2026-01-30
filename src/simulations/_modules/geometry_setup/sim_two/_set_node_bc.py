# -*- coding: utf-8 -*-
# _build_node_bc.py

from ...utilitary        import*
from ...imports          import*
from ...geometry.sim_two import* 
from ..base              import NodeBCBuilder

class NodeBCSetter(LoggerMixin):

    def __init__(self):
        self.sgt        = ShapeGetterTwo()
        self.nbc        = NodeBCBuilder()
        self.step_name  ='Initial'

    def set(self):
        """
        Method: BC_Nodes_All
        What it does: Applies boundary conditions to four key points of 
        the T-shape part for a given step.
        """
        # Obtain the T-shape dimensions
        t_dims = self.sgt.shape()
        largura = t_dims.get('avg_width', 500.0)      # Default width if not specified
        
        self.nbc.build(
            point_coords    = (0.0, 0.0, 0.0),
            u1 = 0, u2 = 0, u3 = 0, ur1 = None, ur2 = None, ur3 = None,
            bc_name         = "BC-Point1-Pinned",
            step_name       = self.step_name)
        
        self.nbc.build(
            point_coords    = (largura, 0.0, 0.0),
            u1 = None, u2 = 0, u3 = 0, ur1 = None, ur2 = None, ur3 = None,  
            bc_name         = "BC-Point2-YZ-Fixed",
            step_name       = self.step_name)
        
        self.nbc.build(
            point_coords    =(0.0, 0.0, self.comprimento),
            u1 = None, u2 = 0, u3 = None, ur1 = None, ur2 = None, ur3 = None,
            bc_name         = "BC-Point3-Y-Fixed",
            step_name       = self.step_name)
        
        self.nbc.build(
            point_coords    = (largura, 0.0, self.comprimento),
            u1 = None, u2 = 0, u3 = None, ur1 = None, ur2 = None, ur3 = None,  
            bc_name         = "BC-Point4-Y-Fixed",
            step_name       = self.step_name)
        
        print("Boundary conditions applied to all specified points in step '{}'.".format(self.step_name))
