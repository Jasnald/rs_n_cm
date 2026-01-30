# src/Simulations/_pipelines/generators.py

from .imports import *
from .config import *
from simulations._inp_modules import *

class ParameterGenerator:
    """Gera a lista de combinações (Mesh Size x Length)."""

    @staticmethod
    def generate_combinations(cfg: SimulationConfig) -> List[Dict]:
        # Usa numpy para criar os ranges (igual ao seu código original)
        # Adiciona um pequeno epsilon no max para garantir inclusão se for float
        mesh_sizes = np.arange(cfg.mesh_min, cfg.mesh_max + cfg.mesh_step / 100, cfg.mesh_step)
        lengths = np.arange(cfg.length_min, cfg.length_max + 1, cfg.length_step)

        combinations = []
        for mesh in mesh_sizes:
            for length in lengths:
                sim_id = f"Mesh-{mesh:.2f}--Length-{int(length)}".replace('.', '_')

                param = {
                    'simulation_id': sim_id,
                    # Parâmetros Geométricos
                    'mesh_size': round(mesh, 2),
                    'comprimento': int(length),

                    # Parâmetros de Simulação (Repassados para o script do CAE)
                    'initialInc': cfg.initial_inc,
                    'maxInc': cfg.max_inc,
                    'maxNumInc': cfg.max_num_inc,
                    'minInc': cfg.min_inc,
                    'nlgeom': cfg.nlgeom,
                    'time': cfg.time_period,

                    # Material (Para referência no script CAE se precisar)
                    'elastic_modulus': cfg.elastic_modulus,
                    'poisson_ratio': cfg.poisson_ratio,
                }
                combinations.append(param)

        return combinations


class GeometryGenerator:
    """Roda o Abaqus CAE para criar os .inp iniciais."""
    def __init__(self, config: SimulationConfig):
        self.cfg = config

    def run_batch(self, params_list: List[Dict], target_dir: Path):
        """Gera geometria para toda a lista de parâmetros."""
        print(f"\n--- Gerando Geometria ({len(params_list)} casos) ---")

        script_path = self.cfg.geometry_script
        for i, params in enumerate(params_list, 1):
            sim_id = params['simulation_id']
            sim_dir = target_dir / sim_id
            sim_dir.mkdir(parents=True, exist_ok=True)

            # Prepara ambiente
            env = os.environ.copy()
            env['SIMULATION_OUTPUT_PATH'] = str(sim_dir)
            env['SIMULATION_PARAMETERS']  = json.dumps(params)

            # Usa o runner
            script_config = AbaqusScriptConfig(
                script_name = str(self.cfg.geometry_script),
                python_cmd  = f'"{self.cfg.abaqus_cmd}" cae noGUI=',
                working_dir = str(sim_dir)
            )

            runner = AbaqusScriptRunner(script_config)

            print(f"[{i}/{len(params_list)}] Criando: {sim_id}")

            # Passa o environment customizado
            runner.config.env = env  # Adicione env ao dataclass se não tiver
            runner.run()

            expected_inp = sim_dir / f"{sim_id}.inp"
            print(f"   -> {expected_inp.name}")
