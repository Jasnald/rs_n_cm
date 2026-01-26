import numpy as np
from .fitter import Fitter
from .mesher import MeshGenerator

class Rebuilder:
    """Gera o 'produto final' para exportação (Abaqus/Cloud)."""

    @staticmethod
    def rebuild_surface(model: dict, geometry_type: str, dims: dict, step=0.5):
        """
        Reconstrói superfície 3D (Exp1).
        geometry_type: 'rect' ou 't_shape'
        """
        # 1. Gerar Grid (X, Y)
        if geometry_type == 't_shape':
            x, y = MeshGenerator.t_shape_grid(dims, step)
        else:
            x, y = MeshGenerator.rectangular_grid(dims['width'], dims['height'], step)

        if len(x) == 0:
            raise ValueError("Grid gerado vazio (verifique dimensões).")

        # 2. Calcular Z usando o modelo
        # (Requer que Fitter tenha eval_2d_poly implementado conforme discutido)
        z = Fitter.eval_2d_poly(x, y, model)

        # 3. Formatar saída (Nx3)
        cloud = np.column_stack((x, y, z))
        return cloud

    @staticmethod
    def rebuild_curve_extrusion(model_1d: dict, dims: dict, step_x=0.5, step_y=1.0):
        """
        Reconstrói curva 1D extrudada em superfície (Exp2).
        dims: {width, height}
        """
        # 1. Grid Retangular
        x_grid, y_grid = MeshGenerator.rectangular_grid(dims['width'], dims['height'], step_x)
        
        # 2. Avalia Z apenas baseado em X (Extrusão)
        z_grid = Fitter.eval_1d_poly(x_grid, model_1d)
        
        # 3. Retorna nuvem 3D
        return np.column_stack((x_grid, y_grid, z_grid))