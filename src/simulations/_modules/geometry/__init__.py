# -*- coding: utf-8 -*-
# Compatível com Python 2.6/2.7 e 3.x (Abaqus antigos e recentes)

print("Importing package 'geometry'...")

from .sim_one   import *
from .sim_two   import *
from .sim_three import *
from .sim_iv    import *
from . import sim_one, sim_two , sim_three, sim_iv

__all__ = sim_one.__all__ + sim_two.__all__ + sim_three.__all__ + sim_iv.__all__
