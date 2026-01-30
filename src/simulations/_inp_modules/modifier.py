# -*- coding: utf-8 -*-

from .imports import *
from .reader import *
from .writer import *
from .parser import *

class ElsetGenerator:
    @staticmethod
    def generate(element_stresses: Dict[int, float],
                 instance_name: str) -> List[str]:
        lines = ["** Elsets for initial stresses\n"]
        for elem in sorted(element_stresses):
            lines.append(f"*Elset, elset=Element-{elem}, "
                         f"instance={instance_name}\n")
            lines.append(f" {elem},\n")
        return lines


class InitialStressGenerator:
    @staticmethod
    def generate(element_stresses: Dict[int, List[float]]) -> List[str]:
        lines = ["**\n", "** Initial Stresses\n",
                 "*Initial Conditions, type=STRESS\n"]  # UMA VEZ

        for elem in sorted(element_stresses):
            stresses = element_stresses[elem]  # lista com 11 valores
            lines.append(f"** Element {elem} ({len(stresses)} points)\n")

            for pt_num, sig in enumerate(stresses, start=1):
                lines.append(f"Element-{elem}, {pt_num}, {sig:.2f}, 0, 0, 0, 0, 0\n")

        return lines



class INPInserter:
    @staticmethod
    def insert_elsets(inp_lines: List[str],
                      elset_lines: List[str]) -> List[str]:
        """
        Elsets logo antes do *End Assembly (fora de qualquer Instance).
        """
        new_lines, inserted = [], False
        for line in inp_lines:
            if not inserted and INPParser.is_header(line, '*end assembly'):
                new_lines.extend(elset_lines)
                inserted = True
            new_lines.append(line)

        if not inserted:
            new_lines.extend(elset_lines)          # fallback
        return new_lines

    @staticmethod
    def insert_initial_stresses(inp_lines: List[str],
                                stress_lines: List[str]) -> List[str]:
        """
        """
        first_step = next((i for i, ln in enumerate(inp_lines)
                           if INPParser.is_header(ln.lstrip(), '*step')), None)

        if first_step is None:
            # Sem *Step ‑ coloca tudo no final
            return (inp_lines +
                    ["** PREDEFINED FIELDS\n"] +
                    stress_lines)

        prefix, suffix = inp_lines[:first_step], inp_lines[first_step:]

        # procurar '** PREDEFINED FIELDS' em prefixo
        insert_idx = next((i for i, ln in enumerate(prefix)
                           if "** predefined fields" in ln.lower()), None)

        if insert_idx is None:
            prefix.extend(["** PREDEFINED FIELDS\n"])
            prefix.extend(stress_lines)
        else:
            prefix[insert_idx + 1:insert_idx + 1] = stress_lines

        # linha separadora antes do *Step
        if not prefix[-1].strip():
            prefix.pop()  # remove blank se existir
        prefix.extend(["** ----------------------------------------------------------------\n",
                       "** \n"])

        return prefix + suffix

    @staticmethod
    def fix_restart_frequency(inp_lines: List[str]) -> List[str]:
        """
        """
        fixed = []
        for ln in inp_lines:
            if "frequency=0" in ln.lower():
                ln = (ln.replace("frequency=0", "frequency=1")
                        .replace("FREQUENCY=0", "FREQUENCY=1"))
            fixed.append(ln)
        return fixed

    @staticmethod
    def replace_material_block(inp_lines: List[str], material_name: str, new_block: List[str]) -> List[str]:
        """
        Substitui bloco de material de forma inteligente, ignorando sub-opções antigas
        (como *Elastic, *Plastic, *Density) até encontrar um novo comando de alto nível.
        """
        output_lines = []
        skipping = False
        replaced = False
        target_upper = material_name.upper()

        # Lista de comandos que DEFINITIVAMENTE encerram um bloco de material
        # Qualquer coisa que não esteja aqui será considerada propriedade do material (e removida)
        block_breakers = [
            '*material', '*step', '*solid section', '*shell section',
            '*boundary', '*initial conditions', '*amplitude', '*surface',
            '*element', '*node', '*nset', '*elset', '*part', '*instance',
            '*assembly', '*end instance', '*end assembly', '*end part'
        ]

        for line in inp_lines:
            line_strip = line.strip().lower()

            # 1. Se estamos deletando o bloco antigo
            if skipping:
                if line_strip.startswith('*') and not line_strip.startswith('**'):
                    # Verifica se é um comando que encerra o bloco (Breaker)
                    is_breaker = any(line_strip.startswith(b) for b in block_breakers)

                    if is_breaker:
                        skipping = False
                        # Não damos append aqui ainda, pois vai cair no fluxo normal abaixo
                    else:
                        # É uma sub-propriedade (ex: *Elastic), continuamos deletando
                        continue
                else:
                    # É linha de dados (números) ou comentário, continua deletando
                    continue

            # 2. Se não estamos pulando, verifica se é o início do material alvo
            if INPParser.is_header(line, '*material'):
                current_name = INPParser.get_parameter(line, 'name')

                if current_name and current_name.upper() == target_upper:
                    skipping = True
                    replaced = True
                    output_lines.extend(new_block)  # Insere o bloco novo
                    continue  # Pula a linha de declaração antiga

            # 3. Caso normal: mantém a linha original
            output_lines.append(line)

        if not replaced:
            print(f"AVISO: Material '{material_name}' não encontrado para substituição.")

        return output_lines

    @staticmethod
    def insert_in_step(inp_lines: List[str], step_name: str, new_lines: List[str]) -> List[str]:
        """
        Insere linhas (ex: Boundary Conditions) dentro de um Step específico.
        Insere logo antes do *End Step.
        """
        output = []
        target_step_lower = step_name.lower()
        in_target_step = False
        inserted = False

        for line in inp_lines:
            # 1. Detecta entrada no Step correto
            if INPParser.is_header(line, '*step'):
                current_name = INPParser.get_parameter(line, 'name')
                if current_name and current_name.lower() == target_step_lower:
                    in_target_step = True

            # 2. Detecta fim do Step e insere conteúdo
            if in_target_step and INPParser.is_header(line, '*end step'):
                output.extend(new_lines)
                in_target_step = False
                inserted = True

            output.append(line)

        if not inserted:
            print(f"AVISO: Step '{step_name}' não encontrado. Conteúdo não inserido.")

        return output


class BCGenerator:
    """Gera blocos *Boundary com deslocamentos (Versão Corrigida: Strings Exatas)."""

    @staticmethod
    def generate(all_nodes: Dict[int, tuple],
                 node_ids: List[int],
                 calculate_z_func,
                 params, degree,
                 instance_name: str) -> List[str]:

        # Cabeçalho idêntico ao original para evitar problemas
        bc_lines = [
            "** \n",
            "** BOUNDARY CONDITIONS (Displacement) adicionadas pelo script\n",
            "** \n"
        ]

        count = 1
        generated_count = 0

        for nid in node_ids:
            if nid not in all_nodes:
                continue
            x, y, z_orig = all_nodes[nid]
            new_z = calculate_z_func(params, x, y, degree)
            disp = -new_z

            if abs(disp) > 1e-6:
                # [CORREÇÃO] Adicionado o "Type: Displacement/Rotation" que faltava
                bc_lines.append(f"** Name: Disp-BC-{count} Type: Displacement/Rotation\n")
                bc_lines.append("*Boundary\n")
                bc_lines.append(f"{instance_name}.{nid}, 3, 3, {disp:.6f}\n")
                count += 1
                generated_count += 1

        print(f"  → {generated_count} BCs de deslocamento geradas.")
        return bc_lines

class StressINPWriter:
    def __init__(self,
                 inp_path: str,
                 instance_name: str = "T_SHAPE_PART-1"):
        self.reader = INPReader(inp_path)
        self.instance_name = instance_name

    def write(self,
              element_stresses: Dict[int, float],
              output_path: str) -> None:
        # 1) Ler arquivo original
        inp_lines = self.reader.read()

        # 2) Gerar blocos
        elset_lines = ElsetGenerator.generate(element_stresses,
                                              self.instance_name)
        stress_lines = InitialStressGenerator.generate(element_stresses)

        # 3) Inserir blocos
        inp_lines = INPInserter.insert_elsets(inp_lines, elset_lines)
        inp_lines = INPInserter.insert_initial_stresses(inp_lines,
                                                        stress_lines)
        # 4) Corrigir frequency=0
        inp_lines = INPInserter.fix_restart_frequency(inp_lines)

        # 5) Escrever resultado
        INPWriter(output_path).write(inp_lines)

        print(f"✓ INP modificado criado: {output_path}")
        print(f"  → {len(element_stresses)} elementos com tensão inicial")
