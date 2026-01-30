# -*- coding: utf-8 -*-
# _set_polygon.py

from mixin_logger import LoggerMixin

class PolygonDrawer(LoggerMixin):

    def draw(self, sketch, points):
        """
        _draw_polygon / (method)
        What it does:
        Draws a closed polygon in the Abaqus sketch using the provided list of points.
        """
        for i in range(len(points)):
            next_i = (i + 1) % len(points)
            sketch.Line(
                point1 = points[i], 
                point2 = points[next_i])