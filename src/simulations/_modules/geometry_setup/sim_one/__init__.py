# -*- coding: utf-8 -*-
# Compatível com Python 2.6/2.7 e 3.x (Abaqus antigos e recentes)

print("Importing package 'sim_one'...")

from ._set_partition    import PartitionSetter

__all__ = [
    "PartitionSetter",
]
