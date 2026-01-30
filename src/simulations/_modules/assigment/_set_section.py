# -*- coding: utf-8 -*-
# _set_section.py

from ..utilitary import *

from _set_section_assign import SectionAssigner

class SectionSetter(LoggerMixin):
    def __init__(self):
        self._section = SectionAssigner()

    def create(self, mat_name, cell_set_name, section_name,
               homogeneous = True, thick = None, int_points = None):
        """
        c_section / (method)
        What it does:
        Creates a homogeneous solid section in Abaqus and assigns it to the 
        T-shaped part, either to all cells or a specified region.
        """
        # Cria a seção homogênea
        #
        if homogeneous:
            self.model.HomogeneousSolidSection(
                name        = section_name,
                material    = mat_name,
                thickness   = None
            )
        if not homogeneous:
            self.model.HomogeneousShellSection(
                name            = section_name,
                material        = mat_name,
                numIntPts       = int_points,
                thickness       = thick,
            )
        if cell_set_name is None:
            # Atribui a seção a todas as células da peça
            region_all = self.t_part.Set(
                cells  = self.t_part.cells, 
                name   = 'AllCells')
            
            self._section.assign(region_all, section_name)
        else:
            region_cells = self.t_part.sets[cell_set_name].cells

            region = self.t_part.Set(
                cells   = region_cells,
                name    = section_name)
            self._section.assign(region,section_name)
