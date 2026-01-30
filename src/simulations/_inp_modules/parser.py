# _inp_modules/parser.py

from .imports import *

class INPParser:
    @staticmethod
    def get_parameter(line: str, key: str) -> str:
        """
        Extrai valor de chave=valor. Ex: 'elset=Set-1' -> 'Set-1'.
        Robustez: lida com espaços ' key = val ' e case-insensitive na chave.
        """
        parts = line.split(',')
        key_lower = key.lower()
        for p in parts:
            if '=' in p:
                k, v = p.split('=', 1)
                if k.strip().lower() == key_lower:
                    return v.strip()
        return ""

    @staticmethod
    def is_header(line: str, keyword: str) -> bool:
        """
        Verifica se linha começa com a keyword (ex: *Element).
        Case-insensitive e assume que comentários já foram filtrados ou não atrapalham.
        """
        return line.lower().startswith(keyword.lower())