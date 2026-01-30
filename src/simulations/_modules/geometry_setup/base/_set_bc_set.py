# -*- coding: utf-8 -*-


from ...utilitary import *
from ...imports   import *


class BCSet(LoggerMixin):

    def __init__(self, model=None, instance_name=None):

        super(BCSet, self).__init__()
        self.model         = model
        self.instance_name = instance_name


    def set(self, set_name, bc_name="", step_name='Initial'):

        bc_name = bc_name or 'Enc-{}'.format(set_name)

        try:
            asm     = self.model.rootAssembly
            region  = None

            if set_name in asm.sets:
                region = asm.sets[set_name]


            elif self.instance_name:
                inst = asm.instances[self.instance_name]
                if set_name in inst.sets:
                    region = inst.sets[set_name]


            if region is None:
                raise RuntimeError("Set '{0}' não encontrado na assembly "
                                   "nem na instância '{1}'.".format(
                                       set_name, self.instance_name))


            self.model.EncastreBC(name=bc_name,
                                  createStepName=step_name,
                                  region=region,
                                  localCsys=None)

            self.logger.info("BC '%s' aplicada com sucesso ao set '%s'.",
                             bc_name, set_name)

        except Exception as err:
            self.logger.error("Falha ao aplicar BC '%s': %s", bc_name, err)
            raise