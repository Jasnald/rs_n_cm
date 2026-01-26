#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
s3_Curve_process.py

Itera graus 1..N em cada Sample<n>, ajusta polinômios
z = a0 + a1*x + ... + an*x^n  (opção Ridge + normalização)
e grava JSON por grau + resumo.
"""

import os
import re
import glob
import json
import logging
from typing import List, Tuple, Dict

import numpy as np

# ------------------------------------------------------------------ #
# CONFIGURAÇÃO GERAL                                                 #
# ------------------------------------------------------------------ #
MAX_DEGREE   = 7          # grau máximo a testar
NORMALIZE_X  = True       # re-escala x para [-1,1] antes de ajustar?
RIDGE_ALPHA  = 1        # 0 → LS clássico   ;   >0 → Ridge

# ------------------------------------------------------------------ #
# LOG                                                                #
# ------------------------------------------------------------------ #
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s",
                    datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# BUSCA DE ARQUIVOS                                                  #
# ------------------------------------------------------------------ #
def find_latest_curve_files(post_dir: str) -> Dict[str, str]:
    """
    Para cada pasta Sample_<n> escolhe:
      1) *_Modified.json
      2) *_IterN.json    (maior N)
      3) *_Average.json
    """
    patt_sample = re.compile(r"Sample_(\d+)$")
    samples = {}
    for folder in os.listdir(post_dir):
        full = os.path.join(post_dir, folder)
        if not os.path.isdir(full):
            continue
        m = patt_sample.match(folder)
        if not m:
            continue
        num = m.group(1)
        name = f"Sample{num}"
        alljs = glob.glob(os.path.join(full, f"{name}*.json"))

        # 1) modified
        mods = [p for p in alljs if p.endswith("_Modified.json")]
        if mods:
            samples[name] = mods[0]
            continue

        # 2) iterações
        iters = []
        for p in alljs:
            m2 = re.search(r"_Iter(\d+)\.json$", p)
            if m2:
                iters.append((int(m2.group(1)), p))
        if iters:
            samples[name] = max(iters, key=lambda x: x[0])[1]
            continue

        # 3) average
        avg = os.path.join(full, f"{name}_Average.json")
        if os.path.isfile(avg):
            samples[name] = avg
    return samples

# ------------------------------------------------------------------ #
# I/O DE PONTOS                                                      #
# ------------------------------------------------------------------ #
def load_xy_points(json_path: str) -> List[Tuple[float, float]]:
    """Carrega [(x, y), ...] do JSON."""
    with open(json_path, "r") as f:
        data = json.load(f)
    pts = data.get("points", [])
    return [(float(p["x"]), float(p["y"]))         # x = indep., y = dep.
            for p in pts if "x" in p and "y" in p]

# ------------------------------------------------------------------ #
# AJUSTE DE POLINÔMIO (LS ou Ridge)                                  #
# ------------------------------------------------------------------ #
def _compose_linear_substitution(coef_t: np.ndarray,
                                 a: float, b: float) -> np.ndarray:
    """
    Recebe coeficientes em t          (p(t))
    devolve coeficientes em x onde t = a*x + b  (p(a x + b))
    """
    out = np.zeros(1)
    linear = np.array([b, a])              # (b + a*x)
    for c in coef_t[::-1]:                 # Horner
        out = np.polynomial.polynomial.polymul(out, linear)
        out[0] += c
    return out


def _vandermonde(x: np.ndarray, degree: int) -> np.ndarray:
    """X = [1, x, x², ...]  (colunas em ordem crescente)."""
    return np.column_stack([x ** k for k in range(degree + 1)])


def fit_polynomial_1d(points: List[Tuple[float, float]],
                      degree: int,
                      alpha: float = 0.0,
                      normalize: bool = True) -> np.ndarray:
    """
    Ajusta polinômio 1-D.
      alpha = 0       → mínimos quadrados clássico
      alpha > 0       → Ridge (λ = alpha)
      normalize=True  → re-escala x → [-1,1] antes de ajustar
    Retorna coeficientes a0..an na variável x original!
    """

    x = np.asarray([p[0] for p in points], dtype=float)
    y = np.asarray([p[1] for p in points], dtype=float)

    # 1) opcional: normalização para [-1,1]
    if normalize:
        xmin, xmax = float(x.min()), float(x.max())
        if xmax == xmin:                       # proteção
            raise ValueError("Todos os x são iguais!")
        a_lin = 2.0 / (xmax - xmin)
        b_lin = -(xmax + xmin) / (xmax - xmin)
        x_scaled = a_lin * x + b_lin           # agora ∈ [-1,1]
    else:
        x_scaled = x
        a_lin, b_lin = 1.0, 0.0                # identidade

    # 2) monta a matriz de termos
    X = _vandermonde(x_scaled, degree)         # shape (n, deg+1)

    # 3) resolve LS ou Ridge
    if alpha == 0.0:
        coef_scaled, *_ = np.linalg.lstsq(X, y, rcond=None)
    else:
        # (XᵀX + λI) c = Xᵀy
        xtx = X.T @ X
        xtx.flat[::degree + 2] += alpha        # adiciona λ à diagonal
        coef_scaled = np.linalg.solve(xtx, X.T @ y)

    # 4) se normalizou, converte p(t)  →  p(a x + b)
    if normalize:
        coef = _compose_linear_substitution(coef_scaled, a_lin, b_lin)
    else:
        coef = coef_scaled

    return coef


# ------------------------------------------------------------------ #
# MÉTRICAS                                                           #
# ------------------------------------------------------------------ #
def evaluate_fit(points: List[Tuple[float, float]],
                 params: np.ndarray) -> Tuple[float, float, float]:
    x = np.asarray([p[0] for p in points], dtype=float)
    y = np.asarray([p[1] for p in points], dtype=float)
    y_hat = np.polynomial.polynomial.polyval(x, params)
    residuals = y - y_hat
    mse = float(np.mean(residuals ** 2))
    rmse = float(np.sqrt(mse))
    max_err = float(np.max(np.abs(residuals)))
    return mse, rmse, max_err


def build_equation_string(params: np.ndarray) -> str:
    terms = []
    for j, a in enumerate(params):
        if j == 0:
            terms.append(f"{a:.6f}")
        else:
            sign = "+" if a >= 0 else "-"
            terms.append(f" {sign} {abs(a):.6f}*x^{j}")
    return "z = " + "".join(terms)

# ------------------------------------------------------------------ #
# ROTINA PRINCIPAL DE EXPERIMENTO                                    #
# ------------------------------------------------------------------ #
def experiment_curves(post_dir: str,
                      max_degree: int = 5,
                      normalize: bool = True,
                      alpha: float = 0.0) -> dict:
    """
    Ajusta graus 1..max_degree em cada amostra.
    Salva:
      - Sample<n>_Curve_deg<d>.json
      - Sample<n>_Curve_Summary.json
    """
    samples = find_latest_curve_files(post_dir)
    if not samples:
        logger.warning("Nenhuma curva para processar em " + post_dir)
        return {}

    curves_dir = os.path.join(post_dir, "Curves")
    os.makedirs(curves_dir, exist_ok=True)

    all_results = {}
    for sample, path in sorted(samples.items()):
        logger.info(f"\n-- Processando {sample} ({os.path.basename(path)})")
        points = load_xy_points(path)
        if len(points) < 2:
            logger.warning(f"  Poucos pontos ({len(points)}). Pulando.")
            continue

        best_rmse = float("inf")
        best_deg  = None
        results   = {}

        for deg in range(1, max_degree + 1):
            try:
                params = fit_polynomial_1d(points, deg,
                                           alpha=alpha,
                                           normalize=normalize)
            except Exception as e:
                logger.warning(f"  Grau {deg}: erro no ajuste -> {e}")
                continue

            mse, rmse, max_err = evaluate_fit(points, params)
            eq_str = build_equation_string(params)

            results[deg] = {
                "params": params.tolist(),
                "equation": eq_str,
                "mse": mse,
                "rmse": rmse,
                "max_error": max_err
            }
            logger.info(f"  Grau {deg}: RMSE = {rmse:.6f}")

            # salva JSON por grau
            out = {
                "sample": sample,
                "degree": deg,
                **results[deg]
            }
            fn = f"{sample}_Curve_deg{deg}.json"
            with open(os.path.join(curves_dir, fn), "w") as fw:
                json.dump(out, fw, indent=2)

            if rmse < best_rmse:
                best_rmse = rmse
                best_deg  = deg

        # summary
        summary = {
            "sample": sample,
            "best_degree": best_deg,
            "best_rmse": best_rmse,
            "results_by_degree": results
        }
        summary_path = os.path.join(curves_dir,
                                    f"{sample}_Curve_Summary.json")
        with open(summary_path, "w") as fs:
            json.dump(summary, fs, indent=2)

        all_results[sample] = summary

    return all_results

# ------------------------------------------------------------------ #
# MAIN                                                               #
# ------------------------------------------------------------------ #
def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    post_dir = os.path.join(base_dir, "Sample_postprocess")

    experiment_curves(post_dir,
                      max_degree=MAX_DEGREE,
                      normalize=NORMALIZE_X,
                      alpha=RIDGE_ALPHA)

    logger.info("Processamento de curvas concluído.")


if __name__ == "__main__":
    main()