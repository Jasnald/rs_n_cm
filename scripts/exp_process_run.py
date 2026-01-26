import os
import sys

# Pega o diretório onde o script está (pasta 'scripts')
script_dir = os.path.dirname(os.path.abspath(__file__))

# Sobe um nível para a raiz do projeto e aponta para 'src'
# De: .../rs_n_cm/scripts -> .../rs_n_cm/src
src_path = os.path.join(script_dir, '..', 'src')
sys.path.append(os.path.abspath(src_path))

from exp_process.pipeline.surface import SurfacePipeline
from exp_process.pipeline.comparison import ComparisonPipeline
from exp_process.utils.io import IOUtils

def main():
    # 1. Configuração de Diretórios
    # Pega o diretório onde este script está (.../scripts)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Sobe um nível para pegar a raiz do projeto (.../rs_n_cm)
    project_root = os.path.dirname(script_dir) 

    # Agora aponta para a pasta data corretamente
    input_dir = os.path.join(project_root, "data", "input", "exp1")
    output_dir = os.path.join(project_root, "data", "output", "exp1")
    surface_output_dir = os.path.join(output_dir, "surface_data")

    # Debug para confirmar
    print(f"Raiz do projeto detectada: {project_root}")
    print(f"Procurando dados em: {input_dir}")

    print("=== INICIANDO PROCESSAMENTO EXP1 ===")
    print(f"Lendo de: {input_dir}")
    print(f"Salvando em: {output_dir}")

    # ---------------------------------------------------------
    # ETAPA 1: Processamento de Superfície (Pipeline)
    # ---------------------------------------------------------
    # Parâmetros: input, output, bottom_clean(0.2), wall_clean(1.5), general_clean(2.0)
    pipeline = SurfacePipeline(input_dir, output_dir, 0.2, 1.5, 2.0)
    io_utils = IOUtils() # Auxiliar para salvar os arquivos

    # Mapeia os arquivos (Side1, Side2, etc.)
    files_map = pipeline.map_files()
    
    if not files_map:
        print("ERRO: Nenhum arquivo compatível encontrado em 'data/input/exp1'.")
        print("Verifique se os nomes seguem o padrão: SideX_MeasurmentY_bottom.txt")
        return

    generated_models = []

    for side, measurements in files_map.items():
        print(f"\n>> Processando {side}...")
        
        # 1. Carrega e Limpa (agora separadamente bottom/wall conforme sua edição)
        points = pipeline.load_and_process_data(measurements)
        
        if points is None or len(points) == 0:
            print(f"   Aviso: Sem pontos válidos para {side}.")
            continue

        if points is not None:
            model = pipeline.fit_model(points, degree=2)
            model['side'] = side
            
            # --- ADIÇÃO: Salvar os pontos junto com o modelo ---
            # Convertendo para lista para ser compatível com JSON
            model['points'] = points.tolist() 
            # ---------------------------------------------------

            save_path = os.path.join(surface_output_dir, f"{side}.json")
            io_utils.save_json(model, save_path)
            generated_models.append(side)
            print(f"   Sucesso! Modelo salvo em: {save_path}")

    # ---------------------------------------------------------
    # ETAPA 2: Comparação (Subtração Exemplo)
    # ---------------------------------------------------------
    if len(generated_models) >= 2:
        print("\n=== INICIANDO COMPARAÇÃO ===")
        comp_pipe = ComparisonPipeline(surface_output_dir)
        
        # Exemplo: Subtrair Side1 (Target) - Side2 (Reference)
        # Ajuste os nomes conforme o que for gerado (ex: Side1, Side2)
        target = "Side1"
        reference = "Side2"
        
        print(f"Subtraindo: {target} - {reference}")
        comp_pipe.compute_subtraction(target, reference, f"Subtraction_{target}_minus_{reference}")
    else:
        print("\nMenos de 2 modelos gerados. Pulando etapa de comparação.")

    print("\n=== FINALIZADO ===")

if __name__ == "__main__":
    main()