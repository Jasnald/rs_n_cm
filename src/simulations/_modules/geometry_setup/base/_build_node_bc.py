# -*- coding: utf-8 -*-
# _build_node_bc.py

from ...utilitary import*
from ...imports   import*

class NodeBCBuilder(LoggerMixin):
    def build(self, point_coords, 
                u1=None,    u2=None,    u3=None, 
                ur1=None,   ur2=None,   ur3=None, 
                bc_name="", step_name='Initial'):
        """
        Method: BC_Nodes
        What it does: Applies boundary conditions to a specific node at 
        given coordinates for a specified step.
        """
        try:
            instance_ref = self.model.rootAssembly.instances[self.instance_name]
            
            # Encontrar o vértice no ponto especificado
            vertex = instance_ref.vertices.findAt((point_coords,))
            boundary_region = Region(vertices=vertex)
            
            bc_params = {
                        'createStepName': step_name,
                        'localCsys'     : None,
                        'name'          : bc_name,
                        'region'        : boundary_region
                    }
                    
            # Adicionar apenas os parâmetros que não são None
            if u1  is not None:  bc_params['u1']  = u1
            if u2  is not None:  bc_params['u2']  = u2
            if u3  is not None:  bc_params['u3']  = u3
            if ur1 is not None:  bc_params['ur1'] = ur1
            if ur2 is not None:  bc_params['ur2'] = ur2
            if ur3 is not None:  bc_params['ur3'] = ur3
        
            # Aplicar a condição de contorno
            self.model.DisplacementBC(**bc_params)
                
            print("Aplicada condição de contorno '{}' no ponto {}".format(bc_name, point_coords))
            
        except Exception as e:
            print("Erro ao aplicar condição de contorno '{}': {}".format(bc_name, e))
