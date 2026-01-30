# src/Simulations/_pipelines/dataclass.py

from .imports import *

@dataclass
class SimulationConfig:
    """
    Centraliza todos os parâmetros da simulação.
    Chega de ficar buscando data['chave']['subchave'] no meio do código!
    """
    # Paths
    work_directory: Path
    cm_directory: Path
    rea_directory: Path
    geometry_script: Path

    # Material
    elastic_modulus: float
    poisson_ratio: float

    # Mesh Generation Params
    mesh_min: float
    mesh_max: float
    mesh_step: float
    length_min: int
    length_max: int
    length_step: int

    # Abaqus Solver Params
    initial_inc: float
    max_inc: float
    max_num_inc: int
    min_inc: float
    nlgeom: bool
    time_period: float

    polynomial_json_dir: Optional[Path] = None
    polynomial_json_default: Optional[Path] = None

    # Internal Params
    instance_name: str = "T_SHAPE_PART-1"
    step_name: str = "Step-1"
    nset_disp_name: str = "Set_Disp"
    abaqus_cmd: str = r"C:\SIMULIA\Commands\abq2021.bat"  # Default fallback

