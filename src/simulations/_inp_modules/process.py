# _inp_modules/process.py
from .imports import *
from .dataclasses import *
from .reader import INPReader
from .parser import INPParser


class SectionReader:
    """Lê seções e mapeia propriedades."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.elset_props_map: Dict[str, SectionProperties] = {}
        self.element_props_map: Dict[int, SectionProperties] = {}
        self.lines = INPReader(self.filepath).read()

    def parse(self):
        print("\n--- INICIO LEITURA DE SEÇÕES ---")
        self._read_sections()
        self._map_elements_to_props()
        print(f"--- FIM LEITURA: {len(self.element_props_map)} elementos mapeados ---\n")
        return self.element_props_map

    def _read_sections(self):
        lines = self.lines
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith('**'): continue

            is_shell = INPParser.is_header(line, '*shell section')
            is_solid = INPParser.is_header(line, '*solid section')

            if is_shell or is_solid:
                elset_name = INPParser.get_parameter(line, 'elset')
                if not elset_name: continue

                thick, pts = 0.0, 1
                if is_shell:
                    # Tenta ler próxima linha de dados
                    if i + 1 < len(lines) and not lines[i + 1].strip().startswith('*'):
                        data = lines[i + 1].strip().split(',')
                        try:
                            thick = float(data[0])
                            pts = int(data[1]) if len(data) > 1 else 5
                        except ValueError:
                            pass

                self.elset_props_map[elset_name.upper()] = SectionProperties(
                    name=elset_name, is_shell=is_shell, thickness=thick, num_int_pts=pts
                )

    def _map_elements_to_props(self):
        target_elsets = set(self.elset_props_map.keys())
        current_prop = None
        in_target_elset = False
        is_generate = False

        for line in self.lines:
            line = line.strip()
            if not line or line.startswith('**'): continue

            if line.startswith('*'):
                in_target_elset = False
                current_prop = None

                if INPParser.is_header(line, '*elset'):
                    elset_name = INPParser.get_parameter(line, 'elset')
                    if elset_name.upper() in target_elsets:
                        in_target_elset = True
                        current_prop = self.elset_props_map[elset_name.upper()]
                        is_generate = 'generate' in line.lower()
                continue

            if in_target_elset and current_prop:
                parts = line.split(',')
                try:
                    if is_generate:
                        start, end = int(parts[0]), int(parts[1])
                        step = int(parts[2]) if len(parts) > 2 else 1
                        for eid in range(start, end + 1, step):
                            self.element_props_map[eid] = current_prop
                    else:
                        for p in parts:
                            if p.strip(): self.element_props_map[int(p)] = current_prop
                except (ValueError, IndexError):
                    pass


class ReadEntities:
    """Lê nós e elementos do arquivo .inp."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.lines = INPReader(self.filepath).read()

    def read_nodes(self) -> List[Node]:
        nodes = []
        in_node_section = False

        for line in self.lines:
            line = line.strip()
            if not line or line.startswith('**'): continue

            if line.startswith('*'):
                in_node_section = INPParser.is_header(line, '*node')
                continue

            if in_node_section:
                parts = line.split(',')
                if len(parts) >= 4:
                    try:
                        nodes.append(Node(
                            int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])))
                    except ValueError:
                        pass
        return nodes

    def read_elements(self) -> List[Element]:
        elements = []
        current_type = 'UNKNOWN'
        in_element_section = False

        for line in self.lines:
            line = line.strip()
            if not line or line.startswith('**'): continue

            if line.startswith('*'):
                if INPParser.is_header(line, '*element'):
                    in_element_section = True
                    current_type = INPParser.get_parameter(line, 'type').upper() or 'UNKNOWN'
                else:
                    in_element_section = False
                continue

            if in_element_section:
                parts = line.split(',')
                if len(parts) >= 2:
                    try:
                        label = int(parts[0])
                        # [CORREÇÃO CLAUDE]: Loop explícito try/except é mais seguro que isdigit()
                        node_ids = []
                        for n in parts[1:]:
                            try:
                                node_ids.append(int(n))
                            except ValueError:
                                pass  # Ignora lixo ou espaços vazios

                        if node_ids:
                            elements.append(Element(label, node_ids, current_type))
                    except ValueError:
                        pass

        return elements

    def read_nset(self, nset_name: str) -> List[int]:
        node_ids = []
        in_nset = False
        target_name = nset_name.upper()

        for line in self.lines:
            if line.startswith('*'):
                # Check if entering the correct Nset
                if INPParser.is_header(line, '*nset'):
                    current_name = INPParser.get_parameter(line, 'nset').upper()
                    in_nset = (current_name == target_name)
                else:
                    in_nset = False
                continue

            if in_nset:
                # Extract IDs handling commas and newlines
                parts = line.split(',')
                for p in parts:
                    if p.strip().isdigit():
                        node_ids.append(int(p))
        return node_ids

class RegionFilter:
    """Filtra elementos por caixa delimitadora (X e Y) e TIPO."""

    @staticmethod
    def filter_by_box(elements: List[Element], nodes: List[Node],
                      x_min: float, x_max: float,
                      y_min: float, y_max: float,
                      target_type: str = None) -> List[Element]:

        node_map = {n.label: n for n in nodes}
        filtered = []

        for elem in elements:
            # 1. Filtro de Tipo (se solicitado)
            if target_type is not None:
                # Se o elemento lido for 'UNKNOWN', mantemos por segurança ou descartamos?
                # Geralmente melhor descartar se não bate com o pedido.
                if elem.elem_type != 'UNKNOWN':
                    if target_type.upper() not in elem.elem_type:
                        continue

            # 2. Filtro Geométrico
            valid_nodes = [node_map[nl] for nl in elem.nodes if nl in node_map]

            if valid_nodes:
                cx = sum(n.x for n in valid_nodes) / len(valid_nodes)
                cy = sum(n.y for n in valid_nodes) / len(valid_nodes)

                if (x_min <= cx <= x_max) and (y_min <= cy <= y_max):
                    filtered.append(elem)

        return filtered


class RegionElementExtractor:
    """Orquestra a extração."""

    def __init__(self, inp_path: str):
        self.reader = ReadEntities(inp_path)
        self.filter = RegionFilter()
        self._nodes = None
        self._elements = None

    def extract(self, x_min: float, x_max: float,
                y_min: float = -float('inf'), y_max: float = float('inf'),
                target_type: str = None) -> List[Element]:

        if self._nodes is None: self._nodes = self.reader.read_nodes()
        if self._elements is None: self._elements = self.reader.read_elements()

        return self.filter.filter_by_box(
            self._elements, self._nodes, x_min, x_max, y_min, y_max, target_type)