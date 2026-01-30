# -*- coding: utf-8 -*-
"""
Interpola tensões a partir de tabelas de distância vs tensão.
"""

from dataclasses import dataclass
from typing import List
import numpy as np


@dataclass
class StressPoint:
    """Ponto da curva distância-tensão."""
    d_um: float
    sigma_MPa: float


class StressTable:
    """Armazena e valida uma tabela de tensões."""
    
    def __init__(self, data: List[dict]):
        self.points = [StressPoint(**p) for p in data]
        self._validate()
    
    def _validate(self):
        """Valida que distâncias são monotônicas."""
        distances = [p.d_um for p in self.points]
        if distances != sorted(distances):
            raise ValueError("Distâncias devem estar em ordem crescente")
    
    def get_arrays(self):
        """Retorna arrays numpy de (distâncias, tensões)."""
        d = np.array([p.d_um for p in self.points])
        s = np.array([p.sigma_MPa for p in self.points])
        return d, s


class CoordinateMapper:
    """Mapeia coordenada X para distância d_um."""
    
    def __init__(self, x_min: float, x_max: float, d_max: float):
        self.x_min = x_min
        self.x_max = x_max
        self.d_max = d_max
        self.length = x_max - x_min
    
    def x_to_distance(self, x: float) -> float:
        """Converte coordenada X para distância d_um."""
        if x < self.x_min or x > self.x_max:
            raise ValueError(f"X={x} fora do range [{self.x_min}, {self.x_max}]")
        
        normalized = (x - self.x_min) / self.length
        return normalized * self.d_max


class StressInterpolator:
    """Interpola tensão a partir de coordenada X."""
    
    def __init__(self, table: StressTable, mapper: CoordinateMapper):
        self.table = table
        self.mapper = mapper
        self.d_array, self.s_array = table.get_arrays()
    
    def interpolate(self, x: float) -> float:
        """
        Interpola tensão para coordenada X.
        
        Args:
            x: Coordenada X do elemento/nó
            
        Returns:
            Tensão interpolada em MPa
        """
        d = self.mapper.x_to_distance(x)
        sigma = np.interp(d, self.d_array, self.s_array)
        return float(sigma)
    
    def interpolate_batch(self, x_values: List[float]) -> List[float]:
        """Interpola múltiplas coordenadas."""
        return [self.interpolate(x) for x in x_values]


if __name__ == '__main__':
    # Tabela amigo1
    amigo1_data = [
        {"d_um": 5,  "sigma_MPa": 0},
        {"d_um": 5,  "sigma_MPa": 0},
        {"d_um": 52, "sigma_MPa": 0},
        {"d_um": 58, "sigma_MPa": 0},
    ]
    
    # Tabela amigo2
    amigo2_data = [
        {"d_um": 5,  "sigma_MPa": 0},
        {"d_um": 5,  "sigma_MPa": 0},
        {"d_um": 50, "sigma_MPa": 0},
        {"d_um": 50, "sigma_MPa": 0},
    ]
    
    # Configuração Região 1: x ∈ [0, 0.08], d_max = 58 μm
    table1  = StressTable(amigo1_data)
    mapper1 = CoordinateMapper(x_min=0.0, x_max=0.08, d_max=58.0)
    interp1 = StressInterpolator(table1, mapper1)
    
    # Configuração Região 2: x ∈ [0.08, 3.92], d_max = 50 μm
    table2 = StressTable(amigo2_data)
    mapper2 = CoordinateMapper(x_min=0.08, x_max=3.92, d_max=50.0)
    interp2 = StressInterpolator(table2, mapper2)
    
    # Teste
    x_test = 0.04  # meio da região 1
    sigma = interp1.interpolate(x_test)
    print(f"X={x_test:.3f} → d={mapper1.x_to_distance(x_test):.2f}μm → σ={sigma:.2f}MPa")
    
    # Batch
    x_vals = [0.01, 0.04, 0.07]
    sigmas = interp1.interpolate_batch(x_vals)
    for x, s in zip(x_vals, sigmas):
        print(f"X={x:.3f} → σ={s:.2f}MPa")