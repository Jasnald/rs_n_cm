# -*- coding: utf-8 -*-
# _set_static_step.py

from ..utilitary import*
from ..imports import *

class StepSetter(LoggerMixin):
        
    def create(self):
        """
        create_static_step / (method)
        What it does:
        Creates a static analysis step in the Abaqus model, 
        replacing any existing step with the same name.
        """
        if self.step_name in self.model.steps:
            del self.model.steps[self.step_name]

        self.model.StaticStep(
            timePeriod  = self.time,
            initialInc  = self.initialInc,
            maxInc      = self.maxInc,
            maxNumInc   = self.maxNumInc,
            minInc      = self.minInc,
            name        = self.step_name,
            previous    = self.previous,
            nlgeom      = self.nlgeom,
            matrixSolver= ITERATIVE)

        if 'F-Output-1' in self.model.fieldOutputRequests:
            del self.model.fieldOutputRequests['F-Output-1']

        if 'H-Output-1' in self.model.historyOutputRequests:
            del self.model.historyOutputRequests['H-Output-1']

        self.model.FieldOutputRequest(
            createStepName  = self.step_name,
            name            = 'FO-' + self.step_name,
            variables       = ('S', 'U'))
        """
        self.model.HistoryOutputRequest(
            createStepName  = self.step_name,
            name            = 'HO' + self.step_name,
            variables       = PRESELECT)  
        """
