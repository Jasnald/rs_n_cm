# -*- coding: utf-8 -*-
# model_mixin.py

class ModelMixinThree:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from _set_geometry3 import GeometrySetterThree
        self._geometry = GeometrySetterThree()
        self.model, self.t_part = self._geometry._geometry(
            depth=self.comprimento)