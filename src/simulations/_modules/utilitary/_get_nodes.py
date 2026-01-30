# -*- coding: utf-8 -*-

class NodeSetCreator:
    """
    Cria sets de nós (nodes) usando bounding box para filtrar.
    """
    LN = 1000000
    DV = 1e-6

    def __init__(self):
        pass

    def set(self, name=None,
            xMin=-LN, yMin=-LN, zMin=-LN,
            xMax=LN, yMax=LN, zMax=LN):
        """
        Cria um set de nós baseado em bounding box.
        """
        DV = self.DV
        if name is None:
            raise ValueError("Erro: Nome do set não pode ser None.")

        # Lista para índices de nós dentro do bounding box
        node_indices = []

        # Itera sobre todos os nós da peça
        for i, node in enumerate(self.t_part.nodes):
            try:
                # Obtém as coordenadas do nó
                coords = node.coordinates

                # Verifica se o nó está dentro do bounding box
                if (xMin - DV <= coords[0] <= xMax + DV and
                    yMin - DV <= coords[1] <= yMax + DV and
                    zMin - DV <= coords[2] <= zMax + DV):
                    node_indices.append(i)

            except Exception as e:
                continue

        print("xMin={}, yMin={}, zMin={}, " \
              "xMax={}, yMax={}, zMax={}".format(
            xMin, yMin, zMin, xMax, yMax, zMax))

        if not node_indices:
            print("Aviso: Nenhum nó encontrado para o set '{}'.".format(name))
            return

        # Cria a sequência de nós usando os índices
        selected_nodes = self.t_part.nodes[node_indices[0]:node_indices[0] + 1]
        for idx in node_indices[1:]:
            selected_nodes += self.t_part.nodes[idx:idx + 1]

        # Cria o Set
        self.t_part.Set(nodes=selected_nodes, name=name)

        print("Set '{}' criado com {} nó(s).".format(
            name, len(node_indices)))

    def get(self, name):
        """
        Retorna os nós de um set existente.
        """
        if name in self.t_part.sets:
            return self.t_part.sets[name].nodes
        else:
            raise KeyError("Erro: Set '{}' não encontrado na peça.".format(name))