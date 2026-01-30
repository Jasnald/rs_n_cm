# -*- coding: utf-8 -*-
# _get_shape.py

from ...imports   import *
from ...utilitary import*
import processor


class ShapeGetterI(LoggerMixin):
    def t_shape(self):
        """
        Retrieves mean dimensions from experimental data file.
        Target: data/input/exp1/exp1_sample01.py
        """
        # Localiza a raiz do projeto a partir do arquivo processor
        src_path = os.path.dirname(os.path.abspath(processor.__file__))
        root_path = os.path.dirname(src_path)
        
        data_path = os.path.join(root_path, "data", "input", "exp1", "exp1_sample01.py")
        
        print(" [ShapeGetter] Loading geometry from: {}".format(data_path))

        dims = processor.ExpProcessor.process(data_path)

        h_width = dims.get('h_width')
        v_width = dims.get('v_width')
        off_1   = dims.get('offset_1')
        
        dims['offset_2'] = h_width - v_width - off_1
            
        return dims
