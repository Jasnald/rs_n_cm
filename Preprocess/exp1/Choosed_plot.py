
"""
Choosed_plot.py
What it does:
This script provides interactive 3D visualization of fitted planes and their original measurement points using Plotly. It loads plane data from JSON files, reconstructs the fitted surface on a regular grid, and displays both the surface and the original points for visual comparison. The script is designed to help users analyze the quality of polynomial or Chebyshev plane fits and compare different surfaces side by side.

Example of use:
    Run this script directly to generate an HTML file with interactive 3D plots for the specified plane data in the 'Sample_postprocess/Choosed_plane' directory.

    python Choosed_plot.py
"""
# plane_plotly_3d.py

import os
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Import functions for loading and processing
from plane_data_utils import load_plane_data_from_json, extract_points_from_plane_data
from s3_Plane_process import calculate_z_polynomial, calculate_z_chebyshev


def generate_plane_plot_data(plane_json_file: str, steps: int = 160):
    """
    generate_plane_plot_data / (function)
    What it does:
    Loads the plane data from the JSON file, computes a regular grid for the fitted surface using the appropriate method (polynomial or Chebyshev), and returns the grid arrays (X, Y, Z), the original measurement points, and a descriptive title.
    """
    plane_data = load_plane_data_from_json(plane_json_file)
    print("Loaded:", plane_data.keys())
    if not plane_data:
        print(f"Could not load file {plane_json_file}")
        return None

    # Plane metadata
    side = plane_data.get('side', 'UnknownSide')
    degree = plane_data.get('degree', 0)
    method = plane_data.get('method_name', 'unknown').lower()
    params = plane_data.get('parameters', [])
    norm_params = plane_data.get('normalization_parameters', None)

    # Extract the original points to define grid limits
    X_orig, Y_orig, Z_orig, _, _ = extract_points_from_plane_data(plane_data)
    if X_orig.size == 0:
        print(f"No points available in {plane_json_file}")
        return None

    # Define grid limits based on the original points
    x_min, x_max = X_orig.min(), X_orig.max()
    y_min, y_max = Y_orig.min(), Y_orig.max()

    # Create a regular grid for X and Y
    grid_x = np.linspace(x_min, x_max, steps)
    grid_y = np.linspace(y_min, y_max, steps)
    X_grid, Y_grid = np.meshgrid(grid_x, grid_y)

    # Initialize the grid Z matrix
    Z_grid = np.zeros_like(X_grid, dtype=float)

    # Fill Z_grid using the chosen method
    for i in range(X_grid.shape[0]):
        for j in range(X_grid.shape[1]):
            x_val = X_grid[i, j]
            y_val = Y_grid[i, j]
            if method == 'chebyshev' and norm_params is not None:
                Z_grid[i, j] = calculate_z_chebyshev(np.array(params), x_val, y_val, degree, norm_params)
            else:
                Z_grid[i, j] = calculate_z_polynomial(np.array(params), x_val, y_val, degree)

    title = f"3D Surface - {side} ({method.capitalize()}, degree={degree})"
    return {'X_grid': X_grid, 'Y_grid': Y_grid, 'Z_grid': Z_grid, 
            'X_orig': X_orig, 'Y_orig': Y_orig, 'Z_orig': Z_orig, 'title': title }


def main():
    """
    main / (function)
    What it does:
    Main execution function. Loads multiple plane data files, generates 3D surface and scatter plots for each, and arranges them in a grid of interactive Plotly subplots. Saves the visualization as an HTML file for further analysis.
    """
    # Defina os caminhos para os arquivos JSON
    base_dir = os.path.dirname(os.path.abspath(__file__))
    plane_dir = os.path.join(base_dir, "Sample_postprocess", "Choosed_plane")
    plane_file1 = os.path.join(plane_dir, "Side1__6_subtraction.json")
    plane_file2 = os.path.join(plane_dir, "Side2__6_subtraction.json")
    plane_file3 = os.path.join(plane_dir, "Final_Average__6_average_subtraction.json")
    plane_file4 = os.path.join(plane_dir, "Avearege__6_rebuild.json")

    # Lista com os arquivos e títulos para exibição
    files_titles = [
        (plane_file1, "Plane 1"),
        (plane_file2, "Plane 2"),
        (plane_file3, "Final Average"),
        (plane_file4, "Rebuild for abaqus")
    ]

    import math
    nfiles = len(files_titles)
    cols = math.ceil(math.sqrt(nfiles))
    rows = math.ceil(nfiles / cols)

    # Criação do layout dos subplots (todos do tipo 'scene' para 3D)
    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[[{'type': 'scene'}, {'type': 'scene'}],
            [{'type': 'scene'}, {'type': 'scene'}]],
        horizontal_spacing=0.02,  # diminui o espaço horizontal
        vertical_spacing=0.04,    # diminui o espaço vertical
        subplot_titles=[title for (_, title) in files_titles]
    )

    # Itera sobre os arquivos, posicionado-os na grade (row, col)
    for idx, (file_path, default_title) in enumerate(files_titles):
        row_idx = idx // cols + 1
        col_idx = idx % cols + 1

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        data = generate_plane_plot_data(file_path, steps=100)
        if data is None:
            continue

        X_grid, Y_grid, Z_grid = data['X_grid'], data['Y_grid'], data['Z_grid']
        X_orig, Y_orig, Z_orig = data['X_orig'], data['Y_orig'], data['Z_orig']

        # Criação dos objetos de trace: superfície e pontos originais
        surface = go.Surface(
            x=X_grid, y=Y_grid, z=Z_grid, colorscale='Spectral',
            opacity=0.8, showscale=False, name="Surface"
        )
        scatter = go.Scatter3d(
            x=X_orig, y=Y_orig, z=Z_orig, mode='markers',
            marker=dict(size=3, color='black'), opacity=0.5,
            name='Original Points'
        )

        # Adiciona os traços à cena correspondente
        fig.add_trace(surface, row=row_idx, col=col_idx)
        fig.add_trace(scatter, row=row_idx, col=col_idx)

        # Atualiza os eixos da cena correspondente
        # A Plotly nomeia as cenas como 'scene', 'scene2', 'scene3', ... de forma sequencial
        scene_id = 'scene' if idx == 0 else f'scene{idx+1}'
        fig.update_layout({
            scene_id: dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z'
            )
        })

    # Ajusta o layout geral do gráfico
    fig.update_layout(
        title="Interactive 3D Surfaces Visualization with Plotly",
        width=1920*0.8,
        height=1080*0.8,
        margin=dict(l=10, r=10, t=50, b=10) 
    )
    output_file = os.path.join(plane_dir, "3D_planes_visualization.html")
    #fig.show()
    fig.write_html(output_file)
    print(f"Visualization saved to {output_file}")


if __name__ == "__main__":
    main()