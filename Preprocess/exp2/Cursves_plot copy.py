#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_curve_fit_hardcoded.py
Script simples que carrega pontos e polinômio de fit cujos caminhos
estão definidos diretamente nas constantes abaixo, e desenha um gráfico
com scatter dos pontos (x,z) e as curvas ajustadas.
"""
import json
import numpy as np
import matplotlib.pyplot as plt

Sample_number = 1
deg = 2

# ————————————————————————————————————————————————————————————————
# AJUSTE AQUI OS CAMINHOS DOS TEUS ARQUIVOS JSON
# ————————————————————————————————————————————————————————————————
POINTS_JSON     = fr"T:\02_SHK\05_dgl_gm\08_Project\Modules_Post_ED2\Sample_postprocess\Sample_{Sample_number}\Sample{Sample_number}_Modified.json"
CURVE_JSON      = fr"T:\02_SHK\05_dgl_gm\08_Project\Modules_Post_ED2\Sample_postprocess\Curves\Sample{Sample_number}_Curve_deg{deg}.json"
#CURVE_JSON      = fr"T:\02_SHK\05_dgl_gm\08_Project\Modules_Post_ED2\Sample_postprocess\Curves\Sample{Sample_number}_Curve_config{deg}.json"
CHOOSED_JSON    = fr"T:\02_SHK\05_dgl_gm\08_Project\Modules_Post_ED2\Sample_postprocess\Choosed_curve\Sample{Sample_number}_Subtraction.json"

#CHOOSED_JSON    = fr"T:\02_SHK\05_dgl_gm\08_Project\Modules_Post_ED2\Sample_postprocess\Choosed_curve\Sample{Sample_number}_Rotated.json"
# ————————————————————————————————————————————————————————————————

def load_points(json_path):
    """Lê o JSON de pontos e retorna 2 arrays numpy: xs, zs."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    xs, zs = [], []
    for p in data.get("points", []):
        # tenta usar 'z'; se não existir, cai em 'y'
        if "x" in p and "y" in p:
            xs.append(float(p["x"]))
            zs.append(float(p["y"]))
        elif "x" in p and "z" in p:
            xs.append(float(p["x"]))
            zs.append(float(p["z"]))
    return np.array(xs), np.array(zs)

def load_curve(json_path):
    """Lê o JSON com o fit polinomial e retorna (params, degree, rmse, eq_str)."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    params = np.array(data["params"], dtype=float)
    degree = data.get("degree", None)
    # rmse pode estar como 'rmse' ou, no summary, 'best_rmse'
    rmse   = data.get("rmse", data.get("best_rmse", None))
    eq_str = data.get("equation", None)
    return params, degree, rmse, eq_str

def polyval(params, x):
    """Avalia polinômio (coef. a0..an) para array x."""
    return np.polynomial.polynomial.polyval(x, params)

def main():
    # 1) Carrega dados
    xs, zs = load_points(POINTS_JSON)
    if xs.size == 0:
        print(f"Nenhum ponto encontrado em {POINTS_JSON}")
        return
    
    # Carrega as duas curvas
    params_curve, degree_curve, rmse_curve, eq_str_curve = load_curve(CURVE_JSON)
    params_choosed, degree_choosed, rmse_choosed, eq_str_choosed = load_curve(CHOOSED_JSON)
    
    # 2) Prepara curvas de fit num grid de x
    x_min, x_max = xs.min(), xs.max()
    x_fit = np.linspace(0, 40, 500)
    z_fit_curve = polyval(params_curve, x_fit)
    z_fit_choosed = polyval(params_choosed, x_fit)
    
    # 3) Plota
    plt.figure(figsize=(10, 6))
    
    # Pontos originais
    plt.scatter(xs, zs, color='black', s=20, label='Dados originais', zorder=5)
    
    # Curva original
    plt.plot(x_fit, z_fit_curve, color='red', linewidth=2, 
             label=f'Fit original (grau={degree_curve})', linestyle='-')
    
    # Curva escolhida/subtraída
    plt.plot(x_fit, z_fit_choosed, color='blue', linewidth=2, 
             label=f'Curva escolhida (grau={degree_choosed})', linestyle='--')
    
    plt.xlabel("x")
    plt.ylabel("z")
    
    # Título com informações das duas curvas
    title = "Comparação de Fits Polinomiais"
    if rmse_curve is not None and rmse_choosed is not None:
        title += f"\nRMSE original={rmse_curve:.4g}, RMSE escolhida={rmse_choosed:.4g}"
    elif rmse_curve is not None:
        title += f"\nRMSE original={rmse_curve:.4g}"
    elif rmse_choosed is not None:
        title += f"\nRMSE escolhida={rmse_choosed:.4g}"
    
    plt.title(title)
    
    # Desenha equações, se houver
    text_y_pos = 0.98
    if eq_str_curve:
        plt.text(0.02, text_y_pos, f"Original: {eq_str_curve}",
                 ha='left', va='top', transform=plt.gca().transAxes,
                 fontsize=8, bbox=dict(boxstyle="round,pad=0.3",
                                       facecolor="lightcoral", alpha=0.7))
        text_y_pos -= 0.08
    
    if eq_str_choosed:
        plt.text(0.02, text_y_pos, f"Escolhida: {eq_str_choosed}",
                 ha='left', va='top', transform=plt.gca().transAxes,
                 fontsize=8, bbox=dict(boxstyle="round,pad=0.3",
                                       facecolor="lightblue", alpha=0.7))
    
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()