"""
CMA2_Main.py (Refatorado & Limpo)
Orquestrador do Workflow de Contour Method Analysis (CMA).
"""
from pathlib import Path

_here = Path(__file__).resolve().parent
_src_root = _here.parent.parent

# Imports do Pipeline Moderno
from Exp_Data.s1_exp import CONFIG_PATH
from _inp_modules import INPRunner
from pipeline import *

def _run_simulation_phase(config):
    """Executa a fase de geometria e simulação FEM."""
    print("\n--- [FASE 1] PREPARAÇÃO E SIMULAÇÃO ---")

    # 1. Limpeza do Diretório
    ClearDirectory(config.cm_directory)
    print(f"✓ Diretório limpo: {config.cm_directory}")

    # 2. Definição do Script de Geometria
    sim_script = _here / "cma2" / "attempt2_copy.py"
    json_dir   = _src_root /"src"/"Preprocess"/"exp2"/"Sample_postprocess"/"Choosed_plane"

    config.geometry_script = sim_script
    config.polynomial_json_dir = json_dir

    # 3. Geração de Combinações e Geometria (Abaqus CAE)
    params_list = ParameterGenerator.generate_combinations(config)

    geo_gen = GeometryGenerator(config)
    geo_gen.run_batch(params_list, config.cm_directory)

    # 4. Processamento dos INPs (Aplica condições de contorno do CM)
    processor = ContourProcessor(config)
    processor.run_batch()

    # 5. Execução dos Jobs (Abaqus Solver)
    runner = INPRunner(
        base_dir=config.cm_directory,
        abaqus_path=config.abaqus_cmd
    )
    runner.run_all(silent=True)

def _run_conversion_phase(config):
    """Executa a conversão de resultados (ODB -> NPY -> XDMF)."""
    print("\n--- [FASE 2] CONVERSÃO DE RESULTADOS ---")

    converter = ResultConverter(config)
    converter.run_pipeline(
        method_type="Contour_Method",
        target_dir_key="CM_directory",
        script_module="cma"
    )

def main(default_process=True, convertion_process=True):
    print("🚀 INICIANDO WORKFLOW: CONTOUR METHOD (CMA)")
    # 1. Carregar Configuração
    cfg_manager = ConfigurationManager(CONFIG_PATH)
    config = cfg_manager.load()

    if default_process:_run_simulation_phase(config)
    if convertion_process:_run_conversion_phase(config)

    print("\n✅ WORKFLOW CMA CONCLUÍDO COM SUCESSO!")


if __name__ == "__main__":
    # Permite rodar apenas conversão ou apenas simulação se necessário
    main(default_process=True, convertion_process=True)