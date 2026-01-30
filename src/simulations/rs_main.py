"""
REA_Main.py (Refatorado & Limpo)
Orquestrador do Workflow de Residual Stresses Analysis.
"""
from pathlib import Path

_here = Path(__file__).resolve().parent
_src_root = _here.parent.parent

from Exp_Data.s1_exp import CONFIG_PATH
from ElementProcess import Nodes_main, StressProcessor
from _inp_modules import INPRunner
from pipeline import *
from cm_main import main as cma_main


def main(run_cma=True, run_rsa=True, convertion_process_rsa=True):
    # 1. Rodar CMA se solicitado (Dependência)
    if run_cma:
        print("🔄 RODANDO DEPENDÊNCIA: CONTOUR METHOD (CMA)")
        cma_main(default_process=True, convertion_process=True)

    print("🚀 INICIANDO WORKFLOW: RESIDUAL STRESSES (RSA)")

    # 2. Carregar Configuração
    cfg_manager = ConfigurationManager(CONFIG_PATH)
    config = cfg_manager.load()

    # --- ETAPA DE SIMULAÇÃO ---
    if run_rsa:
        print("\n--- [FASE 1] PREPARAÇÃO E SIMULAÇÃO ---")

        # A. Limpeza
        ClearDirectory(config.rea_directory)
        print(f"✓ Diretório limpo: {config.rea_directory}")

        # B. Geração de Geometria
        rsa_script = _here / "rsa" /"REA_Extended.py"
        rsa_script = _here / "tests" / "REA_Extended.py"
        config.geometry_script = rsa_script

        params_list = ParameterGenerator.generate_combinations(config)

        geo_gen = GeometryGenerator(config)
        geo_gen.run_batch(params_list, config.rea_directory)

        # C. Processamento de Nós e Tensões (Módulos ElementProcess)
        print("\n>>> Processando Mapa de Tensões (ElementProcess)...")
        # Nodes_main e StressProcessor ainda esperam string paths
        Nodes_main(str(config.rea_directory), use_s1=True, use_s2=False, use_s3=False)

        cm_hdf5_path = config.cm_directory / "xdmf_hdf5_files"
        proc = StressProcessor(str(config.rea_directory), tolerance=5e-2, chunk_size=10000)
        proc.process_all_simulations(str(cm_hdf5_path))

        # D. Aplicação das Tensões no INP (Pipeline)
        processor = ResidualProcessor(config)
        processor.run_batch()

        # E. Execução (Runners)
        runner = INPRunner(
            base_dir    = config.rea_directory,
            abaqus_path = config.abaqus_cmd
        )
        runner.run_all(silent=True)

    # --- ETAPA DE CONVERSÃO ---
    if convertion_process_rsa:
        print("\n--- [FASE 2] CONVERSÃO DE RESULTADOS ---")

        converter = ResultConverter(config)
        converter.run_pipeline(
            method_type     = "Residual_Stresses_Analysis",
            target_dir_key  = "REA_directory",
            script_module   = "rsa"
        )
    print("✅ WORKFLOW RSA CONCLUÍDO COM SUCESSO!")

if __name__ == "__main__":
    main(run_cma=False,
         run_rsa=True,
         convertion_process_rsa=True)