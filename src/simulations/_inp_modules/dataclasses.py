# -*- coding: utf-8 -*-
# _modules/_1_el_region.py

from .imports import *


@dataclass
class Node:
    """Representa um nó do modelo FEA."""
    label: int
    x: float
    y: float
    z: float


@dataclass
class Element:
    """Representa um elemento do modelo FEA."""
    label: int
    nodes: List[int]
    elem_type: str = 'UNKNOWN'


@dataclass
class SectionProperties:
    """Armazena propriedades físicas da seção."""
    name: str
    is_shell: bool
    thickness: float = 0.0
    num_int_pts: int = 1  # Sólidos = 1 (centroide), Shells = N

@dataclass
class AbaqusJobConfig:
    """Configuração para uma única execução."""
    job_name: str
    input_file: str
    output_dir: str
    n_cpus: int = 4
    memory: int = 90
    abaqus_cmd: str = r"C:\SIMULIA\Commands\abq2023.bat"
    interactive: bool = True
    timeout: Optional[float] = 30 * 60 * 60  # 30 horas (None = sem timeout)
    use_scratch: bool = True
    silent_mode: bool = True   # True = guarda logs, False = mostra na tela
    auto_cleanup: bool = True  # Limpa scratch automaticamente se der sucesso

@dataclass
class AbaqusScriptConfig:
    script_name : str
    working_dir : str
    python_cmd  : str = "."
    env         : dict = None

