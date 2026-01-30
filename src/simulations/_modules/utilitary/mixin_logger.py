# -*- coding: utf-8 -*-
# logger_mixin.py

from utils import *
from mixin_context import ContextMixin

class LoggerMixin(ContextMixin):
    def __init__(self, *args, **kwargs):
        self.logger = setup_logger(self.__class__.__name__)
        self.logger.info("Class has been initialized: '{}'.".format(self.__class__.__name__))
        super(LoggerMixin, self).__init__(*args, **kwargs)