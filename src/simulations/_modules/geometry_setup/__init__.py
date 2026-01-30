# -*- coding: utf-8 -*-
# Compatível com Python 2.6/2.7 e 3.x (Abaqus antigos e recentes)

print("Importing package 'geometry_setup'...")

from .                  import *
from .base              import *
from .sim_one           import *
from .sim_two           import *

__all__ = (
    base.__all__ +
    sim_one.__all__+
    sim_two.__all__
    )
