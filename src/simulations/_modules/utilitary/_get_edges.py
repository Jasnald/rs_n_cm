# -*- coding: utf-8 -*-

class EdgeSetCreator:
    """
    Cria sets de arestas (edges) usando bounding box para filtrar.
    """
    LN = 1000000
    DV = 1e-6
    
    def __init__(self):
        #self.t_part = t_part
        pass
    def set(self, name=None, 
            xMin=-LN, yMin=-LN, zMin=-LN, 
            xMax=LN, yMax=LN, zMax=LN):
        """
        Cria um set de arestas baseado em bounding box.
        """
        DV = self.DV
        if name is None:
            raise ValueError("Erro: Nome do set não pode ser None.")
        
        # Lista para índices de arestas dentro do bounding box
        edge_indices = []
        
        # Itera sobre todas as arestas da peça
        for i, edge in enumerate(self.t_part.edges):
            try:
                # Obtém os vértices da aresta
                vertices = edge.getVertices()
                
                # Verifica se algum vértice está dentro do bounding box
                for vertex_id in vertices:
                    coords = edge.pointOn[0]
                    
                    if (xMin + DV <= coords[0] <= xMax - DV and
                        yMin + DV <= coords[1] <= yMax - DV and
                        zMin + DV <= coords[2] <= zMax - DV):
                        edge_indices.append(i)
                        break
                        
            except Exception as e:
                continue
        print("xMin={}, yMin={}, zMin={}," \
            "xMax={}, yMax={}, zMax={}".format(
            xMin, yMin, zMin, xMax, yMax, zMax))
        if not edge_indices:
            print("Aviso: Nenhuma aresta encontrada para o set '{}'.".format(name))
            return
        
        # Cria a sequência de arestas usando os índices
        selected_edges = self.t_part.edges[edge_indices[0]:edge_indices[0]+1]
        for idx in edge_indices[1:]:
            selected_edges += self.t_part.edges[idx:idx+1]
        
        # Cria o Set
        self.t_part.Set(edges=selected_edges, name=name)
        
        print("Set '{}' criado com {} aresta(s).".format(name, len(edge_indices)))

    def get(self, name):
        if name in self.t_part.sets:
            return self.t_part.sets[name].edges
        else:
            raise KeyError("Erro: Set '{}' não encontrado na peça.".format(name))