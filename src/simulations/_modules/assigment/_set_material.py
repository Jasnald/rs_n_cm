# -*- coding: utf-8 -*-
# _set_material.py

from ..utilitary import*

class MaterialSetter(LoggerMixin):

    def material(self, mat_name, E_Modulus, P_ratio):
        """
        c_material / (method)
        What it does:
        Defines an elastic material and assigns it to the Abaqus model for the T-shaped part.
        """
        self.logger.info("Criando material e seção para: {}".format(mat_name))
        
        # Cria o material
        self.model.Material(
            name = mat_name)
        self.model.materials[mat_name].Elastic(
            table=((E_Modulus, P_ratio),))