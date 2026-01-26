from importations import *

from .fitter import Fitter
from .mesher import MeshGenerator

class Rebuilder:

    @staticmethod
    def rebuild_surface(model: dict, geometry_type: str, dims: dict, step=0.5):

        if geometry_type == 't_shape':
            x, y = MeshGenerator.t_shape_grid(dims, step)
        else:
            x, y = MeshGenerator.rectangular_grid(dims['width'], dims['height'], step)

        if len(x) == 0:
            raise ValueError("Grid gerado vazio (verifique dimensões).")

        z = Fitter.eval_2d_poly(x, y, model)

        cloud = np.column_stack((x, y, z))
        return cloud

    @staticmethod
    def rebuild_curve_extrusion(model_1d: dict, dims: dict, step_x=0.5, step_y=1.0):

        x_grid, y_grid = MeshGenerator.rectangular_grid(dims['width'], dims['height'], step_x)

        z_grid = Fitter.eval_1d_poly(x_grid, model_1d)

        return np.column_stack((x_grid, y_grid, z_grid))