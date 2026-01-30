# -*- coding: utf-8 -*-
# _set_model_change.py

from ...utilitary import*
from ...imports import *


class ModelChangeSetter(LoggerMixin):
    def set(self):
        self.model.ModelChange(
            activeInStep    = False,
            createStepName  = self.modelStepName,
            includeStrain   = True,
            name            = self.modelChangeName,
            region          = self.model.rootAssembly.instances[
                self.instance_name].sets[
                self.setChangeName])    