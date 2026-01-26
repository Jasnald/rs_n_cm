#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# plot_curves_and_points_per_sample.py
#
# Cria UMA figure por Sample<n> contendo:
#   • curva ajustada (grau 4)
#   • pontos Y-Z originais
#
# cada figure aparece numa janela própria; se preferir salvar
# em PNG basta descomentar o bloco “fig.savefig(...)”.

import os, re, glob, json
import numpy as np
import matplotlib.pyplot as plt

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
POST_DIR   = os.path.join(BASE_DIR, "Sample_postprocess")
CURVES_DIR = os.path.join(POST_DIR, "Curves")

def y_from_params(params, x):
    return sum(a * x**i for i, a in enumerate(params))

def find_raw_json(sample):
    folder = os.path.join(POST_DIR, sample.replace("Sample", "Sample_"))

    p = os.path.join(folder, f"{sample}_Modified.json")
    if os.path.isfile(p):
        return p

    iters = glob.glob(os.path.join(folder, f"{sample}_Iter*.json"))
    if iters:
        p = max(iters, key=lambda s: int(re.search(r"_Iter(\d+)", s).group(1)))
        return p

    p = os.path.join(folder, f"{sample}_Average.json")
    return p if os.path.isfile(p) else None

# -------------------------------------------------------------------------
xs = np.linspace(-0.03, 0.005, 300)     # eixo Y (independente)

for fp in glob.glob(os.path.join(CURVES_DIR, "*deg2.json")):
    # carrega curva (grau 4)
    with open(fp) as f:
        curve = json.load(f)

    params = curve["params"]
    sample = curve.get("sample") or os.path.basename(fp).split("_Curve_")[0]

    # carrega pontos originais
    raw_json = find_raw_json(sample)
    if not raw_json:
        print(f"[AVISO] pontos não encontrados para {sample}")
        continue
    with open(raw_json) as f:
        raw = json.load(f)

    y_pts = [p["x"] for p in raw["points"]]
    z_pts = [p["y"] for p in raw["points"]]

    # ---------------------------------------------------------------------
    # FIGURE PRÓPRIA PARA ESTA SAMPLE
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.set_title(f"{sample}  –  Fit grau 4 vs. pontos brutos")

    # curva ajustada
    zs = [y_from_params(params, x) for x in xs]
    ax.plot(xs, zs, 'r-', lw=2, label="fit grau 4")

    # pontos originais
    ax.scatter(y_pts, z_pts, s=14, alpha=.7, label=f"{len(y_pts)} pontos")

    ax.set_xlabel("Y")
    ax.set_ylabel("Z")
    ax.grid(True, ls="--", alpha=.4)
    ax.legend()
    fig.tight_layout()

    # se quiser gravar num arquivo:
    # out_png = os.path.join(CURVES_DIR, f"{sample}_curve.png")
    # fig.savefig(out_png, dpi=150)

# mostra todas as janelas depois do loop
plt.show()