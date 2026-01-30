

from .imports import *
from .dataclass import *

class ConfigurationManager:

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._data = None
        self.config: Optional[SimulationConfig] = None

    def load(self) -> SimulationConfig:
        with open(self.config_path, 'r') as f:
            self._data = json.load(f)

        # Helpers para encurtar a extração
        d = self._data.get("directories", {})
        m = self._data.get("material_properties", {})
        ms = self._data.get("mesh_settings", {})
        abq = self._data.get("abaqus_parameters", {})

        # Define caminhos padrão caso não existam no JSON
        # (Ajuste conforme sua estrutura real de pastas)
        root = Path(__file__).resolve().parents[3]

        self.config = SimulationConfig(
            # Directories
            work_directory   = Path(d.get("work_directory", ".")),
            cm_directory     = Path(d.get("CM_directory", "./CM_Simulations")),
            rea_directory    = Path(d.get("REA_directory", "./REA_Simulations")),

            # Scripts (Tenta pegar do JSON ou assume padrão)
            geometry_script  = Path(d.get("geometry_script",
                root / "src/simulations/cma/script.py")),
            polynomial_json_dir=Path(d.get("polynomial_json_dir",
                root / "data/output/exp2/curve_data")),
            polynomial_json_default=Path(d.get("polynomial_json",
                root / "data/output/exp1/surface_data/Average_Side1_Side2.json")),
            # Material
            elastic_modulus  = m.get("elastic_modulus", 210000.0),
            poisson_ratio    = m.get("poisson_ratio", 0.3),

            # Mesh
            mesh_min     = ms.get("mesh_min", 0.6),
            mesh_max     = ms.get("mesh_max", 0.6),
            mesh_step    = ms.get("mesh_step", 0.05),
            length_min   = ms.get("length_min", 50),
            length_max   = ms.get("length_max", 50),
            length_step  = ms.get("length_step", 10),

            # Abaqus
            initial_inc     = abq.get("initialInc", 0.1),
            max_inc         = abq.get("maxInc", 1.0),
            max_num_inc     = abq.get("maxNumInc", 20),
            min_inc         = abq.get("minInc", 1e-6),
            nlgeom          = abq.get("nlgeom", False),
            time_period     = abq.get("timePeriod", 1.0),

            # Command
            abaqus_cmd   = d.get("abaqus_cmd", r"C:\SIMULIA\Commands\abq2021.bat")
        )
        return self.config