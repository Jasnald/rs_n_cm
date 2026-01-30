# -*- coding: utf-8 -*-
# _set_instance.py

from ..utilitary import*
from ..imports import *

class InstanceSetter(LoggerMixin):

    def create(self):
        """
        create_instance / (method)
        What it does:
        Creates an instance of the T-shaped part in the Abaqus assembly 
        if it does not already exist. Returns the instance object.
        """
        if self.instance_name not in self.model.rootAssembly.instances:
            self.model.rootAssembly.Instance(
                name        = self.instance_name, 
                part        = self.t_part, 
                dependent   = ON)
        return self.model.rootAssembly.instances[self.instance_name]