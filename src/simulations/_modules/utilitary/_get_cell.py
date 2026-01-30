# -*- coding: utf-8 -*-

class CellSetCreator:
    """
    Cria sets de células (cells) usando bounding box para filtrar.
    """
    LN = 1000000
    DV = 1e-6

    def __init__(self):
        pass

    def set(self, name=None,
            xMin=-LN, yMin=-LN, zMin=-LN,
            xMax=LN, yMax=LN, zMax=LN):
        """
        Cria um set de células baseado em bounding box.
        """
        DV = self.DV
        if name is None:
            raise ValueError("Erro: Nome do set não pode ser None.")

        # Lista para índices de células dentro do bounding box
        cell_indices = []

        # Itera sobre todas as células da peça
        for i, cell in enumerate(self.t_part.cells):
            try:
                # Obtém as coordenadas do centroide da célula
                coords = cell.pointOn[0]

                if (xMin + DV <= coords[0] <= xMax - DV and
                    yMin + DV <= coords[1] <= yMax - DV and
                    zMin + DV <= coords[2] <= zMax - DV):
                    cell_indices.append(i)
                    #break

            except Exception as e:
                continue

        print("xMin={}, yMin={}, zMin={}," \
              "xMax={}, yMax={}, zMax={}".format(
            xMin, yMin, zMin, xMax, yMax, zMax))

        if not cell_indices:
            print("Aviso: Nenhuma célula encontrada para o set '{}'.".format(name))
            return

        # Cria a sequência de células usando os índices
        selected_cells = self.t_part.cells[cell_indices[0]:cell_indices[0] + 1]
        for idx in cell_indices[1:]:
            selected_cells += self.t_part.cells[idx:idx + 1]

        # Cria o Set
        self.t_part.Set(cells=selected_cells, name=name)

        print("Set '{}' criado com {} célula(s).".format(name, len(cell_indices)))

    def get(self, name):
        if name in self.t_part.sets:
            return self.t_part.sets[name].cells
        else:
            raise KeyError("Erro: Set '{}' não encontrado na peça.".format(name))