# -*- coding: utf-8 -*-
"""
Name: ODB_Reader_VTK.py (refatorado para XDMF+HDF5)
What it does: Fornece classes e utilitários para converter arquivos Abaqus ODB para o novo formato
XDMF+HDF5, incluindo conversão batch e gerenciamento de configuração.
"""

import os
import sys
import inspect
import json
import logging
import re

# Define current directory and module paths
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))

# Adiciona o diretório raiz do projeto para que o Python encontre o Modules_Exp_Data
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Importa a nova classe de conversão e os parâmetros do Abaqus
from Odb_Npz_Converter  import OdbToNPYConverter
from Exp_Data.s1_exp    import *
from utils              import *


class ODB2NPYParameters(object):
    """
    Classe: ODB2XDMFParameters
    O que faz: Carrega a configuração, gerencia os parâmetros de conversão e fornece os diretórios
    de simulação (para os ODB) e de saída (para os arquivos XDMF+HDF5).
    """
    def __init__(self, config_path=None, method_type=None, method_type_dir=None):
        """
        Inicializa os parâmetros com base na configuração, método e diretórios.
        """
        self.logger = setup_logger(self.__class__.__name__, clear=True)
        self.config = self._load_config(config_path)
        # Parâmetros padrões para conversão – observe que alguns parâmetros anteriores (como Piecenum,
        # BeginFrame e EndFrame) foram substituídos por parâmetros específicos do novo conversor.
        self.conversion_params = {
            'MeshType': '12',                # '12' para Hexaedro, '10' para Tetraedro
            'stress_threshold': 1e-6,          # Threshold para filtragem de stress baixos
            'batch_size': 1000,                # Quantidade de nós processados por vez
            'inspect_first': True              # Inspeciona a estrutura do ODB antes da conversão
        }
        self.method_type = method_type
        self.method_type_dir = method_type_dir
        self.Simulation_dir = None
        self.NPY_Dir = None  # Diretório de saída atualizado para XDMF+HDF5
 
    def _load_config(self, config_path):
        """
        Carrega a configuração a partir de um arquivo JSON e retorna um dicionário.
        """
        if config_path is None:
            config_path = CONFIG_PATH
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            return config
        except Exception as e:
            self.logger.error("Erro ao carregar a configuração de '{}': {}".format(config_path, str(e)))
            return None
    
    def run(self):
        """
        Carrega os diretórios e os parâmetros de conversão a partir da configuração e os retorna.
        """
        env_message = ("Python version:     {version}\n"
                       "Current directory:  {current_dir}\n"
                       "Root directory:     {root_dir}\n"
                       "Encoding:           {encoding}"
                       ).format(version     = sys.version,
                                current_dir = current_dir,
                                root_dir    = root_dir,
                                encoding    = (sys.getdefaultencoding() if hasattr(sys, 'getdefaultencoding') 
                                          else "unknown"))
        self.logger.info(env_message)
    
        params = AbaqusParameters()
        params.parameters = self.config if self.config is not None else {}

        # Acessa diretórios e parâmetros de conversão da configuração
        self.Simulation_dir = params.parameters["directories"].get(self.method_type_dir, "")
        conversion_params = params.parameters["conversion_params"].get(self.method_type, {})
        self.conversion_params.update(conversion_params)

        # Define a pasta de saída; neste exemplo, usamos "xdmf_files" para armazenar os arquivos XDMF+HDF5
        self.NPY_Dir = os.path.join(self.Simulation_dir, "npy_files")
    
        self.logger.info("\nSimulation directory (ODB): {odb}\nOutput directory (NPY): {xdmf}".format(
            odb=self.Simulation_dir, xdmf=self.NPY_Dir))

        return self.Simulation_dir, self.NPY_Dir, self.conversion_params


class OdbBatchConverter(object):
    """
    Classe: OdbBatchConverter
    O que faz: Localiza arquivos ODB, inspeciona sua estrutura e converte-os para o novo formato XDMF+HDF5
    em batch ou individualmente.
    """
    def __init__(self, Simulation_dir, NPY_Dir, conversion_params=None):
        """
        Inicializa o conversor batch com os diretórios de simulação e saída, além dos parâmetros de conversão.
        """
        self.logger = setup_logger(self.__class__.__name__, clear=True)
        
        self.Simulation_dir = Simulation_dir
        self.NPY_Dir = NPY_Dir
        
        if conversion_params is None:
            self.conversion_params = {
                'MeshType': '12',
                'stress_threshold': 1e-6,
                'batch_size': 100,
                'inspect_first': True
            }
        else:
            self.conversion_params = conversion_params.copy()

    def set_conversion_params(self, **kwargs):
        """
        Define parâmetros de conversão personalizados para o batch converter.
        """
        self.conversion_params.update(kwargs)

    @staticmethod
    def safe_str_convert(text):
        """
        Converte com segurança um texto para string ASCII para resolver questões de Unicode na API do Abaqus.
        """
        logger = logging.getLogger(__name__)
        try:
            if sys.version_info[0] == 2:
                if isinstance(text, unicode):
                    logger.info("Convertendo unicode para ASCII: {}".format(text))
                    return text.encode('ascii', 'ignore')
                else:
                    return str(text)
            else:
                if isinstance(text, bytes):
                    logger.info("Convertendo bytes para ASCII: {}".format(text))
                    return text.decode('ascii', 'ignore')
                else:
                    return str(text)
        except Exception:
            return str(text)

    def find_odb_files(self, directory):
        """
        Procura por todos os arquivos ODB em um diretório e retorna suas paths.
        """
        odb_files = []
        if os.path.exists(directory):
            for f in os.listdir(directory):
                if f.lower().endswith(".odb"):
                    full_path = os.path.join(directory, f)
                    odb_files.append(full_path)
        else:
            self.logger.info("Diretório não encontrado: {}".format(directory))
        return odb_files

    def inspect_odb_structure(self, odb_file):
        """
        Inspeciona um arquivo ODB para determinar os steps e instâncias disponíveis, registrando a estrutura.
        """
        try:
            from odbAccess import openOdb
            message = "Inspecionando estrutura do ODB: {}\n".format(os.path.basename(odb_file))
            odb_file_safe = self.safe_str_convert(odb_file)
            odb = openOdb(odb_file_safe, readOnly=True)
            rootassembly = odb.rootAssembly
            instances_obj = rootassembly.instances
            steps_obj = odb.steps

            instance_names = list(instances_obj.keys())
            step_names = list(steps_obj.keys())

            message += "  Steps disponíveis ({} no total):\n".format(len(step_names))
            for i, step_name in enumerate(step_names):
                frames_count = len(steps_obj[step_name].frames)
                message += "    [{}] {} ({} frames)\n".format(i, step_name, frames_count)

            message += "  Instâncias disponíveis ({} no total):\n".format(len(instance_names))
            for i, inst_name in enumerate(instance_names):
                n_nodes = len(instances_obj[inst_name].nodes)
                n_elements = len(instances_obj[inst_name].elements)
                message += "    [{}] {} ({} nós, {} elementos)\n".format(i, inst_name, n_nodes, n_elements)

            odb.close()
            self.logger.info(message)

            return {
                'steps': len(step_names),
                'instances': len(instance_names),
                'step_names': step_names,
                'instance_names': instance_names
            }

        except Exception as e:
            self.logger.error("Erro inspecionando o ODB {}: {}".format(os.path.basename(odb_file), str(e)))
            return None

    def convert_single_odb(self, odb_file, output_folder):
        """
        Converte um único arquivo ODB para o formato NPY usando os parâmetros fornecidos.
        """
        header = "\n{line}\nConvertendo o arquivo: {file}\n{line}".format(
            line="=" * 45,
            file=os.path.basename(odb_file))
        self.logger.info(header)

        try:
            # Interpretar parâmetros legacy
            begin_frame = self.conversion_params.get('BeginFrame', '-1')
            end_frame = self.conversion_params.get('EndFrame', '-1') 
            piecenum = self.conversion_params.get('Piecenum', '1')
            
            if self.conversion_params.get('inspect_first', True):
                structure = self.inspect_odb_structure(odb_file)
                if structure:
                    # Determinar steps (sempre todos por enquanto)
                    steps_param = 'all'
                    
                    # Determinar instances baseado em Piecenum
                    if piecenum == '1' or piecenum == 1:
                        instances_param = '0'  # Primeira instância apenas
                    else:
                        instances_param = 'all'
                else:
                    steps_param = '0'
                    instances_param = '0'
            else:
                steps_param = '0'
                instances_param = '0'

            # Converter parâmetros de frame para o formato do conversor
            frame_params = self._convert_frame_params(begin_frame, end_frame)

            odb_path = os.path.dirname(odb_file)
            odb_basename = os.path.splitext(os.path.basename(odb_file))[0]

            odb_path_safe = self.safe_str_convert(odb_path)
            odb_basename_safe = self.safe_str_convert(odb_basename)
            output_folder_safe = self.safe_str_convert(output_folder)

            params_message = ("\nIniciando conversão...\n"
                            "Parâmetros:\n"
                            "  - Mesh Type: {mesh}\n"
                            "  - Steps: {steps}\n"
                            "  - Instances: {instances}\n"
                            "  - BeginFrame: {begin_f}\n"
                            "  - EndFrame: {end_f}\n"
                            "  - ODB Path: {odb_path}\n"
                            "  - ODB Name: {odb_name}\n"
                            "  - Output Path: {output}"
                            ).format(mesh=self.conversion_params.get('MeshType'),
                                    steps=steps_param,
                                    instances=instances_param,
                                    begin_f=begin_frame,
                                    end_f=end_frame,
                                    odb_path=odb_path_safe,
                                    odb_name=odb_basename_safe,
                                    output=output_folder_safe)
            self.logger.info(params_message)

            converter = OdbToNPYConverter(
                odb_path=odb_path_safe,
                odb_name=odb_basename_safe,
                output_path=output_folder_safe,
                mesh_type=self.conversion_params.get('MeshType', '12'),
                steps=steps_param,
                instances=instances_param,
                stress_threshold=self.conversion_params.get('stress_threshold', 1e-6),
                batch_size=self.conversion_params.get('batch_size', 1000),
                compression=False,
                # Novos parâmetros para controle de frames
                begin_frame=begin_frame,
                end_frame=end_frame
            )

            converter.convert()
            self.logger.info("\nConversão concluída com sucesso para: {}".format(os.path.basename(odb_file)))
        except Exception as e:
            self.logger.error("\nErro convertendo {}: {}\nDetalhes: {}".format(
                os.path.basename(odb_file), str(e), repr(e)))
            
    def _convert_frame_params(self, begin_frame, end_frame):
        """
        Converte parâmetros legacy de frame para o novo formato.
        -1 significa último frame.
        """
        return {
            'begin_frame': begin_frame,
            'end_frame': end_frame
        }


    def convert_batch(self):
        """
        Converte todos os arquivos ODB no diretório de simulação para o formato XDMF+HDF5 em batch.
        """
        odb_files = self.find_odb_files(self.Simulation_dir)
        if not odb_files:
            self.logger.info("Nenhum arquivo ODB encontrado em: {}".format(self.Simulation_dir))
            return

        message = ("Diretório ODB: {odb_dir}\nOutput Directory (XDMF): {output_dir}\nArquivos ODB encontrados:\n"
                   .format(odb_dir=self.Simulation_dir, output_dir=self.NPY_Dir))
        for f in odb_files:
            message += "  - {}\n".format(os.path.basename(f))
        self.logger.info(message)

        if not os.path.exists(self.NPY_Dir):
            os.makedirs(self.NPY_Dir)
            self.logger.info("Diretório de saída criado: {}".format(self.NPY_Dir))

        for odb_file in odb_files:
            odb_name = os.path.splitext(os.path.basename(odb_file))[0]
            # ao invés de passar sempre self.NPY_Dir, crie um subdiretório:
            out_dir = os.path.join(self.NPY_Dir, odb_name)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            self.convert_single_odb(odb_file, out_dir)

        complete_message = ("\n{line}\nCONVERSÃO COMPLETA!\nArquivos XDMF salvos em: {output_dir}\n{line}"
                            .format(line="=" * 45, output_dir=self.NPY_Dir))
        self.logger.info(complete_message)


# Exemplo de uso no script principal (ou o módulo de execução)
if __name__ == "__main__":
    # Primeira etapa: obter parâmetros e diretórios
    parameters = ODB2NPYParameters(
        method_type="Contour_Method", 
        method_type_dir="CM_directory")
    Simulation_dir, NPY_Dir, conversion_params = parameters.run()
    
    # Segunda etapa: executar a conversão batch
    converter = OdbBatchConverter(Simulation_dir, NPY_Dir, conversion_params)
    converter.convert_batch()