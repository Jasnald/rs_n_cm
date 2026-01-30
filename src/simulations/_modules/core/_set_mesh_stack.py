# -*- coding: utf-8 -*-
# _set_mesh_stack.py

from ..utilitary import *
from ..imports import *


class MeshSetterStack(LoggerMixin):
    def __init__(self):
        pass

    def set(self, cell_set_name, direction):
        if cell_set_name not in self.t_part.sets:
            print("ERRO: Set '{}' not found!.".format(cell_set_name))
            return

        region_cells = self.t_part.sets[cell_set_name].cells
        target_normal = direction
        tolerance = 1e-2
        candidates = []

        def dot_product(v1, v2):
            return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]

        for face in self.t_part.faces:

            face_center = face.pointOn[0]  # Coordenada aproximada
            face_normal = face.getNormal(face_center)
            dot_normal = dot_product(face_normal, target_normal)

            if dot_normal > (1.0 - tolerance):
                pos_score = dot_product(face_center, target_normal)
                candidates.append((face, pos_score))


        if not candidates:
            print("ERRO: Any face was found in this direction: {}.".format(target_normal))
            return

        best_face, max_score = max(candidates, key=lambda item: item[1])

        print("Choosed face (Score {:.2f}). Apliyng...".format(max_score))

        self.t_part.assignStackDirection(
            cells           = region_cells,
            referenceRegion = best_face
        )

        print("Stack Direction aliened with the vetor {}.".format(direction))

"""
from abaqus journual
#self.part#.assignStackDirection(
    cells           = #self.part#.cells.getSequenceFromMask(
    ('[#1ff ]', ), ), 
    referenceRegion = #self.part#.faces[37])
"""
