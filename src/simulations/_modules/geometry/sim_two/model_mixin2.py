# -*- coding: utf-8 -*-
# model_mixin.py

class ModelMixinTwo:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from _set_geometry2 import GeometrySetterTwo
        self._geometry = GeometrySetterTwo()
        self.model, self.t_part = self._geometry._geometry(
            depth=self.comprimento)