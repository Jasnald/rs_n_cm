# -*- coding: utf-8 -*-
# model_mixin.py

class ModelMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from _set_geometry import GeometrySetter
        self._geometry = GeometrySetter()
        self.model, self.t_part = self._geometry._geometry(
            depth=self.comprimento)