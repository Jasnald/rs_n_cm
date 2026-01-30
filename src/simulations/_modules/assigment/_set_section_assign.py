# -*- coding: utf-8 -*-
# _set_section.py

from ..utilitary import*

class SectionAssigner(LoggerMixin):

    def assign(self,region, section_name):
        """
        c_section_ass / (method)
        What it does:
        Assigns the specified section to the given region of the T-shaped part 
        in Abaqus.
        """
        self.t_part.SectionAssignment(
            region      = region, 
            sectionName = section_name) 