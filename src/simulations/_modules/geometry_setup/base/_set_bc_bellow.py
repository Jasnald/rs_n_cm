# -*- coding: utf-8 -*-
# _set_bc_bellow.py

from ...utilitary import*
from ...imports   import*
from ._set_partition_XZ import PartitionXZSetter

class BCBelowSetter(LoggerMixin):

    LBB = 1e6

    def __init__(self):#,
    #     y_cutoff        = None,
    #     remove          = None,
    #     remove_step     = None,
    #     bc_type         = None):

    #     if y_cutoff    is not None: self.y_cutoff    = y_cutoff
    #     if remove      is not None: self.remove      = remove
    #     if remove_step is not None: self.remove_step = remove_step
    #     if bc_type     is not None: self.bc_type     = bc_type
        self.ptt = PartitionXZSetter()
        self.y_cutoff    = 0.0          # define em quem chamar
        self.remove      = False        # se BC será desativado
        self.remove_step = 'Step-2'     # passo em que desativa
        self.bc_type     = 'EncastreBC'

    def set(self): 
            
        """
        Method: set_boundary_conditions_below_y
        What it does: Applies a boundary condition to all faces below a y-axis 
        cutoff and optionally deactivates it in a later step.
        """
        instance_ref = self.model.rootAssembly.instances[self.instance_name]

        self.ptt.set(coord = self.y_cutoff)

        faces_below_cutoff = instance_ref.faces.getByBoundingBox(
            xMin = -self.LBB, yMin = -self.LBB,      zMin = -self.LBB, 
            xMax =  self.LBB, yMax =  self.y_cutoff, zMax =  self.LBB
        )
        
        print("Found {} faces below y={}".format(len(faces_below_cutoff), self.y_cutoff))
        if len(faces_below_cutoff) == 0:
            print("No faces found below y_cutoff = {}. Adjust parameters if needed.".format(self.y_cutoff))
            return
        
        boundary_region = Region(faces=faces_below_cutoff)

        # If type is unknown, default to 'EncastreBC'
        if self.bc_type not in ['EncastreBC', 'PinnedBC']:
            print("Unknown boundary condition type '{}'. Defaulting to 'EncastreBC'.".format(self.bc_type))
            self.bc_type = 'EncastreBC'

        bc_name = 'BC-Faces-Below-Y{}'.format(self.y_cutoff)
        getattr(self.model, self.bc_type)(
            createStepName  = 'Initial',
            localCsys       = None,
            name            = bc_name,
            region          = boundary_region
        )
        print("Applied '{}' to {} faces with y <= {}.".format(self.bc_type, len(faces_below_cutoff), self.y_cutoff))


        if self.remove:
            try:
                self.model.boundaryConditions[bc_name].deactivate(self.remove_step)
                print("Boundary condition '{}' deactivated in step '{}'.".format(bc_name, self.remove_step))
            except Exception as e:
                print("Error deactivating boundary condition '{}': {}".format(bc_name, e))
        else:
            print("Boundary condition '{}' remains active.".format(bc_name))
