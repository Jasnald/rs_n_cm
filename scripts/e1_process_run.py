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
from exp_process.core.segmenter import StepSegmenter
from exp_process.core.fitter import Fitter
from exp_process.core.operations import ModelOps
from exp_process.utils.io import IOUtils
from exp_process.gui.viewer import PointCloudViewer
from exp_process.core.transformer import DataTransformer
from processor import ExpProcessor

# Configurações Globais
INPUT_DIR = os.path.join(project_root, "data", "input", "exp1")
OUTPUT_DIR = os.path.join(project_root, "data", "output", "exp1")
SURFACE_DIR = os.path.join(OUTPUT_DIR, "surface_data")
HIGH_DEGREE = 4 # Grau detalhado
LOW_DEGREE = 1  # Grau para remover inclinação
IO = IOUtils()

sample_path = os.path.join(project_root, "data", "input", "exp1", "exp1_sample01.py")
    
print(f">> Lendo medições de: {os.path.basename(sample_path)}")
dimensoes_reais = ExpProcessor.process(sample_path)
largura_base = dimensoes_reais.get('h_width')

DATA_FIX_RULES = {
    "Side2": {
        "mirror_x": True,
        "mirror_ref": largura_base,
        "invert_z": False
    }
}



def step1_preprocess_and_segment():
    print("\n=== ETAPA 1: PRE-PROCESSAMENTO E SEGMENTAÇÃO ===")
    pipeline = SurfacePipeline(INPUT_DIR, OUTPUT_DIR, 1.2, 1.2, 1.5)
    files_map = pipeline.map_files()
    processed_files = []

    if not files_map:
        print("ERRO: Nenhum arquivo encontrado.")
        return []

    for side, measurements in files_map.items():
        print(f">> Processando {side}...")
        points = pipeline.load_and_process_data(measurements)
        
        if points is None or len(points) == 0: continue

        # Segmenta Passos
        steps_list = StepSegmenter.find_steps(points, threshold_percent=0.6)
        
        # Salva _Steps.json
        steps_data = {
            "id": side,
            "total_steps": len(steps_list),
            "steps": []
        }
        for i, step_pts in enumerate(steps_list):
            steps_data["steps"].append({
                "step_number": i + 1,
                "point_count": len(step_pts),
                "points": step_pts.tolist()
            })
            
        save_path = os.path.join(SURFACE_DIR, f"{side}_Steps.json")
        IO.save_json(steps_data, save_path)
        processed_files.append(side)
        
    return processed_files

def step2_manual_validation():
    print("\n=== ETAPA 2: VALIDAÇÃO MANUAL (GUI) ===")
    print(">> Edite os pontos e SALVE. Feche a janela para continuar.")
    
    root = tk.Tk()
    app = PointCloudViewer(root, input_dir=SURFACE_DIR)
    
    def on_closing():
        plt.close('all')
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
    print(">> Continuando...")

def step3_fitting_and_flattening(sides_list):
    """
    Replica a lógica do s4_Choosed_plane:
    1. Ajusta Grau Alto (4)
    2. Ajusta Grau Baixo (1)
    3. Subtrai (4 - 1) para "aplanar" a superfície
    """
    print(f"\n=== ETAPA 3: AJUSTE E APLANAMENTO ({HIGH_DEGREE} - {LOW_DEGREE}) ===")
    transformer = DataTransformer(DATA_FIX_RULES)


    for side in sides_list:
        step_file = os.path.join(SURFACE_DIR, f"{side}_Steps.json")
        if not os.path.exists(step_file): continue
            
        print(f">> Ajustando {side}...")
        data = IO.load_json(step_file)
        
        # Junta pontos de todos os passos
        all_points = []
        if 'steps' in data:
            for step in data['steps']:
                all_points.extend(step['points'])
        points_np = np.array(all_points)
        
        if len(points_np) < 10: continue

        print(f"   [Transform] Verificando regras para {side}...")
        points_np = transformer.apply(side, points_np)

        X, Y, Z = points_np[:, 0], points_np[:, 1], points_np[:, 2]

        # 1. Fit Grau Alto (Detalhe)
        model_high = Fitter.fit_2d_poly(X, Y, Z, degree=HIGH_DEGREE)
        
        # 2. Fit Grau Baixo (Referência/Inclinação)
        model_low = Fitter.fit_2d_poly(X, Y, Z, degree=LOW_DEGREE)
        
        # 3. Subtração (Aplanamento)
        # Isso cria uma superfície sem a inclinação da peça
        model_flat = ModelOps.subtract_coeffs(model_high, model_low)
        

        model_flat['side'] = side
        model_flat['points'] = points_np.tolist()
        model_flat['note'] = f"Subtraction: Degree {HIGH_DEGREE} - Degree {LOW_DEGREE}"
        
        # Salva como o JSON principal para a próxima etapa usar
        save_path = os.path.join(SURFACE_DIR, f"{side}.json")
        IO.save_json(model_flat, save_path)
        print(f"   Salvo modelo aplanado para {side}")

def step4_comparison():
    print("\n=== ETAPA 4: MÉDIA ENTRE LADOS (Side1 e Side2) ===") # Ajustei o texto
    
    file1 = os.path.join(SURFACE_DIR, "Side1.json")
    file2 = os.path.join(SURFACE_DIR, "Side2.json")
    
    if os.path.exists(file1) and os.path.exists(file2):
        print(">> Calculando Média (Average) entre Side1 e Side2...")
        
        m1 = IO.load_json(file1)
        m2 = IO.load_json(file2)
        
        # CORREÇÃO: Usar average_models em vez de subtract_coeffs
        # Note que average_models espera uma LISTA de modelos
        avg_model = ModelOps.average_models([m1, m2]) 
        
        avg_model['side'] = "Average_S1_S2" # Ajustei o nome para refletir a operação
        
        # Ajustar o nome do ficheiro de saída também
        save_path = os.path.join(SURFACE_DIR, "Average_Side1_Side2.json")
        IO.save_json(avg_model, save_path)
        print(">> Média salva com sucesso.")
    else:
        print(">> Arquivos Side1/Side2 não encontrados.")

def main():
    sides = step1_preprocess_and_segment()
    if not sides: return
    
    step2_manual_validation()
    
    # Aqui ocorre a mágica do antigo s4 (Deg N - Deg 1)
    step3_fitting_and_flattening(sides)
    
    step4_comparison()
    print("\n=== FIM ===")

if __name__ == "__main__":
    main()