"""
CM_Main.py (Refatorado & Limpo)
Orquestrador do Workflow de Contour Method.
"""
from pathlib import Path

_here = Path(__file__).resolve().parent
_src_root = _here.parent.parent


CONFIG_PATH = _src_root / "data" / "config.json"

print(f"{_src_root}")
print(f"{CONFIG_PATH}")

from _inp_modules import *
from pipeline import *


def main(default_process=True, convertion_process=True):
    print("🚀 INICIANDO WORKFLOW: CONTOUR METHOD")

    # 1. Carregar Configuração (Centralizada)
    cfg_manager = ConfigurationManager(CONFIG_PATH)
    config = cfg_manager.load()

    # --- ETAPA DE SIMULAÇÃO ---
    if default_process:
        print("\n--- [FASE 1] PREPARAÇÃO E SIMULAÇÃO ---")

        ClearDirectory(config.cm_directory)
        print(f"✓ Diretório limpo: {config.cm_directory}")

        #sim_script = _here / rsa /"REA_Extended.py"
        #config.geometry_script = sim_script

        params_list = ParameterGenerator.generate_combinations(config)

        geo_gen = GeometryGenerator(config)
        geo_gen.run_batch(params_list, config.cm_directory)

        processor = ContourProcessor(config)
        processor.run_batch(use_default_single_file=True)

        runner = INPRunner(
            base_dir    = config.cm_directory,
            abaqus_path = config.abaqus_cmd
        )

        runner.run_all(silent=True)

    # --- ETAPA DE CONVERSÃO ---
    if convertion_process:
        print("\n--- [FASE 2] CONVERSÃO DE RESULTADOS ---")

        converter = ResultConverter(config)
        converter.run_pipeline(
            method_type     = "Contour_Method",
            target_dir_key  = "CM_directory",
            script_module   = "cma"
        )
    print("✅ WORKFLOW CONCLUÍDO COM SUCESSO!")

if __name__ == "__main__":
    main(default_process=True,
         convertion_process=True)