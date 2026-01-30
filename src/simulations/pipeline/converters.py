# src/Simulations/pipeline/converters.py

from .imports import *
from .config import SimulationConfig
from simulations._inp_modules import *
from conversor.Npy_2_Xdmf import NPY2XDMFParameters, NpyBatchToXdmfConverter


class ResultConverter:
    def __init__(self, config: SimulationConfig):
        self.cfg = config

    def run_pipeline(self, method_type: str, target_dir_key: str, script_module: str):

        print(f"\n{'=' * 60}")
        print(f"RESULTS CONVERSION PIPELINE: {method_type}")
        print(f"{'=' * 60}\n")

        # --- ETAPA 1: Extração ODB -> NPY ---
        self._run_abaqus_extraction(script_module)

        # --- ETAPA 2: Conversão NPY -> XDMF ---
        self._run_npy_to_xdmf(method_type, target_dir_key)

    def _run_abaqus_extraction(self, script_module: str) -> bool:
        print(">>> Etapa 1: Extraindo dados do ODB (Abaqus Python)...")

        root_sim    = Path(__file__).parent.parent
        script_path = root_sim / script_module / "ODB_2_XDMF.py"

        python_cmd = f'"{self.cfg.abaqus_cmd}" python '

        script_config   = AbaqusScriptConfig(
            script_name = script_path.name,
            working_dir = str(script_path.parent),
            python_cmd  = python_cmd
        )

        runner = AbaqusScriptRunner(script_config)
        runner.run()

        print("✓ Extração ODB concluída.")
        return True

    def _run_npy_to_xdmf(self, method_type, target_dir_key):
        print("\n>>> Etapa 2: Convertendo NPY para XDMF/HDF5...")

        params_loader = NPY2XDMFParameters(
            method_type     = method_type,
            method_type_dir = target_dir_key
        )

        npy_root, out_dir, opts = params_loader.run()
        npy_files_dir = Path(npy_root) / "npy_files"

        batch = NpyBatchToXdmfConverter(str(npy_files_dir), out_dir, opts)
        batch.convert_all()

        print("\n✓ CONVERSÃO FINAL CONCLUÍDA COM SUCESSO")