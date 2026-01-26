"""
s1_Outline_process.py
What it does:
This script processes experimental measurement data by combining, averaging, and cleaning point cloud files from different sides and steps. It supports combining bottom and wall data, calculating averages, detecting steps, and performing iterative outlier removal using IQR-based methods. The output is a set of cleaned and structured files ready for further analysis or visualization.

Example of use:
    Run this script directly to process all measurement files in the 'Sample_og' directory, producing cleaned and averaged results in 'Sample_postprocess'.

    python Outline_process.py
"""
import os
import re
import numpy as np
import json
from collections import defaultdict
import time
from scipy import stats



def combine_bottom_wall_files():
    """
    combine_bottom_wall_files / (function)
    What it does:
    Combines '_bottom' and '_wall' measurement files for each side and measurement, adding #bottom and #wall markers for identification. Outputs a single .txt file per measurement in the postprocess directory.
    """
    print("\n\nIniciando processamento de arquivos...")

    # Define caminhos dos diretórios
    base_dir = os.path.dirname(os.path.abspath(__file__))
    original_dir = os.path.join(base_dir, "Sample_og")
    output_dir = os.path.join(base_dir, "Sample_postprocess")

    # Cria o diretório de saída, se necessário
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Diretório de saída criado: {output_dir}")

    # Regex para identificar arquivos como "SideX_MeasurmentY_bottom"
    bottom_pattern = re.compile(r'(Side(\d+)_Measurment(\d+))_bottom')

    processed_count = 0
    error_count = 0

    # Dicionário para agrupar arquivos por lado (Side)
    side_files = defaultdict(list)

    # Lista todos os arquivos no diretório original
    try:
        all_files = os.listdir(original_dir)
    except FileNotFoundError:
        print(f"Erro: Diretório não encontrado: {original_dir}")
        return {}

    # Filtra para os arquivos contendo "_bottom"
    bottom_files = [f for f in all_files if "_bottom" in f]
    if not bottom_files:
        print("Nenhum arquivo '_bottom' encontrado no diretório original.")
        return {}

    print(f"Encontrados {len(bottom_files)} arquivos '_bottom' para processar.")

    # Combina _bottom e _wall -> gera um único arquivo .txt para cada medição
    for bottom_file in bottom_files:
        match = bottom_pattern.search(bottom_file)
        if not match:
            print(f"Pulando arquivo com formato inesperado: {bottom_file}")
            continue

        base_name = match.group(1)      # ex.: "Side1_Measurment2"
        side_num = match.group(2)       # ex.: "1"
        measurement_num = match.group(3)  # ex.: "2"

        wall_file_prefix = f"{base_name}_wall"
        output_file = f"{base_name}.txt"

        # Procura o arquivo de parede correspondente
        wall_file_path = None
        for f in all_files:
            if f.startswith(wall_file_prefix):
                wall_file_path = os.path.join(original_dir, f)
                break

        if not wall_file_path:
            print(f"Aviso: Arquivo de parede correspondente não encontrado para {bottom_file}")
            error_count += 1
            continue

        bottom_file_path = os.path.join(original_dir, bottom_file)
        output_file_path = os.path.join(output_dir, output_file)

        try:
            # Combina os conteúdos dos arquivos bottom e wall
            with open(bottom_file_path, 'r') as bf, open(wall_file_path, 'r') as wf, open(output_file_path, 'w') as of:
                # Adiciona marcador para dados bottom
                of.write("#bottom\n")
                bottom_content = bf.read()
                of.write(bottom_content)

                # Adiciona uma nova linha se necessário
                if bottom_content and not bottom_content.endswith('\n'):
                    of.write('\n')

                # Adiciona marcador para dados wall
                of.write("#wall\n")
                wall_content = wf.read()
                of.write(wall_content)

            print(f"Arquivo criado com sucesso: {output_file}")
            processed_count += 1

            # Armazena para processamento posterior (média)
            side_key = f"Side{side_num}"
            side_files[side_key].append((output_file_path, int(measurement_num)))

        except Exception as e:
            print(f"Erro ao processar {base_name}: {str(e)}")
            error_count += 1

    print("\nProcessamento de arquivos combinados concluído!")
    print(f"Arquivos processados com sucesso: {processed_count}")
    print(f"Erros encontrados: {error_count}")

    return side_files

def calculate_average_for_sides(side_files):
    """
    calculate_average_for_sides / (function)
    What it does:
    For each side, calculates the average of all combined measurement files, keeping #bottom and #wall sections. Handles shape mismatches by trimming to the minimum number of rows. Outputs an average file per side.
    """
    print("\nCalculando médias para cada lado...")
    average_count = 0
    error_count = 0

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "Sample_postprocess")

    # Dicionário para armazenar os arquivos de média por lado
    side_average_files = {}

    for side, files_info in side_files.items():
        # Ordena por número de medição
        files_info.sort(key=lambda x: x[1])

        if len(files_info) < 2:
            print(f"Pulando {side}: Apenas {len(files_info)} medição(ões) encontrada(s) (necessário pelo menos 2).")
            continue

        try:
            # Lê os dados mantendo as seções #bottom e #wall
            bottom_data_sets = []
            wall_data_sets = []

            for file_path, _ in files_info:
                with open(file_path, 'r') as f:
                    lines = f.readlines()

                current_section = None
                bottom_lines = []
                wall_lines = []

                for line in lines:
                    line = line.strip()
                    if line == "#bottom":
                        current_section = "bottom"
                    elif line == "#wall":
                        current_section = "wall"
                    elif line and not line.startswith("#") and current_section:
                        try:
                            values = list(map(float, line.split()))
                            if current_section == "bottom":
                                bottom_lines.append(values)
                            else:
                                wall_lines.append(values)
                        except ValueError:
                            # Ignora linhas inválidas
                            pass

                if bottom_lines:
                    bottom_data_sets.append(np.array(bottom_lines))
                if wall_lines:
                    wall_data_sets.append(np.array(wall_lines))

            # Calcula a média para dados bottom
            if bottom_data_sets:
                bottom_shapes = [arr.shape for arr in bottom_data_sets]
                if len(set(bottom_shapes)) > 1:
                    print(f"Aviso: Arquivos bottom para {side} têm formas diferentes {bottom_shapes}. Usando apenas o número mínimo de linhas.")
                    min_rows = min(shape[0] for shape in bottom_shapes)
                    trimmed_data = [arr[:min_rows] for arr in bottom_data_sets]
                    bottom_avg = np.mean(trimmed_data, axis=0)
                else:
                    bottom_avg = np.mean(bottom_data_sets, axis=0)
            else:
                bottom_avg = np.array([])

            # Calcula a média para dados wall
            if wall_data_sets:
                wall_shapes = [arr.shape for arr in wall_data_sets]
                if len(set(wall_shapes)) > 1:
                    print(f"Aviso: Arquivos wall para {side} têm formas diferentes {wall_shapes}. Usando apenas o número mínimo de linhas.")
                    min_rows = min(shape[0] for shape in wall_shapes)
                    trimmed_data = [arr[:min_rows] for arr in wall_data_sets]
                    wall_avg = np.mean(trimmed_data, axis=0)
                else:
                    wall_avg = np.mean(wall_data_sets, axis=0)
            else:
                wall_avg = np.array([])

            # Salva o arquivo de média
            average_file = f"{side}_Average.txt"
            average_file_path = os.path.join(output_dir, average_file)

            with open(average_file_path, 'w') as f:
                if len(bottom_avg) > 0:
                    f.write("#bottom\n")
                    np.savetxt(f, bottom_avg, fmt='%.6f')

                if len(wall_avg) > 0:
                    f.write("#wall\n")
                    np.savetxt(f, wall_avg, fmt='%.6f')

            side_average_files[side] = average_file_path

            print(f"Arquivo de média criado com sucesso: {average_file}")
            average_count += 1

        except Exception as e:
            print(f"Erro ao calcular média para {side}: {str(e)}")
            error_count += 1

    print("\nCálculo de média concluído!")
    print(f"Arquivos de média criados: {average_count}")
    print(f"Total de erros encontrados até agora: {error_count}")

    return side_average_files

def detect_steps(side_average_files):
    """
    detect_steps / (function)
    What it does:
    Detects step changes along the X axis in the averaged data for each side, segments the data into steps, and writes a JSON file per side with structured step and point information. Intended to be run before outlier cleaning.
    """
    print("\nDetectando passos no eixo X e gerando JSON...")
    steps_files = {}
    error_count = 0

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "Sample_postprocess")

    for side, avg_file_path in side_average_files.items():
        steps_file_name = f"{side}_Steps.json"
        steps_file_path = os.path.join(output_dir, steps_file_name)

        try:
            # Carrega os dados do arquivo de média
            all_data = []
            current_section = None

            with open(avg_file_path, 'r') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if line == "#bottom" or line == "#wall":
                    current_section = line[1:]  # remove o '#' para obter "bottom" ou "wall"
                elif line and not line.startswith("#"):
                    try:
                        values = list(map(float, line.split()))
                        if len(values) >= 3:
                            all_data.append([float(values[0]), float(values[1]), float(values[2]), current_section])
                        # Apenas linhas com pelo menos 3 valores são consideradas
                    except ValueError:
                        pass

            if not all_data:
                print(f"Aviso: Não há dados válidos em {side} para detectar passos.")
                continue

            # Converte para array numpy (dtype=object para acomodar strings)
            data_array = np.array(all_data, dtype=object)

            if len(data_array) < 2:
                print(f"Aviso: Poucos pontos em {side} para detectar passos.")
                continue

            # Extrai as colunas numéricas para ordenação
            numeric_data = data_array[:, :3].astype(float)
            sorted_indices = np.lexsort((numeric_data[:, 1], numeric_data[:, 0]))
            sorted_data = data_array[sorted_indices]

            # Detecta mudanças de passo (quando X muda mais de 0.6%)
            x_values = sorted_data[:, 0].astype(float)
            x_diff_percent = np.zeros_like(x_values)
            x_diff_percent[1:] = 100 * np.abs(x_values[1:] - x_values[:-1]) / (np.abs(x_values[:-1]) + 1e-10)

            # Encontra índices onde a diferença é maior que 0.6%
            step_indices = np.where(x_diff_percent > 0.6)[0]

            if len(step_indices) == 0:
                step_boundaries = [0, len(sorted_data)]
            else:
                step_boundaries = [0] + list(step_indices) + [len(sorted_data)]

            # Prepara a estrutura do JSON
            steps_data = {
                "side": side,
                "total_steps": len(step_boundaries) - 1,
                "steps": []
            }

            for i in range(len(step_boundaries) - 1):
                start_idx = step_boundaries[i]
                end_idx = step_boundaries[i+1]
                step_data = sorted_data[start_idx:end_idx]
                mean_x = float(np.mean(step_data[:, 0].astype(float)))

                step_info = {
                    "step_number": i + 1,
                    "point_count": len(step_data),
                    "mean_x": mean_x,
                    "points": []
                }

                for point in step_data:
                    x, y, z, section = point
                    step_info["points"].append({
                        "x": float(x),
                        "y": float(y),
                        "z": float(z),
                        "section": section
                    })

                steps_data["steps"].append(step_info)

            # Salva o JSON dos passos
            with open(steps_file_path, 'w') as f:
                json.dump(steps_data, f, indent=2)

            steps_files[side] = steps_file_path
            print(f"Arquivo JSON de passos criado com sucesso: {steps_file_name} com {len(step_boundaries) - 1} passos")

        except Exception as e:
            print(f"Erro ao criar arquivo de passos para {side}: {str(e)}")
            error_count += 1

    print("\nDetecção de passos concluída!")
    print(f"Arquivos JSON de passos criados: {len(steps_files)}")
    print(f"Total de erros encontrados: {error_count}")

    return steps_files

def run_iterative_outlier_cleaning(steps_files, num_iterations=2, params_per_iteration=None):
    """
    run_iterative_outlier_cleaning / (function)
    What it does:
    Performs iterative outlier cleaning on step files, applying multiple passes with potentially different IQR parameters for each iteration. Returns a dictionary of cleaned file paths after all iterations.
    Args:
        steps_files: Dictionary mapping side to step file path
        num_iterations: Number of cleaning iterations to perform
        params_per_iteration: List of IQR parameter dicts for each iteration (optional)
    Returns:
        Dictionary of cleaned file paths after all iterations
    """
    if params_per_iteration is None:
        # Parâmetros padrão para cada iteração - primeira mais restritiva, depois mais permissiva
        params_per_iteration = [
            # Primeira iteração - Remove outliers mais extremos
            {
                "bottom": {"xz": (1, 1), "yz": (1, 1)},
                "wall": {"xz": (1, 1), "yz": (1, 1)},
                "default": {"xz": (1.5, 1.5), "yz": (1.5, 1.5)}
            }
        ]
        
        # Adicionar mais iterações se necessário
        if num_iterations > len(params_per_iteration):
            for i in range(len(params_per_iteration), num_iterations):
                # Iterações adicionais usam parâmetros da última iteração configurada
                params_per_iteration.append(params_per_iteration[-1])
    
    print(f"\n{'='*80}")
    print(f"INICIANDO PROCESSO DE LIMPEZA ITERATIVA - {num_iterations} ITERAÇÕES")
    print(f"{'='*80}")
    
    current_files = steps_files
    
    for iteration in range(num_iterations):
        print(f"\n{'-'*80}")
        print(f"ITERAÇÃO {iteration+1}/{num_iterations}")
        print(f"{'-'*80}")
        
        # Obtém os parâmetros para esta iteração
        if iteration < len(params_per_iteration):
            current_params = params_per_iteration[iteration]
        else:
            current_params = params_per_iteration[-1]
        
        # Executa a limpeza para esta iteração
        cleaned_files = IQR_outliers_section_specific(current_files, current_params)
        
        # Atualiza os arquivos para a próxima iteração
        current_files = cleaned_files
        
        print(f"\nIteração {iteration+1} concluída. Arquivos processados: {len(cleaned_files)}")
    
    print(f"\n{'='*80}")
    print(f"PROCESSO DE LIMPEZA ITERATIVA CONCLUÍDO - {num_iterations} ITERAÇÕES")
    print(f"{'='*80}")
    
    return current_files


def IQR_outliers_section_specific(steps_files, section_params=None):
    """
    IQR_outliers_section_specific / (function)
    What it does:
    Removes outliers from each step of the data using IQR-based methods, applying cleaning to both XZ and YZ coordinates with section-specific parameters. Returns a dictionary of cleaned file paths.
    Args:
        steps_files: Dictionary mapping side to step file path
        section_params: Dictionary of IQR parameters for each section (optional)
            Format: {"section_name": {"xz": (factor_x, factor_z), "yz": (factor_y, factor_z)}}
    """
    if section_params is None:
        # Valores padrão para cada tipo de seção
        section_params = {
            "bottom": {"xz": (0.2, 0.2), "yz": (0.2, 0.2)},  # Mais restritivo para bottom
            "wall": {"xz": (1.5, 1.5), "yz": (1.5, 1.5)},    # Mais permissivo para wall
            "default": {"xz": (1.0, 1.0), "yz": (1.0, 1.0)}  # Valores padrão para outras seções
        }
    
    print("\nIniciando limpeza de outliers com parâmetros específicos por seção...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "Sample_postprocess")
    os.makedirs(output_dir, exist_ok=True)
    
    cleaned_files = {}
    error_count = 0
    
    for side, steps_file_path in steps_files.items():
        try:
            # Gera um nome de arquivo com indicador de iteração
            iteration_indicator = ""
            if "_Cleaned_" in steps_file_path:
                # Arquivo já foi processado anteriormente, incrementa o contador de iteração
                if "_Iter" in steps_file_path:
                    current_iter = int(re.search(r"_Iter(\d+)_", steps_file_path).group(1))
                    iteration_indicator = f"_Iter{current_iter+1}"
                else:
                    iteration_indicator = "_Iter2"
            else:
                iteration_indicator = "_Iter1"
            
            with open(steps_file_path, 'r') as f:
                steps_data = json.load(f)
            
            # Nome do arquivo de saída com indicador de iteração
            file_basename = os.path.basename(steps_file_path)
            name_parts = file_basename.split("_Cleaned_")
            if len(name_parts) > 1:
                side_part = name_parts[0]
            else:
                side_part = side
                
            cleaned_file_name = f"{side_part}_Cleaned{iteration_indicator}_IQR.json"
            cleaned_file_path = os.path.join(output_dir, cleaned_file_name)
            cleaned_data = steps_data.copy()
            
            total_points_original = 0
            total_points_cleaned = 0
            outliers_removed = 0
            
            for step_idx, step in enumerate(steps_data["steps"]):
                # Organiza os pontos por seção (bottom/wall)
                sections = {}
                for point in step["points"]:
                    section = point["section"]
                    if section not in sections:
                        sections[section] = []
                    sections[section].append(point)
                
                cleaned_points = []
                step_removed_count = 0
                
                for section, section_points in sections.items():
                    section_orig_count = len(section_points)
                    total_points_original += section_orig_count
                    
                    if len(section_points) <= 5:
                        # Poucos pontos para análise estatística, mantém todos
                        cleaned_points.extend(section_points)
                        continue
                    
                    # Obtém os parâmetros específicos para esta seção ou usa os padrões
                    if section in section_params:
                        params = section_params[section]
                    else:
                        params = section_params["default"]
                    
                    # Extração das coordenadas para análise
                    x_values = np.array([point["x"] for point in section_points])
                    y_values = np.array([point["y"] for point in section_points])
                    z_values = np.array([point["z"] for point in section_points])
                    
                    # Aplicando IQR para coordenadas XZ
                    mask_xz = np.ones(len(section_points), dtype=bool)
                    
                    # Processamento para coordenada X
                    q1_x = np.percentile(x_values, 25)
                    q3_x = np.percentile(x_values, 75)
                    iqr_x = q3_x - q1_x
                    factor_x = params["xz"][0]
                    lower_bound_x = q1_x - factor_x * iqr_x
                    upper_bound_x = q3_x + factor_x * iqr_x
                    mask_x = (x_values >= lower_bound_x) & (x_values <= upper_bound_x)
                    mask_xz = mask_xz & mask_x
                    
                    # Processamento para coordenada Z (em contexto XZ)
                    q1_z_x = np.percentile(z_values, 25)
                    q3_z_x = np.percentile(z_values, 75)
                    iqr_z_x = q3_z_x - q1_z_x
                    factor_z_x = params["xz"][1]
                    lower_bound_z_x = q1_z_x - factor_z_x * iqr_z_x
                    upper_bound_z_x = q3_z_x + factor_z_x * iqr_z_x
                    mask_z_x = (z_values >= lower_bound_z_x) & (z_values <= upper_bound_z_x)
                    mask_xz = mask_xz & mask_z_x
                    
                    # Aplicando IQR para coordenadas YZ
                    mask_yz = np.ones(len(section_points), dtype=bool)
                    
                    # Processamento para coordenada Y
                    q1_y = np.percentile(y_values, 25)
                    q3_y = np.percentile(y_values, 75)
                    iqr_y = q3_y - q1_y
                    factor_y = params["yz"][0]
                    lower_bound_y = q1_y - factor_y * iqr_y
                    upper_bound_y = q3_y + factor_y * iqr_y
                    mask_y = (y_values >= lower_bound_y) & (y_values <= upper_bound_y)
                    mask_yz = mask_yz & mask_y
                    
                    # Processamento para coordenada Z (em contexto YZ)
                    q1_z_y = np.percentile(z_values, 25)
                    q3_z_y = np.percentile(z_values, 75)
                    iqr_z_y = q3_z_y - q1_z_y
                    factor_z_y = params["yz"][1]
                    lower_bound_z_y = q1_z_y - factor_z_y * iqr_z_y
                    upper_bound_z_y = q3_z_y + factor_z_y * iqr_z_y
                    mask_z_y = (z_values >= lower_bound_z_y) & (z_values <= upper_bound_z_y)
                    mask_yz = mask_yz & mask_z_y
                    
                    # Combinando as máscaras - um ponto é mantido se estiver dentro dos limites em XZ E YZ
                    combined_mask = mask_xz & mask_yz
                    
                    for idx, is_clean in enumerate(combined_mask):
                        if is_clean:
                            cleaned_points.append(section_points[idx])
                    
                    removed = np.sum(~combined_mask)
                    removed_xz = np.sum(~mask_xz)
                    removed_yz = np.sum(~mask_yz)
                    outliers_removed += removed
                    step_removed_count += removed
                    
                    if removed > 0:
                        print(f"  {side} - Passo {step_idx+1} - Seção {section}: "
                              f"Removidos {removed} de {section_orig_count} pontos")
                        print(f"    Parâmetros XZ: {params['xz']}, YZ: {params['yz']}")
                        print(f"    Detectados em XZ: {removed_xz}, em YZ: {removed_yz}, final: {removed}")
                
                cleaned_data["steps"][step_idx]["points"] = cleaned_points
                cleaned_data["steps"][step_idx]["point_count"] = len(cleaned_points)
                total_points_cleaned += len(cleaned_points)
                
                if step_removed_count > 0:
                    step_orig_count = step["point_count"]
                    print(f"  Passo {step_idx+1}: Total removido: {step_removed_count} de {step_orig_count} pontos "
                          f"({step_removed_count/step_orig_count*100:.1f}%)")
            
            # Salva o arquivo JSON limpo
            with open(cleaned_file_path, 'w') as f:
                json.dump(cleaned_data, f, indent=2)
            
            cleaned_files[side] = cleaned_file_path
            
            if outliers_removed > 0:
                print(f"\nLimpeza específica por seção concluída para {side}:")
                print(f"  Total de pontos originais: {total_points_original}")
                print(f"  Total de pontos após limpeza: {total_points_cleaned}")
                print(f"  Outliers removidos: {outliers_removed} ({outliers_removed/total_points_original*100:.1f}%)")
            else:
                print(f"\n{side}: Nenhum outlier detectado.")
        
        except Exception as e:
            print(f"Erro ao limpar outliers para {side}: {str(e)}")
            error_count += 1
            #traceback.print_exc()  # Mostra detalhes do erro para depuração
    
    print("\nProcesso de limpeza de outliers específico por seção concluído!")
    print(f"Arquivos limpos criados: {len(cleaned_files)}")
    print(f"Total de erros encontrados: {error_count}")
    
    return cleaned_files


# Exemplo de uso da limpeza iterativa
def clean_outliers_multiple_passes(steps_files, iterations=2):
    """
    clean_outliers_multiple_passes / (function)
    What it does:
    Example function for running multiple passes of outlier cleaning with predefined IQR parameters for each iteration. Returns the cleaned file paths after all passes.
    """
    # Configuração de parâmetros para cada iteração
    params = [
        # Primeira iteração - Remove outliers mais grosseiros
        {
            "bottom": {"xz": (1.2, 1.2), "yz": (1.2, 1.2)},
            "wall": {"xz": (1.2, 1.2), "yz": (1.2, 1.2)},
            "default": {"xz": (1.5, 1.5), "yz": (1.5, 1.5)}
        },
        # Segunda iteração - Refinamento mais detalhado
        {
            "bottom": {"xz": (1.2, 1.2), "yz": (1.2, 1.2)},
            "wall": {"xz": (1.2, 1.2), "yz": (1.2, 1.2)},
            "default": {"xz": (1.5, 1.5), "yz": (1.5, 1.5)}
        },
        # Terceira iteração - Refinamento mais detalhado
        {
            "bottom": {"xz": (1.2, 1.2), "yz": (1.2, 1.2)},
            "wall": {"xz": (1.2, 1.2), "yz": (1.2, 1.2)},
            "default": {"xz": (1.5, 1.5), "yz": (1.5, 1.5)}
        }
    ]
    
    # Adiciona parâmetros adicionais se necessário
    while len(params) < iterations:
        params.append(params[-1])
    
    return run_iterative_outlier_cleaning(steps_files, iterations, params)





def main():
    """
    main / (function)
    What it does:
    Main execution function. Runs the full pipeline: combines files, calculates averages, detects steps, cleans outliers, and prints summary information. Results are saved in the postprocess directory.
    """
    start_time = time.time()

    print("=== Processamento de Dados Experimentais ===")

    # Etapa 1: Combinar arquivos bottom e wall com marcadores
    side_files = combine_bottom_wall_files()

    # Etapa 2: Calcular médias para cada lado (mantendo marcadores)
    side_average_files = calculate_average_for_sides(side_files)

    # Etapa 3: Detectar passos (antes da limpeza de outliers)
    steps_files = detect_steps(side_average_files)

    # Etapa 4: Limpar outliers
    cleaned_files = clean_outliers_multiple_passes(steps_files, iterations=3)

    # Etapa 5: Criar planos a partir dos arquivos processados
    #planes = create_planes_from_processed_files()

    end_time = time.time()
    print(f"\nProcessamento concluído em {end_time - start_time:.2f} segundos!")
    print("Verifique a pasta Sample_postprocess para os resultados.")

if __name__ == "__main__":
    main()