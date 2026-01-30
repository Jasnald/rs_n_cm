# -*- coding: utf-8 -*-
"""
Leitor de parâmetros JSON compatível com Python 2.7 e 3.x
"""

import json
import os
import sys


class JsonReader:
    """Lê parâmetros de configuração de arquivo JSON."""
    
    def __init__(self, json_path):
        """
        Args:
            json_path (str): Caminho para o arquivo JSON
        """
        self.json_path = json_path
        self._data = None
    
    def load(self):
        """Carrega dados do JSON."""
        if not os.path.exists(self.json_path):
            raise IOError("Arquivo JSON não encontrado: {}".format(self.json_path))
        
        with open(self.json_path, 'r') as f:
            self._data = json.load(f)
        
        return self._data
   
   
    def get_table(self, table_name):
        """
        Retorna dados de uma tabela específica.
        
        Args:
            table_name (str): Nome da tabela ('amigo1' ou 'amigo2')
            
        Returns:
            list: Lista de dicionários com d_um e sigma_MPa
        """
        if self._data is None:
            self.load()
        
        tables = self._data.get('tables', {})
        return tables.get(table_name, [])
    
    def get_all_tables(self):
        """Retorna todas as tabelas."""
        if self._data is None:
            self.load()
        
        return self._data.get('tables', {})
    
    def get(self, key, default=None):
        """Acesso genérico a qualquer chave."""
        if self._data is None:
            self.load()
        
        return self._data.get(key, default)


if __name__ == '__main__':
    # Exemplo de uso
    json_path = 'config.json'
    
    reader = JsonReader(json_path)
    
    # Opção 1: Carregar tudo
    data = reader.load()
    print("Comprimento: {}".format(data['analysis']['comprimento']))
    
    # Opção 2: Acessar partes específicas
    analysis = reader.get_analysis_params()
    print("Mesh size: {}".format(analysis.get('mesh_size')))
    
    geometry = reader.get_geometry_params()
    print("cord1: {}".format(geometry.get('cord1')))
    
    # Opção 3: Tabelas
    amigo1 = reader.get_table('amigo1')
    print("Amigo1 tem {} pontos".format(len(amigo1)))
    
    for point in amigo1[:3]:
        print("  d_um={}, sigma={}".format(point['d_um'], point['sigma_MPa']))