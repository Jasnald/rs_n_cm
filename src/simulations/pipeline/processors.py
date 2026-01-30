# src/Simulations/_pipelines/processors.py

from .imports import *
from .config import SimulationConfig
from _inp_modules import *

from Preprocess.exp1.s3_Plane_process import calculate_z_polynomial



class ContourProcessor:
    def __init__(self, config: SimulationConfig):
        self.cfg = config

    @staticmethod
    def _extract_sample_id(filename: str) -> str:
        """
        Transforma 'Sample4__3.json' ou 'Sample4.json' em 'S4'.
        Usado para gerar o prefixo do arquivo de saída.
        """
        # Procura por "Sample" seguido de dígitos
        match = re.search(r'(?:Sample|S)(\d+)', filename, re.IGNORECASE)
        return f"S{match.group(1)}" if match else None

    def run_batch(self, json_pattern: str = "*.json", use_default_single_file: bool = False):

        json_files = []

        if use_default_single_file:
            # MODO 1: Único Arquivo (Definido no Config)
            default_file = self.cfg.polynomial_json_default
            print(f"\n--- Processando INPs (Modo: Arquivo Único Padrão) ---")

            if default_file and default_file.exists():
                json_files = [default_file]
                print(f"   Arquivo selecionado: {default_file.name}")
            else:
                print(f"ERRO: Arquivo padrão não encontrado ou não definido: {default_file}")
                return
        else:
            # MODO 2: Batch / Pasta Inteira
            print(f"\n--- Processando INPs (Modo: Batch na pasta, Filtro: '{json_pattern}') ---")
            if not self.cfg.polynomial_json_dir or not self.cfg.polynomial_json_dir.exists():
                print(f"ERRO: Diretório de JSONs não encontrado: {self.cfg.polynomial_json_dir}")
                return

            # Busca e filtra
            found = sorted(self.cfg.polynomial_json_dir.glob(json_pattern))
            json_files = [f for f in found if f.suffix.lower() == '.json']

            if not json_files:
                print(f"Nenhum JSON encontrado com o padrão '{json_pattern}'.")
                return

        # --- BUSCA DE INPS (Igual) ---
        inp_files = [f for f in self.cfg.cm_directory.rglob("*.inp") if not f.name.endswith('_FI.inp')]

        if not inp_files:
            print("Nenhum INP de malha encontrado.")
            return

        print(f"Processando {len(inp_files)} INPs com {len(json_files)} arquivos JSON.")

        # --- LOOP DE PROCESSAMENTO ---
        count = 0
        for inp_path in inp_files:
            print(f"\n> Base INP: {inp_path.name}")

            for json_path in json_files:
                # Se for arquivo único, podemos querer manter o nome original sem prefixo?
                # Geralmente é melhor manter o prefixo para evitar sobrescrever, mas se quiser 1:1 estrito:
                # if use_default_single_file: prefix = "" else: ...

                prefix = self._extract_sample_id(json_path.name)

                out_name = f"{prefix}_{inp_path.stem}_FI.inp"
                out_path = inp_path.parent / out_name

                print(f"   Aplicando {json_path.name[:35]}... -> {out_name}")

                try:
                    params, degree = JSONReader.read_parameters(str(json_path))
                    if params is None: continue

                    self._process_single(inp_path, out_path, params, degree)
                    count += 1
                except Exception as e:
                    print(f"      [ERRO] {e}")

        print(f"\n--- Fim: {count} arquivos gerados ---")

    def _process_single(self, inp_path, out_path, params, degree):
        # (Este method permanece IDÊNTICO ao anterior)
        reader = INPReader(str(inp_path))
        lines = reader.read()

        entity_reader = ReadEntities(str(inp_path))
        nodes = entity_reader.read_nodes()
        node_map = {n.label: (n.x, n.y, n.z) for n in nodes}

        disp_node_ids = entity_reader.read_nset(self.cfg.nset_disp_name)
        if not disp_node_ids:
            print(f"      [AVISO] Nset '{self.cfg.nset_disp_name}' vazio. Usando busca por Z=0.")
            disp_node_ids = [n_id for n_id, coords in node_map.items() if abs(coords[2]) < 1e-6]

        bc_lines = BCGenerator.generate(
            all_nodes=node_map, node_ids=disp_node_ids,
            calculate_z_func=calculate_z_polynomial,
            params=params, degree=degree,
            instance_name=self.cfg.instance_name
        )

        lines = INPInserter.insert_in_step(lines, self.cfg.step_name, bc_lines)

        new_mat = [
            "*Material, name=WORK_PIECE_MATERIAL\n",
            "*Elastic\n",
            f"{self.cfg.elastic_modulus}, {self.cfg.poisson_ratio}\n"
        ]
        lines = INPInserter.replace_material_block(lines, "WORK_PIECE_MATERIAL", new_mat)
        lines = INPInserter.fix_restart_frequency(lines)

        INPWriter(str(out_path)).write(lines)

class ResidualProcessor:
    """
    Aplica Tensões Residuais (Initial Conditions) nos arquivos INP.
    """

    def __init__(self, config: SimulationConfig, csv_filename="stress_input.txt"):
        self.cfg = config
        self.csv_filename = csv_filename

    def run_batch(self):
        print(f"\n--- Processando INPs (Residual Stresses) ---")
        base_dir = self.cfg.rea_directory

        # Procura INPs ignorando a pasta Output
        inp_files = [
            f for f in base_dir.rglob("*.inp")
            if not f.name.endswith('_FI.inp') and "Output" not in f.parts
        ]

        processed = 0
        for inp_path in inp_files:
            sim_name = inp_path.stem
            sim_dir = inp_path.parent

            # Localiza CSV (Lógica Fuzzy Lenth/Length)
            csv_path = self._find_csv(base_dir, sim_name)
            out_path = sim_dir / f"{sim_name}_FI.inp"

            print(f"Processando: {sim_name}")

            try:
                self._process_single(inp_path, csv_path, out_path)
                processed += 1
                print("  -> Sucesso.")
            except Exception as e:
                print(f"  -> ERRO: {e}")

        print(f"--- Fim: {processed} arquivos processados ---")

    def _find_csv(self, base_dir, sim_name):
        """Busca fuzzy melhorada com normalização"""

        # Normaliza: Lenth→Length, _→., Mesh-0_6→Mesh-0.6
        def normalize(s):
            return s.replace("Lenth", "Length").replace("_", ".")

        output_dir = base_dir / "Output"
        if not output_dir.exists():
            return None

        norm_sim = normalize(sim_name)

        for d in output_dir.iterdir():
            if d.is_dir():
                norm_cand = normalize(d.name)
                if norm_sim == norm_cand:  # Match exato primeiro
                    csv = d / self.csv_filename
                    if csv.exists():
                        return csv

        # Fallback: match parcial
        for d in output_dir.iterdir():
            if d.is_dir():
                norm_cand = normalize(d.name)
                if norm_sim in norm_cand or norm_cand in norm_sim:
                    csv = d / self.csv_filename
                    if csv.exists():
                        return csv
        return None

    def _process_single(self, inp_path, csv_path, out_path):
        stresses = StressReader.read(str(csv_path))
        print(f"     (Leu {len(stresses)} elementos com tensão)")

        reader = INPReader(str(inp_path))
        lines = reader.read()

        elset_lines = ElsetGenerator.generate(stresses, self.cfg.instance_name)
        stress_lines = InitialStressGenerator.generate(stresses)

        lines = INPInserter.insert_elsets(lines, elset_lines)
        lines = INPInserter.insert_initial_stresses(lines, stress_lines)

        new_mat = [
            "*Material, name=WORK_PIECE_MATERIAL\n",
            "*Elastic\n",
            f"{self.cfg.elastic_modulus}, {self.cfg.poisson_ratio}\n"
        ]
        lines = INPInserter.replace_material_block(lines, "WORK_PIECE_MATERIAL", new_mat)
        lines = INPInserter.fix_restart_frequency(lines)

        INPWriter(str(out_path)).write(lines)