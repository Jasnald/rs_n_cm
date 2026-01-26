# s2_RE_ExnCon_batch.py

import os
import glob
import re
from typing import Dict, Optional, Any, List

# importa a classe original
from .s2_RE_ExnCon import StressProcessor

class StressProcessorBatch(StressProcessor):
    """
    Extende StressProcessor para:
      1) descobrir meshes no padrão Mesh-*--Lenth-*
      2) para cada mesh base, processar TODOS os casos S* no HDF5
      3) salvar cada caso em Output/Sx_<Mesh-…>
    """

    def find_simulations(self) -> Dict[str, Dict[str, str]]:
        """
        Sobrescreve para:
          - aceitar Mesh-*--Lenth-*.inp (padrão principal)
          - aceitar também S*_Mesh-*--Lenth-*.inp (retrocompatível)
          - normalizar nome da mesh para 'Mesh-…' sem prefixo Sx_
        """
        try:
            patterns = [
                os.path.join(self.base_dir, "Mesh-*--Lenth-*.inp"),
                os.path.join(self.base_dir, "S*_Mesh-*--Lenth-*.inp")
            ]
            inp_files = []
            for p in patterns:
                inp_files.extend(glob.glob(p))
            inp_files = sorted(set(inp_files))

            simulations = {}
            for inp_file in inp_files:
                fname = os.path.splitext(os.path.basename(inp_file))[0]
                # remove Sx_ se existir
                m = re.match(r"^S\d+_(.+)$", fname)
                mesh_name = m.group(1) if m else fname

                output_path = os.path.join(self.base_dir, "Output", mesh_name)
                elem_data = os.path.join(output_path, "elements_data.txt")
                if os.path.exists(elem_data):
                    simulations[mesh_name] = {
                        "inp_file": inp_file,
                        "output_path": output_path,
                        "elements_data_file": elem_data
                    }
                    self.logger.info(f"Mesh encontrada: {mesh_name}")
                else:
                    self.logger.warning(
                        f"elements_data.txt não encontrado em {output_path}"
                    )

            self.logger.info(f"find_simulations: {len(simulations)} malhas válidas")
            return simulations

        except Exception as e:
            self.logger.error(f"Erro em find_simulations (batch): {e}")
            return {}

    def process_specific_simulation(
            self,
            mesh_name: str,
            hdf5_folder: str
        ) -> Optional[Dict[str, Dict[str, List[Dict[str, Any]]]]]:
        """
        Para uma mesh base (ex: 'Mesh-0_6--Lenth-50'):
          - lê HDF5 combinado
          - extrai z=0
          - lê elements_data.txt da mesh
          - para cada grupo S*, mapeia e salva em Output/Sx_<mesh_name>
        Retorna dict dos casos processados:
          { 'S1_Mesh-…': stress_by_z, 'S2_Mesh-…': stress_by_z, … }
        """
        sims = self.find_simulations()
        if mesh_name not in sims:
            self.logger.error(f"Mesh '{mesh_name}' não encontrada")
            return None

        info = sims[mesh_name]
        self.logger.info(f"=== PROCESSANDO MESH: {mesh_name} ===")

        # 1. ler HDF5 combinado
        hdf5_data = self.read_combined_hdf5_from_folder(hdf5_folder)
        if not hdf5_data:
            self.logger.error("Nenhum dado HDF5 encontrado")
            return None

        # 2. extrair z=0
        z0_all = self.extract_z0_data_by_z(hdf5_data)
        if not z0_all:
            self.logger.error("Falha ao extrair z=0")
            return None

        # 3. ler mesh
        mesh_df = self.read_mesh_file(info["elements_data_file"])
        if mesh_df is None:
            self.logger.error("Falha ao ler elements_data.txt")
            return None

        # 4. iterar sobre casos S* em z0_all[0.0]
        cases = list(z0_all.get(0.0, {}).keys())
        results = {}

        for file_key in cases:
            group_label = file_key.replace(".h5", "")   # ex: "S1"
            case_name = f"{group_label}"
            case_out = os.path.join(self.base_dir, "Output", case_name)
            os.makedirs(case_out, exist_ok=True)

            # dados só desse caso
            z0_single = {0.0: {file_key: z0_all[0.0][file_key]}}
            stress_by_z = self.create_stress_mapping_by_z(z0_single, mesh_df)
            if not stress_by_z:
                self.logger.error(f"Falha no mapeamento {case_name}")
                continue

            # salvar JSON / HDF5
            self.save_organized_data(stress_by_z, case_out, format="json")
            self.save_organized_data(stress_by_z, case_out, format="hdf5")
            # criar arquivo Abaqus
            self.create_abaqus_stress_file(stress_by_z, case_out)

            results[case_name] = stress_by_z
            self.logger.info(f"Caso {case_name} gerado em {case_out}")

        self.logger.info(f"=== CONCLUÍDO: {mesh_name} ({len(results)} casos) ===")
        return results

    def process_all_simulations(
            self,
            hdf5_folder: str
        ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Processa todas as meshes encontradas, e para cada uma
        cria sub-pastas por caso S*:
          Output/S1_<mesh>, Output/S2_<mesh>, …
        Retorna todos os casos em um único dict.
        """
        sims = self.find_simulations()
        if not sims:
            self.logger.warning("Nenhuma mesh encontrada (batch)")
            return {}

        all_results = {}
        meshes = list(sims.keys())
        for i, mesh in enumerate(meshes, 1):
            self.logger.info(f"[{i}/{len(meshes)}] processando mesh '{mesh}'")
            try:
                res = self.process_specific_simulation(mesh, hdf5_folder)
                if res:
                    all_results.update(res)
                    self.logger.info(f"Mesh '{mesh}' processada: {len(res)} casos")
                else:
                    self.logger.error(f"Mesh '{mesh}' falhou")
            except Exception as e:
                self.logger.error(f"Erro em mesh '{mesh}': {e}")
        self.logger.info(f"Batch concluído: {len(all_results)} casos gerados no total")
        return all_results


# Exemplo de uso (se executado diretamente)
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    base_dir = r"C:\Simulation4\Residual_Stresses_Analysis"
    hdf5_folder = r"C:\Simulation4\Contour_Method\xdmf_hdf5_files"

    processor = StressProcessorBatch(base_dir)
    # processa todas as meshes e casos S*
    results = processor.process_all_simulations(hdf5_folder)
    print("Casos gerados:", list(results.keys()))