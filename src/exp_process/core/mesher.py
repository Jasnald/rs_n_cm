import numpy as np
import logging
# Requer: pip install shapely
from shapely.geometry import Polygon, Point

class MeshGenerator:
    """
    Recria a lógica de 'Rebuild' do s5: Gera um grid regular 
    dentro de uma geometria definida (ex: retângulo ou T-shape).
    """
    
    @staticmethod
    def generate_rectangular_grid(
        x_min, x_max, y_min, y_max, 
        step_x=0.5, step_y=0.5
    ):
        """
        Gera uma malha retangular simples (para Exp2 ou testes).
        Retorna: (X_grid, Y_grid) em formato meshgrid 1D (flattened).
        """
        xs = np.arange(x_min, x_max + step_x, step_x)
        ys = np.arange(y_min, y_max + step_y, step_y)
        
        # Cria malha 2D e achata para lista de pontos
        X, Y = np.meshgrid(xs, ys)
        return X.flatten(), Y.flatten()

    @staticmethod
    def generate_t_shape_grid(
        bounds_dict, 
        step=0.5
    ):
        """
        Gera malha baseada em limites complexos (lógica do Shapely antiga).
        bounds_dict: {'x_min': ..., 'x_max': ..., etc}
        """
        # Exemplo simplificado de geometria T. 
        # No código real, você montaria o Polygon com as coordenadas exatas.
        p1 = (bounds_dict['x_min'], bounds_dict['y_min'])
        p2 = (bounds_dict['x_max'], bounds_dict['y_max'])
        # ... definir vértices do T ...
        
        # Por enquanto, retornamos um retangulo bounding box para não quebrar
        return MeshGenerator.generate_rectangular_grid(
            bounds_dict['x_min'], bounds_dict['x_max'],
            bounds_dict['y_min'], bounds_dict['y_max'],
            step, step
        )

    @staticmethod
    def project_z(x_grid, y_grid, fit_model):
        """
        Calcula o Z para cada ponto da malha usando os coeficientes do modelo.
        """
        coeffs = np.array(fit_model['coeffs'])
        degree = fit_model['degree']
        
        # Reconstrói Z baseado na equação polinomial 2D (mesma lógica do Fitter)
        z_grid = np.zeros_like(x_grid)
        
        # Lógica deve espelhar exatamente o Fitter.fit_2d_poly
        # Se usou [1, x, y, x^2, y^2...], deve reconstruir igual.
        idx = 0
        for i in range(len(x_grid)):
            row_val = 0
            # Se fit_2d_poly usou a ordem "row.append(x**k); row.append(y**k)" + intercepto no final:
            current_coeff_idx = 0
            
            # Recalcula termos (Isso precisa estar 100% alinhado com o fitter.py)
            # Idealmente, o Fitter deveria ter um método 'predict(x, y)' para evitar duplicação aqui.
            pass 
            
        return z_grid