import sys, os, inspect

_here      = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
M_PP_S1_EXP_DIR = os.path.join(_here)

__all__ = [
    'M_PP_S1_EXP_DIR',]