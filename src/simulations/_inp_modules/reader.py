#!/usr/bin/env python
# -*- coding: utf-8 -*-

#reader.py

from .imports import *

class INPReader:
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)

    def read(self) -> List[str]:
        with open(self.filepath, "r", encoding="utf-8") as f:
            return f.readlines()

class JSONReader:
    """Lê parâmetros do arquivo .json."""
    @staticmethod
    def read_parameters(json_path: str):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Retorna tupla (array numpy, grau) para compatibilidade
            params = np.array(data['parameters'])
            degree = data['degree']
            return params, degree
        except Exception as e:
            print(f"Erro ao ler JSON: {e}")
            return None, None


class StressReader:
    """Lê dados de tensão de arquivos .txt ou .csv separados por vírgula."""

    @staticmethod
    def read(file_path: str) -> Dict[int, List[float]]:
        stresses = {}
        path = Path(file_path)

        if not path.exists():
            print(f"AVISO: Arquivo de tensão não encontrado: {path}")
            return stresses

        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=',')

            for row in reader:
                if not row or row[0].strip().startswith('#'):
                    continue

                try:
                    elem_id = int(row[0])
                    vals = [float(x) for x in row[1:7]]
                    stresses[elem_id] = vals
                except (ValueError, IndexError):
                    pass

        return stresses