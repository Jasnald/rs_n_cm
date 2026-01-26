import os
import json
import numpy as np
import re

def calc_average_and_save_json():
    """
    Lê 2d-Gerade1.txt de cada lado L/R, calcula a média e grava
    Sample<n>_Average.json em …/Sample_postprocess/Sample_<n>/
    
    Devolve um dicionário:
        { "Sample<n>": r"caminho\Sample<n>_Average.json", ... }
    """
    print("\n=== Passo 1: Calcular médias e gravar JSON ===")

    base_dir   = os.path.dirname(os.path.abspath(__file__))
    input_dir  = os.path.join(base_dir, "Sample_og", "Milling Samples")
    post_dir   = os.path.join(base_dir, "Sample_postprocess")

    os.makedirs(post_dir, exist_ok=True)

    # --- localizar pastas L / R ------------------------------------------------
    samples = {}                                     # {num: {"L":folder, "R":folder}}
    for folder in os.listdir(input_dir):
        m = re.match(r'(\d+)([LR])$', folder)        # “12L”  “12R”
        if m:
            num, side = m.groups()
            samples.setdefault(num, {})[side] = folder

    average_json_files = {}

    for num, sides in sorted(samples.items(), key=lambda x: int(x[0])):
        if "L" not in sides or "R" not in sides:
            print(f"  › Amostra {num}: faltando L ou R — ignorada")
            continue

        try:
            file_L = os.path.join(input_dir, sides["L"], "2d-Gerade1.txt")
            file_R = os.path.join(input_dir, sides["R"], "2d-Gerade1.txt")

            data_L = np.loadtxt(file_L)
            data_R = np.loadtxt(file_R)

            # usamos apenas as 3 primeiras colunas (x, y, z)
            if data_L.ndim == 2 and data_L.shape[1] > 3:
                data_L = data_L[:, :3]
            if data_R.ndim == 2 and data_R.shape[1] > 3:
                data_R = data_R[:, :3]

            # Garante tamanhos iguais
            min_len = min(len(data_L), len(data_R))

            # primeiros min_len pontos de L
            paired_L = data_L[:min_len]

            # últimos min_len pontos de R, mas em ordem invertida
            paired_R = data_R[::-1][:min_len]

            avg = (paired_L + paired_R) / 2.0

            # transforma em lista de dicionários [{x:…, y:…, z:…}, …]
            if avg.shape[1] == 3:
                points = [
                    {"x": float(x), "y": float(y), "z": float(z)}
                    for x, y, z in avg
                ]
            elif avg.shape[1] == 2:           # caso só tenha X-Y
                points = [
                    {"x": float(x), "y": float(y)}
                    for x, y in avg
                ]
            else:
                raise ValueError("Formato inesperado: %s colunas" % avg.shape[1])

            # salva JSON
            sample_folder = os.path.join(post_dir, f"Sample_{num}")
            os.makedirs(sample_folder, exist_ok=True)

            avg_json_path = os.path.join(sample_folder,
                                         f"Sample{num}_Average.json")
            with open(avg_json_path, "w") as f:
                json.dump({"points": points, "point_count": len(points)}, f, indent=2)

            average_json_files[f"Sample{num}"] = avg_json_path
            print(f"  › Amostra {num}: {len(points)} pontos → {avg_json_path}")

        except Exception as e:
            print(f"  ! Erro na amostra {num}: {e}")

    print("=== Médias concluídas ===")
    return average_json_files


def clean_iqr_one_file(json_in, json_out, iqr_factors):
    """
    Carrega json_in, remove outliers (IQR) e grava json_out.
    Devolve nº de pontos removidos.
    """
    with open(json_in) as f:
        data = json.load(f)

    pts = data["points"]
    if len(pts) <= 5:
        # Poucos pontos: copia directo
        with open(json_out, "w") as f:
            json.dump(data, f, indent=2)
        return 0

    # extrai arrays
    arr = {k: np.array([p[k] for p in pts]) for k in pts[0].keys()}

    mask = np.ones(len(pts), bool)

    for ax, factor in iqr_factors.items():
        if ax not in arr:
            continue
        q1, q3 = np.percentile(arr[ax], [25, 75])
        iqr = q3 - q1
        lo, hi = q1 - factor * iqr, q3 + factor * iqr
        mask &= (arr[ax] >= lo) & (arr[ax] <= hi)

    cleaned_pts = [p for p, keep in zip(pts, mask) if keep]
    removed = len(pts) - len(cleaned_pts)

    out_data = {"points": cleaned_pts,
                "point_count": len(cleaned_pts)}

    with open(json_out, "w") as f:
        json.dump(out_data, f, indent=2)

    return removed

def run_iterative_iqr(avg_json_files,
                      iterations=2,
                      iqr_params=None):
    """
    Executa ‘iterations’ limpezas IQR.
    Salva ficheiros “…_Iter1.json”, “…_Iter2.json”, …
    Devolve dicionário com o último ficheiro de cada amostra.
    """
    if iqr_params is None:
        iqr_params = [
            {"x": 1.3, "y": 1.3, "z": 1.3},   # iteração 1
            {"x": 1.0, "y": 1.0, "z": 1.0},   # iteração 2
        ]

    current_files = avg_json_files.copy()

    print("\n=== Passo 2: Limpeza IQR (iterativa) ===")
    for it in range(1, iterations + 1):
        print(f"\n··· Iteração {it}/{iterations}")
        next_files = {}

        for sample, in_path in current_files.items():
            sample_folder = os.path.dirname(in_path)
            out_path = os.path.join(sample_folder,
                                    f"{sample}_Iter{it}.json")
            params = iqr_params[it-1] if it - 1 < len(iqr_params) else iqr_params[-1]
            removed = clean_iqr_one_file(in_path, out_path, params)
            next_files[sample] = out_path

            msg = "nenhum" if removed == 0 else f"{removed}"
            print(f"  › {sample}: removidos {msg} pontos")

        current_files = next_files

    print("\n=== Limpeza concluída ===")
    return current_files

def main():
    iqr_params_per_iteration=[
            {"x": 1.5, "y": 1.5, "z": 1.5},
            {"x": 1.0, "y": 1.0, "z": 1.0},
            {"x": 0.9, "y": 0.9, "z": 0.9},
        ]

    avg_json = calc_average_and_save_json()
    final_files = run_iterative_iqr(avg_json, iterations=1,
                                    iqr_params=iqr_params_per_iteration)
    print(f"\nArquivos finais gerados: {len(final_files)}")
    return final_files

if __name__ == "__main__":
    main()