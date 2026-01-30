# -*- coding: utf-8 -*-
# _get_shape2.py

from ...imports   import *
from ...utilitary import*
import processor

class ShapeGetterII(LoggerMixin):
    def t_shape(self):
        """
        Retrieves mean dimensions from experimental data file.
        Target: data/input/exp2/exp2_sample.py
        """
        # Localiza a raiz do projeto a partir do arquivo processor
        src_path = os.path.dirname(os.path.abspath(processor.__file__))
        root_path = os.path.dirname(src_path)
        
        data_path = os.path.join(root_path, "data", "input", "exp2", "exp2_sample.py")
        
        print(" [ShapeGetter] Loading geometry from: {}".format(data_path))

        dims = processor.ExpProcessor.process(data_path)

            
        return dims
