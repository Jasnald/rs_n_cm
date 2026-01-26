#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Choosed_plot_curve.py
Visualiza, em 3-D interativo (Plotly), todas as superfícies
reconstruídas a partir de curvas 1-D
(arquivos *_Rebuild_from_curve.json).

Cada subplot mostra:
  • a superfície z = f(x) (constante em y)
  • os pontos de medição originais

O HTML gerado fica em Sample_postprocess/Choosed_plane.
"""

import os
import glob
import math
import json
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from set_dir import _set_dir
current_dir, root_dir = _set_dir()

# ---------------------------------------------------------------
# Caminhos / utils já existentes no seu projecto
from plane_data_utils import (
    load_plane_data_from_json,
    extract_points_from_plane_data
)

def evaluate_curve(params: np.ndarray, x: float) -> float:
    return np.polynomial.polynomial.polyval(x, params)

# ---------------------------------------------------------------
def build_grid_and_eval(params, degree, x_min, x_max,
                        y_min, y_max, steps_x=60, steps_y=60):
    """cria mesh regular e avalia z = f(x) (ignora y)."""
    gx = np.linspace(x_min, x_max, steps_x)
    gy = np.linspace(y_min, y_max, steps_y)
    X, Y = np.meshgrid(gx, gy)
    Z = np.zeros_like(X, dtype=float)
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            Z[i, j] = evaluate_curve(np.array(params), X[i, j])
    return X, Y, Z

# ---------------------------------------------------------------
def get_curve_plane_files(plane_dir):
    """
    Retorna lista de arquivos com method_name == 'Rebuild_from_curve'
    ou nome terminando em '_Rebuild_from_curve.json'
    """
    cand = glob.glob(os.path.join(plane_dir, "*_Rebuild_from_curve.json"))
    res = []
    for fp in cand:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                d = json.load(f)
            if d.get("method_name", "").lower() == "rebuild_from_curve":
                res.append(fp)
        except Exception:
            continue
    return sorted(res)

# ---------------------------------------------------------------
def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    plane_dir = os.path.join(base_dir, "Sample_postprocess", "Choosed_plane")

    files = get_curve_plane_files(plane_dir)
    if not files:
        print("Nenhum *Rebuild_from_curve.json encontrado em", plane_dir)
        return

    n = len(files)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    fig = make_subplots(
        rows=rows, cols=cols,
        specs=[[{'type': 'scene'} for _ in range(cols)] for _ in range(rows)],
        horizontal_spacing=0.03,
        vertical_spacing=0.05,
        subplot_titles=[os.path.basename(f).replace("_Rebuild_from_curve.json", "")
                        for f in files]
    )

    for idx, fpath in enumerate(files):
        data = load_plane_data_from_json(fpath)
        if not data:
            print("Falha ao ler", fpath)
            continue

        params = data.get("parameters", [])
        degree = data.get("degree", 0)

        Xo, Yo, Zo, _, _ = extract_points_from_plane_data(data)
        if Xo.size == 0:
            print("Sem pontos em", fpath)
            continue

        Xg, Yg, Zg = build_grid_and_eval(
            params, degree,
            Xo.min(), Xo.max(), Yo.min(), Yo.max()
        )

        surf = go.Surface(
            x=Xg, y=Yg, z=Zg, colorscale='Spectral',
            showscale=False, opacity=0.8
        )
        scat = go.Scatter3d(
            x=Xo, y=Yo, z=Zo,
            mode='markers', marker=dict(size=3, color='black'),
            name='Measured'
        )

        r = idx // cols + 1
        c = idx % cols + 1
        fig.add_trace(surf,   row=r, col=c)
        fig.add_trace(scat,   row=r, col=c)

        scene_id = 'scene' if idx == 0 else f'scene{idx+1}'
        fig.update_layout({
            scene_id: dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z'
            )
        })

    fig.update_layout(
        title="Rebuild-from-Curve – Interactive 3-D Surfaces",
        width=1920*0.9, height=1080*0.85,
        margin=dict(l=10, r=10, t=50, b=10)
    )

    html_out = os.path.join(plane_dir, "3D_curves_visualization.html")
    fig.write_html(html_out)
    print("HTML salvo em", html_out)

# ---------------------------------------------------------------
if __name__ == "__main__":
    main()