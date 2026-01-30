# -*- coding: utf-8 -*-
"""
Main: Orquestra extração de elementos, interpolação de tensões e escrita do INP.
"""
from Simulations._inp_modules   import *
from .interpolator    import StressTable, CoordinateMapper, StressInterpolator
from typing import List, Set, Dict, Any

# Pequena classe de configuração (pode ficar aqui ou em dataclasses)
class RegionConfig:
    def __init__(self, x_min, x_max, table_data, d_max,
                 y_min=-float('inf'), y_max=float('inf'), elem_type=None):
        self.x_min, self.x_max = x_min, x_max
        self.y_min, self.y_max = y_min, y_max
        self.table_data = table_data
        self.d_max = d_max
        self.elem_type = elem_type

class StressCalculator:

    def __init__(self, inp_path: str):
        # Reutiliza as ferramentas existentes no próprio módulo
        self.extractor = RegionElementExtractor(inp_path)
        self.section_reader = SectionReader(inp_path)
        self.props_map = self.section_reader.parse()

        # Carrega nós para cálculo de centróide
        self._nodes_map = {n.label: n for n in self.extractor.reader.read_nodes()}

    def _get_centroid_x(self, element: Element) -> float:
        xs = [self._nodes_map[nid].x for nid in element.nodes if nid in self._nodes_map]
        return sum(xs) / len(xs) if xs else 0.0

    def calculate_all_regions(self, regions: List[RegionConfig]) -> Dict[int, Any]:
        """Itera sobre uma lista de regiões e consolida os resultados."""
        all_stresses = {}
        for i, config in enumerate(regions):
            print(f"  > Processando região {i + 1}...")
            # Chama o método singular que já existe
            stresses = self.calculate_region(config)
            all_stresses.update(stresses)
        return all_stresses

    def calculate_region(self, config) -> Dict[int, Any]:
        """
        config: Objeto RegionConfig (pode vir do script principal)
        """
        # Cria a tabela matemática baseada nos dados da config
        table = StressTable(config.table_data)

        elements = self.extractor.extract(
            x_min=config.x_min, x_max=config.x_max,
            y_min=config.y_min, y_max=config.y_max,
            target_type=config.elem_type
        )

        result = {}

        for elem in elements:
            props = self.props_map.get(elem.label)
            if not props:
                # Opcional: Logar aviso ou pular
                print(f"Aviso: Elemento {elem.label} sem propriedades de seção.")
                continue

            # 1. Caso SÓLIDO
            if not props.is_shell:
                cx = self._get_centroid_x(elem)
                mapper = CoordinateMapper(config.x_min, config.x_max, config.d_max)
                interp = StressInterpolator(table, mapper)
                try:
                    val = interp.interpolate(cx)
                    result[elem.label] = val
                except ValueError:
                    result[elem.label] = 0.0

            # 2. Caso SHELL (Interpolação através da espessura)
            else:
                # Mapper local: de 0 até a espessura da seção
                mapper_local = CoordinateMapper(0.0, props.thickness, config.d_max)
                interp_local = StressInterpolator(table, mapper_local)

                stresses_through_thickness = []
                # Define pontos de integração (simplificado para exemplo)
                num_pts = props.num_int_pts
                if num_pts > 1:
                    depths = [props.thickness * i / (num_pts - 1) for i in range(num_pts)]
                else:
                    depths = [props.thickness / 2.0]

                for d in depths:
                    try:
                        val = interp_local.interpolate(d)
                        stresses_through_thickness.append(val)
                    except ValueError:
                        stresses_through_thickness.append(0.0)

                result[elem.label] = stresses_through_thickness

        return result
