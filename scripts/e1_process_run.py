import os
import sys

# Impede criação de cache
sys.dont_write_bytecode = True

# Configuração de Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, 'src')
sys.path.append(os.path.abspath(src_path))

import tkinter as tk
from exp_process.pipeline.surface import SurfacePipeline
from exp_process.pipeline.comparison import ComparisonPipeline
from exp_process.utils.io import IOUtils
from exp_process.gui.viewer import PointCloudViewer

def main():
    POLY_DEGREE = 4
    input_dir = os.path.join(project_root, "data", "input", "exp1")
    output_dir = os.path.join(project_root, "data", "output", "exp1")
    surface_output_dir = os.path.join(output_dir, "surface_data")

    print("=== INICIANDO PROCESSAMENTO EXP1 ===")

    # 1. Processamento Automático (Equivalente ao s1 e s3)
    pipeline = SurfacePipeline(input_dir, output_dir, 0.2, 1.5, 2.0)
    io_utils = IOUtils()
    files_map = pipeline.map_files()
    
    if not files_map:
        print("Erro: Arquivos não encontrados.")
        return

    generated_models = []
    for side, measurements in files_map.items():
        print(f">> Ajustando polinômio para {side}...")
        points = pipeline.load_and_process_data(measurements)
        
        if points is not None:
            model = pipeline.fit_model(points, degree=POLY_DEGREE)
            model['side'] = side
            model['degree'] = POLY_DEGREE
            model['points'] = points.tolist() # Salva pontos para a GUI mostrar
            
            save_path = os.path.join(surface_output_dir, f"{side}.json")
            io_utils.save_json(model, save_path)
            generated_models.append(side)

    # 2. Comparação Automática (Equivalente ao s4)
    if len(generated_models) >= 2:
        comp_pipe = ComparisonPipeline(surface_output_dir)
        comp_pipe.compute_subtraction("Side1", "Side2", "Subtraction_Side1_Side2")

    print("=== PROCESSAMENTO CONCLUÍDO. ABRINDO INTERFACE DE VALIDAÇÃO... ===")

    # 3. Interface Gráfica (Equivalente ao s2)
    root = tk.Tk()
    app = PointCloudViewer(root, input_dir=surface_output_dir)
    root.mainloop()

if __name__ == "__main__":
    main()