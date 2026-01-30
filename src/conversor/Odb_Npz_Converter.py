#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
OdbToNPYConverter: Converte arquivos ODB do Abaqus para arquivos .npy
salvando dados de geometria, topologia e campos físicos (deslocamento, tensões, etc.)
em arrays numpy separados para cada frame e step.

Estrutura dos arquivos gerados:
    output_path/
        coordinates.npy         # Array [n_nodes, 3]
        connectivity.npy        # Array achatada de conectividade
        element_types.npy       # Array [n_elements]
        offsets.npy             # Offsets para conectividade
        time_series/
            step_X_nome/
                frame_Y/
                    displacement.npy    # [n_nodes, 3]
                    stress_tensor.npy   # [n_nodes, 9]
                    von_mises.npy       # [n_nodes]
                    max_principal.npy   # [n_nodes]
                    min_principal.npy   # [n_nodes]

Os dados de tensões são filtrados: se o valor de von Mises for inferior ao threshold (default: 1e-6),
os valores de tensões (tensor, máximo e mínimo) são zerados.

Uso:
    converter = OdbToNPYConverter(
         odb_path=r"C:\Simulations_All\Contour_Method",
         odb_name='Mesh_0_8_Lenth_50_FI',
         output_path=r'C:\Temp\ooxdmf',
         mesh_type='12',
         steps='all',
         instances='all',
         stress_threshold=1e-6,
         batch_size=1000,
         compression=True
    )
    converter.convert()
"""

from __future__ import print_function
import os, sys, time, gc
import numpy as np
from odbAccess import *  # Disponibiliza constantes como ELEMENT_NODAL, INTEGRATION_POINT, etc.
import re
from numpy.lib.format import open_memmap   # já vem com NumPy

try:    xrange
except  NameError: xrange = range

class OdbToNPYConverter(object):
    def __init__(self, odb_path, odb_name, output_path, mesh_type, 
                 steps='all', instances='all', stress_threshold=1e-6,
                 batch_size=1000, compression=True, begin_frame='-1', end_frame='-1'):

        self.odb_path           = odb_path
        self.odb_name           = odb_name
        self.output_path        = output_path
        self.mesh_type          = int(mesh_type)
        self.steps              = steps
        self.instances          = instances
        self.stress_threshold   = stress_threshold
        self.batch_size         = batch_size
        self.compression        = compression
        self.begin_frame        = begin_frame
        self.end_frame          = end_frame

        if self.mesh_type == 12:
            self.mesh_conner = 8
            self.mesh_name = "Hexahedron"
        elif self.mesh_type == 10:
            self.mesh_conner = 4
            self.mesh_name = "Tetra"
        else:
            print("Mesh type error or unidentified")
            sys.exit(0)

    def convert(self):
        """
        Executa o processo completo de conversão:
          1. Abre o arquivo ODB
          2. Extrai a geometria e a topologia (de todas as instâncias selecionadas)
          3. Processa os dados temporais (steps e frames)
          4. Salva os dados em arquivos .npy separados por tipo e frame
        """
        start_time = time.time()
        print("=== ODB TO NPY CONVERSION ===")
        print("Model: {} \nMesh type: {}".format(self.odb_name, self.mesh_name))
        
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
            print("Output directory created: {}".format(self.output_path))
        
        odb_full_path = os.path.join(self.odb_path, self.odb_name) + '.odb'
        if not os.path.exists(odb_full_path):
            print("ERROR: ODB file not found: {}".format(odb_full_path))
            return
        
        odb = openOdb(odb_full_path, readOnly=True)
        print("ODB opened successfully")

        
        try:
            # 1) Extrai a geometria e topologia agregando os dados das instâncias selecionadas
            geom_data = self._extract_geometry(odb)
            print("Geometry extracted: total nodes = {}".format(geom_data["global_node_count"]))
            
            # 2) Salva geometria e topologia imediatamente
            self._save_geometry_topology(geom_data)
            print("Geometry and topology saved")
            
            # 3) Processa os dados temporais em chunks - não mantém tudo em memória
            self._process_temporal_data_optimized(odb, geom_data["global_node_count"],
                                                 geom_data["instance_mapping"])
            print("Temporal data processed and saved")
            
        except Exception as e:
            print("General error in conversion: {}".format(str(e)))
        finally:
            try:
                odb.close()
            except:
                pass
            print("\nTotal time: {:.2f}s".format(time.time() - start_time))

    def _save_geometry_topology(self, geom_data):
        """Salva geometria e topologia imediatamente após extração."""
        np.save(os.path.join(self.output_path, 'coordinates.npy'),
                geom_data['coordinates'])
        np.save(os.path.join(self.output_path, 'connectivity.npy'),
                geom_data['connectivity'])
        np.save(os.path.join(self.output_path, 'element_types.npy'),
                geom_data['element_types'])
        np.save(os.path.join(self.output_path, 'offsets.npy'),
                geom_data['offsets'])
        
        # Libera memória da geometria
        del geom_data['coordinates']
        del geom_data['connectivity']
        del geom_data['element_types']
        del geom_data['offsets']
        gc.collect()


    # ------------------------------------------------------------------
    @staticmethod
    def _cache_displacement_data(field_u):
        """
        Retorna:
            cache[instance_name][node_label] = [ FieldValue, FieldValue, ... ]
        Mantém TODAS as ocorrências de deslocamento do nó
        """
        cache = {}
        if field_u is None:
            return cache

        # Estratégias análogas às das tensões
        strategies = [
            (NODAL,             "Nodal"),
            (ELEMENT_NODAL,     "Element-Nodal"),
            (INTEGRATION_POINT, "Integration-Point"),
            (None,              "Default")
        ]
        for pos, desc in strategies:
            fld = field_u if pos is None else field_u.getSubset(position=pos)
            if not fld.values:
                continue
            for v in fld.values:
                inst = v.instance.name
                nlab = getattr(v, 'nodeLabel', None)
                if inst and nlab:
                    cache.setdefault(inst, {}).setdefault(nlab, []).append(v)
            print("Displacement data found using: {} ({} values)".format(
                desc, len(fld.values)))
            return cache

        print("WARNING: no displacement strategy worked!")
        return cache

    # ------------------------------------------------------------------
    @staticmethod
    def _cache_stress_data(field_s):
        """
        Retorna:
            cache[instance_name][node_label] = [ FieldValue, FieldValue, ... ]
        Mantém TODAS as ocorrências de tensão do nó
        """
        cache = {}
        if field_s is None:
            return cache

        # tentamos primeiro ELEMENT_NODAL (mais comum)
        strategies = [
            (ELEMENT_NODAL,     "Element-Nodal"),
            (NODAL,             "Nodal"),
            (INTEGRATION_POINT, "Integration-Point"),
            (None,              "Default")
        ]
        for pos, desc in strategies:
            fld = field_s if pos is None else field_s.getSubset(position=pos)
            if not fld.values:
                continue
            # sucesso – guardamos listas
            for v in fld.values:
                inst = v.instance.name
                nlab = getattr(v, 'nodeLabel', None)
                if inst and nlab:
                    cache.setdefault(inst, {}).setdefault(nlab, []).append(v)
            print("Stress data found using: {} ({} values)".format(desc, len(fld.values)))
            return cache

        print("WARNING: no stress strategy worked!")
        return cache
    # ------------------------------------------------------------------



    @staticmethod
    def _get_indices_to_process(items, available_names, item_type):
        """
        Determina os índices (dentro da lista de nomes disponíveis) a processar.
        Se items for 'all', retorna todos os índices.
        Caso contrário, supõe que items é uma string separada por vírgula.
        """
        if items == 'all':
            return list(range(len(available_names)))
        indices = []
        for item in items.split(",") if isinstance(items, str) else items:
            try:
                idx = int(item)
                if 0 <= idx < len(available_names):
                    indices.append(idx)
                else:
                    print("WARNING: Invalid {} index {} (max: {})".format(item_type, idx, len(available_names)-1))
            except ValueError:
                print("WARNING: Invalid {} index: {}".format(item_type, item))
        return indices
    
    def _get_frame_range(self, frames):
        """
        Retorna o intervalo de frames a ser processado baseado em begin_frame e end_frame.
        -1 significa último frame.
        """
        total = len(frames)
        # converte strings → ints (ou -1)
        b = int(self.begin_frame) if str(self.begin_frame) != '-1' else -1
        e = int(self.end_frame)   if str(self.end_frame)   != '-1' else -1
        # -1 → último frame
        if b < 0: b = total - 1
        if e < 0: e = total - 1
        # limita a [0, total-1]
        b = max(0, min(b, total-1))
        e = max(0, min(e, total-1))
        # se b>e, processa só b
        if b > e: e = b
        return b, e


    def _extract_geometry(self, odb):
        """
        Extrai os dados de geometria e topologia agregando os nós e conectividade
        de todas as instâncias selecionadas.
        """
        rootassembly = odb.rootAssembly
        instances_obj = rootassembly.instances
        available_instances = list(instances_obj.keys())
        instance_indices = self._get_indices_to_process(self.instances, available_instances, "instance")
        
        global_coords = []
        connectivity = []
        element_types = []
        offsets = []
        instance_mapping = {}
        element_counter = 0
        current_global_node_count = 0
        
        for idx in instance_indices:
            inst_name = available_instances[idx]
            inst_obj = instances_obj[inst_name]
            nodes = inst_obj.nodes
            
            # CORREÇÃO: Criar mapeamento correto label->índice
            node_map = {}
            node_labels = []  # Lista ordenada dos labels desta instância
            
            for node in nodes:
                global_coords.append(node.coordinates)
                node_map[node.label] = current_global_node_count
                node_labels.append(node.label)
                current_global_node_count += 1
                
            instance_mapping[inst_name] = {
                "node_mapping": node_map,
                "node_count": len(nodes),
                "global_start": current_global_node_count - len(nodes),
                "node_labels": node_labels  # ADICIONAR: lista dos labels reais
            }
            
            # Processa elementos usando o mapeamento correto
            elements = inst_obj.elements
            for elem in elements:
                conn = elem.connectivity
                if len(conn) < self.mesh_conner:
                    continue
                mapped = [node_map[nlabel] for nlabel in conn[:self.mesh_conner]]
                
                connectivity.extend(mapped)
                element_types.append(self.mesh_type)
                element_counter += 1
                offsets.append(element_counter * self.mesh_conner)
        
        return {
            "coordinates": np.array(global_coords, dtype=np.float64),
            "connectivity": np.array(connectivity, dtype=np.int32),
            "element_types": np.array(element_types, dtype=np.uint8),
            "offsets": np.array(offsets, dtype=np.int32),
            "global_node_count": current_global_node_count,
            "instance_mapping": instance_mapping
        }


    def _process_temporal_data_optimized(self, odb, global_node_count, instance_mapping):
        """
        Processa os dados temporais de forma otimizada:
        1. Cache dos dados de campo para evitar múltiplos acessos
        2. Processamento em chunks para economizar memória
        3. Salvamento imediato de cada frame
        """
        steps_obj        = odb.steps
        available_steps  = list(steps_obj.keys())
        step_indices     = self._get_indices_to_process(self.steps, available_steps, "step")

        for s_idx in step_indices:
            step_name = available_steps[s_idx]
            frames    = steps_obj[step_name].frames
            begin_f, end_f = self._get_frame_range(frames)
            
            # Cria diretório do step
            safe_step_name = re.sub(r'[^\w\-\.]', '_', step_name) 
            step_dir = os.path.join(
                self.output_path, 
                'time_series', 
                'step_{}_{}'.format(s_idx + 1, safe_step_name)
                )
            if not os.path.exists(step_dir):
                os.makedirs(step_dir)
            
            print("Processing step {}/{}: {}".format(s_idx + 1, len(step_indices), step_name))

            for f_idx in range(begin_f, end_f + 1):
                frame = frames[f_idx]
                print("  Processing frame {}/{}".format(f_idx + 1, end_f + 1))
                
                # Processa e salva frame em chunks
                self._process_and_save_frame(frame, step_dir, f_idx, global_node_count, instance_mapping)
                
                # Força limpeza de memória
                gc.collect()

    def stress_map(self):
        _STRESS_MAP = (
            (0, 0),  # S11
            (4, 1),  # S22
            (8, 2),  # S33
            (1, 3), (3, 3),  # S12 -> (0,1) e (1,0)
            (2, 4), (6, 4),  # S13
            (5, 5), (7, 5),  # S23
        )
        return _STRESS_MAP

    @staticmethod
    def _get_nonempty_attr(obj, attr, default=None):
        """
        Retorna obj.<attr> se existir e tiver len>0 (quando aplicável),
        senão retorna default.
        """
        val = getattr(obj, attr, default)
        if val is None: return default
        if len(val) == 0: return default

        return val

    def _process_and_save_frame(self, frame, step_dir, frame_idx, global_node_count, instance_mapping):
        """
        VERSÃO OTIMIZADA: Usa os invariantes JÁ CALCULADOS pelo Abaqus
        """
        frame_dir = os.path.join(step_dir, 'frame_{:03d}'.format(frame_idx + 1))
        if not os.path.exists(frame_dir):
            os.makedirs(frame_dir)

        # 1. Alocação
        sum_disp = np.zeros((global_node_count, 3), dtype=np.float32)
        sum_stress = np.zeros((global_node_count, 9), dtype=np.float32)

        # NOVO: Arrays para invariantes
        sum_mises = np.zeros(global_node_count, dtype=np.float32)
        sum_max_principal = np.zeros(global_node_count, dtype=np.float32)
        sum_min_principal = np.zeros(global_node_count, dtype=np.float32)

        count_disp = np.zeros(global_node_count, dtype=np.float32)
        count_stress = np.zeros(global_node_count, dtype=np.float32)

        field_u = frame.fieldOutputs['U'] if 'U' in frame.fieldOutputs else None
        if field_u is not None:
            for block in field_u.bulkDataBlocks:
                # Guard: bloco/instância inválidos
                inst = getattr(block, "instance", None)
                if not inst:continue

                inst_name = inst.name
                inst_map = instance_mapping.get(inst_name)
                if not inst_map:continue

                node_map = inst_map.get("node_mapping")
                if not node_map:continue

                block_labels = self._get_nonempty_attr(block, "nodeLabels")
                block_data   = self._get_nonempty_attr(block, "data")

                if block_labels is None or block_data is None: continue

                get_idx = node_map.get

                for i in xrange(len(block_labels)):
                    idx = get_idx(block_labels[i])
                    if idx is None:continue

                    sum_disp[idx]   += block_data[i]
                    count_disp[idx] += 1.0

        # 3. TENSÃO (COM INVARIANTES DO ABAQUS!)
        field_s = frame.fieldOutputs['S'] if 'S' in frame.fieldOutputs else None
        if field_s is not None:
            stress_map = self.stress_map()
            for block in field_s.bulkDataBlocks:

                inst = getattr(block, "instance", None)
                if not inst:continue

                inst_map = instance_mapping.get(inst.name)
                if not inst_map:continue

                node_map = inst_map.get("node_mapping")
                if not node_map:continue

                block_labels = self._get_nonempty_attr(block, "nodeLabels")
                block_data   = self._get_nonempty_attr(block, "data")

                if block_labels is None or block_data is None: continue

                block_mises  = self._get_nonempty_attr(block, "mises")
                block_max_p  = self._get_nonempty_attr(block, "maxPrincipal")
                block_min_p  = self._get_nonempty_attr(block, "minPrincipal")


                get_idx = node_map.get

                for i in xrange(len(block_labels)):
                    idx = get_idx(block_labels[i])
                    if idx is None:continue
                    
                    d = block_data[i]

                    row = sum_stress[idx]
                    for out_i, in_i in stress_map:
                        row[out_i] += d[in_i]

                    if block_mises is not None:
                        sum_mises[idx] += block_mises[i]
                    if block_max_p is not None:
                        sum_max_principal[idx] += block_max_p[i]
                    if block_min_p is not None:
                        sum_min_principal[idx] += block_min_p[i]

                    count_stress[idx] += 1.0

        # 4. MÉDIAS
        np.maximum(count_disp, 1.0, out=count_disp)
        np.maximum(count_stress, 1.0, out=count_stress)

        full_displacement = sum_disp / count_disp[:, np.newaxis]
        full_stress_tensor = sum_stress / count_stress[:, np.newaxis]

        # MÉDIAS DOS INVARIANTES (DIRETO DO ABAQUS)
        full_von_mises = sum_mises / count_stress
        full_max_principal = sum_max_principal / count_stress
        full_min_principal = sum_min_principal / count_stress

        # 5. THRESHOLD (igual)
        mask = full_von_mises < self.stress_threshold
        if np.any(mask):
            full_von_mises[mask] = 0.0
            full_max_principal[mask] = 0.0
            full_min_principal[mask] = 0.0
            full_stress_tensor[mask] = 0.0

        # 6. SAVE
        np.save(os.path.join(frame_dir, "displacement.npy"), full_displacement)
        np.save(os.path.join(frame_dir, "stress_tensor.npy"), full_stress_tensor)
        np.save(os.path.join(frame_dir, "von_mises.npy"), full_von_mises)
        np.save(os.path.join(frame_dir, "max_principal.npy"), full_max_principal)
        np.save(os.path.join(frame_dir, "min_principal.npy"), full_min_principal)

if __name__ == '__main__':
    converter = OdbToNPYConverter(
        odb_path            = r"C:\Simulations_All\Contour_Method",
        odb_name            = 'Mesh_0_8_Lenth_50_FI',
        output_path         = r'C:\Temp\ooxdmf',
        mesh_type           = '12',
        steps               = 'all',
        instances           = '-1',
        stress_threshold    = 1e-6,
        batch_size          = 1000,
        compression         = True
    )
    converter.convert()