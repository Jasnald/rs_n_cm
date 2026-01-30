# -*- coding: utf-8 -*-
# __init__.py

print("Importing package 'imports'...")

# Windows-specific fix for Abaqus Python environment
import os, sys, inspect, shutil, json, warnings, logging, traceback

# Abaqus modules
import mesh, job, step, material, section, assembly, sketch, part

from abaqus import mdb

# módulo partition (opcional)
try:
    import partition
except ImportError:
    partition = None
    warnings.warn("O módulo 'partition' não está disponível no ambiente atual.")

# constantes do Abaqus
from abaqusConstants import (
    C3D8R, STANDARD, OFF, GENERAL,
    ISOTROPIC, MECHANICAL, SOLID, 
    ON, THREE_D, DEFORMABLE_BODY,
    CARTESIAN, XYPLANE, XZPLANE, YZPLANE, PRESELECT, 
    FINER, DOUBLE, MEDIUM, COARSE, SINGLE,
    ITERATIVE, SWEEP,ADVANCING_FRONT, SC8R
)

from regionToolset import Region



# API pública

_MDB    = ['mdb']

_REGION = ['Region']

_BASE   = [
    "os", "sys", "inspect", "shutil", "json", "warnings",
    ]

_MODS   = [
    "mesh", "job", "step", "material", 
    "section", "assembly", "sketch", "part", "partition"
    ]

_CONSTS = [
    "C3D8R", "STANDARD", "OFF", "GENERAL",
    "ISOTROPIC", "MECHANICAL", "SOLID",
    "ON", "THREE_D", "DEFORMABLE_BODY",
    "CARTESIAN", "XYPLANE", "XZPLANE", "YZPLANE",
    "PRESELECT", "FINER", "DOUBLE", "MEDIUM", "COARSE", "SINGLE",
    "ITERATIVE", "SWEEP", "ADVANCING_FRONT", "SC8R"
    ]

__all__ = _MODS + _CONSTS + _MDB + _BASE + _REGION