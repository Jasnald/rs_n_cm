# -*- coding: utf-8 -*-
"""
plane_plot_utils.py
What it does:
This module provides utility functions for visualizing reconstructed planes and T-shaped regions using Matplotlib. It includes tools for creating boolean masks and patches for T-shapes, and for plotting fitted plane surfaces (polynomial or Chebyshev) with optional masking and overlays of original points.

Example of use:
    from plane_plot_utils import plot_plane_reconstruction_on_ax
    fig, ax = plt.subplots()
    plot_plane_reconstruction_on_ax(ax, plane_data, use_t_shape=True)
    plt.show()
"""
import numpy as np
import matplotlib.pyplot as plt

# Importe as funções necessárias do seu projeto
from exp1.s3_Plane_process import calculate_z_polynomial, calculate_z_chebyshev
from plane_data_utils import extract_points_from_plane_data
# Caso deseje usar a forma T.
from Exp_Data.s1_exp.sample_dim import Mean_dim_wp
from Exp_Data.s1_exp.mean_dim import DimOne



def create_t_shape_mask(X_grid, Y_grid, t_dims):
    """
    create_t_shape_mask / (function)
    What it does:
    Creates a boolean mask for points inside a T-shaped region, based on the provided grid and T dimensions.
    """
    X_flat = X_grid.flatten()
    Y_flat = Y_grid.flatten()

    # Barra horizontal
    h_xmin, h_xmax = 0, t_dims['h_width']
    h_ymin, h_ymax = 0, t_dims['h_thickness']

    # Barra vertical
    v_pos_x = t_dims['h_width'] - t_dims['offset_1'] - t_dims['offset_2']
    v_xmin, v_xmax = v_pos_x, v_pos_x + t_dims['v_width']
    v_ymin, v_ymax = t_dims['h_thickness'], t_dims['h_thickness'] + t_dims['v_height']

    h_mask = (X_flat >= h_xmin) & (X_flat <= h_xmax) \
             & (Y_flat >= h_ymin) & (Y_flat <= h_ymax)

    v_mask = (X_flat >= v_xmin) & (X_flat <= v_xmax) \
             & (Y_flat >= v_ymin) & (Y_flat <= v_ymax)

    t_mask = h_mask | v_mask
    return t_mask.reshape(X_grid.shape)

def create_t_shape_patches(t_dims):
    """
    create_t_shape_patches / (function)
    What it does:
    Returns Matplotlib rectangle patches for drawing the T-shaped region, based on the provided T dimensions.
    """
    import matplotlib.patches as patches
    edge_color = 'black'
    # Barra horizontal
    horizontal_bar = patches.Rectangle(
        (0, 0),
        t_dims['h_width'],
        t_dims['h_thickness'],
        fill=False, edgecolor=edge_color, linewidth=.2, linestyle=':'
    )
    # Barra vertical
    v_pos_x = t_dims['h_width'] - t_dims['offset_1'] - t_dims['offset_2']
    vertical_bar = patches.Rectangle(
        (v_pos_x, t_dims['h_thickness']),
        t_dims['v_width'],
        t_dims['v_height'],
        fill=False, edgecolor=edge_color, linewidth=.2, linestyle=':'
    )
    return horizontal_bar, vertical_bar

def plot_plane_reconstruction_on_ax(
    ax, plane_data, z_min=0.0, z_max=0.02, xy_margin=0.05,
    use_t_shape=False
):
    """
    plot_plane_reconstruction_on_ax / (function)
    What it does:
    Plots the reconstructed plane surface on the given Matplotlib axis using parameters from the plane data JSON. Optionally applies a T-shape mask and overlays the T contour. Also plots original points colored by fitted Z value.
    """
    # Extração de dados
    X, Y, Z_orig, Z_fit, residuals = extract_points_from_plane_data(plane_data)
    side = plane_data.get('side', 'UnknownSide')
    degree = plane_data.get('degree', 0)
    method = plane_data.get('method_name', 'UnknownMethod')
    parameters = plane_data.get('parameters', [])
    norm_params = plane_data.get('normalization_parameters', None)

    if X.size == 0:
        ax.text(0.5, 0.5, "Sem pontos para {} ({}, grau={}).".format(
            side, method, degree),
                ha='center', va='center')
        return

    if not parameters:
        ax.text(0.5, 0.5, "Parâmetros para reconstrução não encontrados",
                ha='center', va='center')
        return

    # Definição de limites + grade
    x_min, x_max = X.min(), X.max()
    y_min, y_max = Y.min(), Y.max()

    x_range = x_max - x_min
    y_range = y_max - y_min
    x_min -= xy_margin * x_range
    x_max += xy_margin * x_range
    y_min -= xy_margin * y_range
    y_max += xy_margin * y_range

    grid_size = 160
    X_grid, Y_grid = np.meshgrid(
        np.linspace(x_min, x_max, grid_size),
        np.linspace(y_min, y_max, grid_size)
    )

    Z_grid = np.zeros_like(X_grid)
    params = np.array(parameters)

    # Calcula Z em cada ponto da grade
    for i in range(grid_size):
        for j in range(grid_size):
            if method.lower() == 'chebyshev' and norm_params:
                Z_grid[i, j] = calculate_z_chebyshev(
                    params, X_grid[i, j], Y_grid[i, j], degree, norm_params
                )
            else:
                Z_grid[i, j] = calculate_z_polynomial(
                    params, X_grid[i, j], Y_grid[i, j], degree
                )

    # Clipa para visualização
    Z_clipped = np.clip(Z_grid, z_min, z_max)

    # Se quiser aplicar a forma T
    if use_t_shape:
        t_dims = DimOne()
        t_mask = create_t_shape_mask(X_grid, Y_grid, t_dims)
        Z_masked = np.where(t_mask, Z_clipped, np.nan)
        cont = ax.contourf(X_grid, Y_grid, Z_masked, levels=50, cmap='Spectral', 
                           alpha=0.8, vmin=z_min, vmax=z_max)
        # Desenha patches do T
        h_patch, v_patch = create_t_shape_patches(t_dims)
        ax.add_patch(h_patch)
        ax.add_patch(v_patch)
    else:
        # Caso não queira usar a forma T
        cont = ax.contourf(X_grid, Y_grid, Z_clipped, levels=50, cmap='Spectral', 
                           alpha=0.8, vmin=z_min, vmax=z_max)

    # Pontos originais sobre a superfície
    Z_fit_clipped = np.clip(Z_fit, z_min, z_max)
    ax.scatter(X, Y, c=Z_fit_clipped, cmap='jet', s=1,
               vmin=z_min, vmax=z_max)

    ax.set_title('{} ({}, grau={}) - Plano reconstruído'.format(
        side, method, degree))
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.grid(True)

    # (Opcional) retornar o handle do contour, caso queira usar colorbar
    return cont