from importations import *


class MeshGenerator:

    @staticmethod
    def rectangular_grid(width: float, height: float, step: float) -> tuple:

        x = np.arange(0, width + step, step)
        y = np.arange(0, height + step, step)
        X, Y = np.meshgrid(x, y)
        return X.flatten(), Y.flatten()

    @staticmethod
    def t_shape_grid(dims: dict, step: float) -> tuple:

        h_poly = Polygon([
            (0, 0), (dims['h_width'], 0),
            (dims['h_width'], dims['h_thickness']), (0, dims['h_thickness'])
        ])

        v_x_start = dims.get('offset_1', (dims['h_width'] - dims['v_width'])/2)
        v_poly = Polygon([
            (v_x_start, dims['h_thickness']),
            (v_x_start + dims['v_width'], dims['h_thickness']),
            (v_x_start + dims['v_width'], dims['h_thickness'] + dims['v_height']),
            (v_x_start, dims['h_thickness'] + dims['v_height'])
        ])

        t_shape = h_poly.union(v_poly)

        min_x, min_y, max_x, max_y = t_shape.bounds
        x_range = np.arange(min_x, max_x + step, step)
        y_range = np.arange(min_y, max_y + step, step)
        
        valid_points = []
        for x in x_range:
            for y in y_range:
                if t_shape.contains(Point(x, y)):
                    valid_points.append((x, y))
                    
        if not valid_points:
            return np.array([]), np.array([])
            
        pts = np.array(valid_points)
        return pts[:, 0], pts[:, 1]