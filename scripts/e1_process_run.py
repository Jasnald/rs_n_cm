import os
import sys
import numpy as np
import time
import tkinter as tk
import matplotlib.pyplot as plt
# Impede criação de cache
sys.dont_write_bytecode = True

# Configuração de Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, 'src')
sys.path.append(os.path.abspath(src_path))

# Importações do Pipeline
from exp_process.pipeline.surface import SurfacePipeline
from exp_process.pipeline.comparison import ComparisonPipeline
from exp_process.core.segmenter import StepSegmenter
from exp_process.core.fitter import Fitter
from exp_process.utils.io import IOUtils
from exp_process.gui.viewer import PointCloudViewer

# Configurações Globais
INPUT_DIR = os.path.join(project_root, "data", "input", "exp1")
OUTPUT_DIR = os.path.join(project_root, "data", "output", "exp1")
SURFACE_DIR = os.path.join(OUTPUT_DIR, "surface_data")
POLY_DEGREE = 4
IO = IOUtils()

def step1_preprocess_and_segment():
    """
    Equivalente ao antigo s1_Outline_process.
    Lê raw -> Limpa Outliers -> Segmenta Passos -> Salva _Steps.json
    """
    print("\n=== ETAPA 1: PRE-PROCESSAMENTO E SEGMENTAÇÃO ===")
    
    # Instancia pipeline apenas para usar as ferramentas de carregamento e limpeza
    pipeline = SurfacePipeline(INPUT_DIR, OUTPUT_DIR, 1.2, 1.2, 1.5)
    files_map = pipeline.map_files()
    
    processed_files = []

    if not files_map:
        print("ERRO: Nenhum arquivo de entrada encontrado.")
        return []

    for side, measurements in files_map.items():
        print(f">> Processando {side} (Raw -> Clean -> Steps)...")
        
        # 1. Carrega e Limpa (IQR)
        points = pipeline.load_and_process_data(measurements)
        
        if points is None or len(points) == 0:
            print(f"   Aviso: {side} vazio. Pulando.")
            continue

        # 2. Segmenta Passos
        steps_list = StepSegmenter.find_steps(points, threshold_percent=0.6)
        
        # 3. Estrutura e Salva
        steps_data = {
            "id": side,
            "total_steps": len(steps_list),
            "steps": []
        }
        
        for i, step_pts in enumerate(steps_list):
            steps_data["steps"].append({
                "step_number": i + 1,
                "point_count": len(step_pts),
                "points": step_pts.tolist() # Salva X, Y, Z
            })
            
        filename = f"{side}_Steps.json"
        save_path = os.path.join(SURFACE_DIR, filename)
        IO.save_json(steps_data, save_path)
        processed_files.append(side)
        
    return processed_files

def step2_manual_validation():
    """
    Equivalente ao antigo s2_Outline_gui.
    Abre a GUI e BLOQUEIA a execução até o usuário fechar a janela.
    """
    print("\n=== ETAPA 2: VALIDAÇÃO MANUAL (GUI) ===")
    print(">> Abrindo interface gráfica...")
    print(">> Faça suas alterações (Delete pontos) e clique em SALVAR.")
    print(">> FECHE a janela para continuar o script para a Etapa 3.")
    
    root = tk.Tk()
    # Abre apontando para a pasta onde salvamos os Steps na Etapa 1
    app = PointCloudViewer(root, input_dir=SURFACE_DIR)
    
    # --- CORREÇÃO: Garante que o script continue ao fechar ---
    def on_closing():
        print(">> Encerrando interface gráfica...")
        plt.close('all') # Fecha figuras do Matplotlib para não travar
        root.quit()      # Para o mainloop
        root.destroy()   # Destroi a janela
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    # ---------------------------------------------------------
    
    root.mainloop() # O script para aqui e espera o root.quit()
    
    print(">> Interface fechada. Continuando fluxo...")

def step3_surface_fitting(sides_list):
    """
    Equivalente ao antigo s3_Plane_process.
    Lê _Steps.json (possivelmente modificado) -> Ajusta Polinômio -> Salva _Model.json
    """
    print("\n=== ETAPA 3: AJUSTE DE SUPERFÍCIE (FIT) ===")
    
    for side in sides_list:
        step_file = os.path.join(SURFACE_DIR, f"{side}_Steps.json")
        
        if not os.path.exists(step_file):
            print(f"   Erro: Arquivo {step_file} não encontrado.")
            continue
            
        print(f">> Ajustando modelo para {side} (Lendo {os.path.basename(step_file)})...")
        
        # 1. Carrega dados (Pode ter sido editado na GUI)
        data = IO.load_json(step_file)
        
        # 2. Achata os passos de volta para uma nuvem de pontos única para o Fit
        all_points = []
        if 'steps' in data:
            for step in data['steps']:
                all_points.extend(step['points'])
        
        points_np = np.array(all_points)
        
        if len(points_np) < 10:
            print("   Poucos pontos para ajuste. Pulando.")
            continue
            
        # 3. Faz o Fit (Fitter espera X, Y, Z)
        # points_np[:, 0] = X, [:, 1] = Y, [:, 2] = Z
        model = Fitter.fit_2d_poly(points_np[:, 0], points_np[:, 1], points_np[:, 2], degree=POLY_DEGREE)
        
        # 4. Adiciona metadados e salva
        model['side'] = side
        model['points'] = points_np.tolist() # Guarda pontos usados no fit
        
        # Salva como SideX_Model.json (ou SideX.json para manter compatibilidade)
        save_path = os.path.join(SURFACE_DIR, f"{side}.json")
        IO.save_json(model, save_path)

def step4_comparison():
    """
    Equivalente ao antigo s4_Choosed_plane.
    Lê Side1.json e Side2.json -> Subtrai -> Salva Subtraction.json
    """
    print("\n=== ETAPA 4: COMPARAÇÃO E SUBTRAÇÃO ===")
    
    file1 = os.path.join(SURFACE_DIR, "Side1.json")
    file2 = os.path.join(SURFACE_DIR, "Side2.json")
    
    if os.path.exists(file1) and os.path.exists(file2):
        print(">> Executando subtração: Side1 - Side2...")
        comp_pipe = ComparisonPipeline(SURFACE_DIR)
        comp_pipe.compute_subtraction("Side1", "Side2", "Subtraction_Side1_Side2")
    else:
        print(">> Arquivos necessários para subtração (Side1, Side2) não encontrados.")

def main():
    # 1. Roda S1 (Gera dados brutos segmentados)
    processed_sides = step1_preprocess_and_segment()
    
    if not processed_sides:
        print("Processo abortado na Etapa 1.")
        return

    # 2. Roda S2 (GUI para intervenção humana)
    # Comente esta linha se quiser rodar tudo direto sem abrir a janela
    step2_manual_validation() 
    
    # 3. Roda S3 (Gera a matemática baseada nos dados, possivelmente editados)
    step3_surface_fitting(processed_sides)
    
    # 4. Roda S4 (Gera resultados finais)
    step4_comparison()
    
    print("\n=== FLUXO COMPLETO FINALIZADO COM SUCESSO ===")

if __name__ == "__main__":
    main()