#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Npy_2_Xdmf.py
-------------
Converte as pastas geradas pelo OdbToNPYConverter (arquivos *.npy)
para um par de arquivos único XDMF + HDF5.

Estrutura de entrada esperada
    <root_npy_dir>/
       Mesh-0_9--Lenth-50_FI/
          coordinates.npy
          connectivity.npy
          element_types.npy
          offsets.npy
          time_series/
              step_1_*(...)/frame_1/  displacement.npy ...
              ...

Estrutura de saída (um único arquivo)
    S_batch.h5
        ├─  Mesh-0_9--Lenth-50_FI/geometry/coordinates
        ├─  Mesh-0_9--Lenth-50_FI/geometry/connectivity
        ├─  Mesh-0_9--Lenth-50_FI/topology/element_types
        ├─  Mesh-0_9--Lenth-50_FI/topology/offsets
        └─  Mesh-0_9--Lenth-50_FI/time_series/step_1/frame_1/...
    S_batch.xdmf          <-- referencia o HDF5

Dependências
    numpy, h5py, xml.etree.ElementTree, xml.dom.minidom, logging, json
"""

import os
import re
import sys
import json
import glob
import h5py
import errno
import logging
import inspect
import numpy as np
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom                               # Para “pretty print”

# -----------------------------------------------------------------------------#
# Utilitário de log – o mesmo usado nos outros módulos
# -----------------------------------------------------------------------------#
from Exp_Data.s1_exp    import CONFIG_PATH
from utils              import *

# -----------------------------------------------------------------------------#
# (1) PARAMETRIZAÇÃO – a “cara” da classe ODB2NPYParameters
# -----------------------------------------------------------------------------#
class NPY2XDMFParameters(object):
    """
    NPY2XDMFParameters / (class)
    What it does:
    Loads the project's config.json and returns input/output directories and options for the NPY to XDMF conversion process.
    """
    def __init__(self,
                 config_path=None,
                 method_type="Contour_Method",
                 method_type_dir="CM_directory"):
        self.logger = setup_logger(self.__class__.__name__)
        self.config = self._load_config(config_path)
        self.method_type = method_type
        self.method_type_dir = method_type_dir

        # defaults
        self.options = {
            "hdf5_compression": True,
            "xdmf_precision"  : 8     # double
        }

    # --------------------------------------------------------------------- #
    def _load_config(self, config_path):
        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(
                inspect.getfile(inspect.currentframe())))
            root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
            config_path = CONFIG_PATH
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning("Não foi possível carregar config: %s", e)
            return {}

    # --------------------------------------------------------------------- #
    def run(self):
        """
        run / (method)
        What it does:
        Reads config.json and returns (input_dir, output_dir, options) for the conversion.
        """
        # … da mesma forma que ODB2NPYParameters …
        directories = self.config.get("directories", {})
        conv_params = self.config.get("conversion_params", {})

        input_dir  = directories.get(self.method_type_dir, "")
        output_dir = os.path.join(input_dir, "xdmf_hdf5_files")

        self.options.update(conv_params.get("NPY2XDMF", {}))   # opcional

        self.logger.info("Input dir : %s", input_dir)
        self.logger.info("Output dir: %s", output_dir)
        self.logger.info("Opções    : %s", self.options)

        return input_dir, output_dir, self.options


# -----------------------------------------------------------------------------#
# (2) CONVERSOR PRINCIPAL
# -----------------------------------------------------------------------------#
class Npy2XdmfConverter(object):
    """
    Npy2XdmfConverter / (class)
    What it does:
    Converts all subfolders inside `root_dir` (each folder = one model) into a single S_batch.h5 + S_batch.xdmf file pair.
    """
    def __init__(self,
                 root_dir,
                 output_dir,
                 h5_filename="S_batch.h5",
                 compression=True,
                 logger=None):
        self.root_dir      = os.path.abspath(root_dir)
        self.output_dir    = os.path.abspath(output_dir)
        self.h5_filename   = h5_filename
        self.compression   = compression
        self.logger        = logger or setup_logger(self.__class__.__name__)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.h5_path   = os.path.join(self.output_dir, self.h5_filename)
        self.xdmf_path = os.path.splitext(self.h5_path)[0] + ".xdmf"

        self.precision_coord = 8    # 8 Bytes = double
        self.precision_data  = 4    # 4 Bytes = float32

        # meta para o XDMF
        self._meta = {}     # sim_name -> dict( n_nodes, n_elems, nodes_per_elem )

    # --------------------------------------------------------------------- #
    @staticmethod
    def _np_load(path):
        # Usa mmap para não encher a RAM quando possível
        return np.load(path, mmap_mode='r')

    # --------------------------------------------------------------------- #
    def _write_hdf5(self):
        """
        _write_hdf5 / (method)
        What it does:
        Iterates through all subfolders in root_dir and writes their data into the HDF5 file, preserving the hierarchy for geometry and time series.
        """
        flags = {"compression": "gzip", "compression_opts": 6} \
                if self.compression else {}

        with h5py.File(self.h5_path, "w") as h5:
            # Cada sub-diretório de primeiro nível que contenha coordinates.npy
            # é assumido como um “modelo”.
            sim_dirs = sorted(
                d for d in glob.glob(os.path.join(self.root_dir, "*"))
                if os.path.isdir(d) and
                   os.path.exists(os.path.join(d, "coordinates.npy"))
            )

            if not sim_dirs:
                raise RuntimeError("Nenhum diretório válido com *.npy foi encontrado em %s" %
                                   self.root_dir)

            for sim_dir in sim_dirs:
                sim_name = os.path.basename(sim_dir)
                self.logger.info("Processando modelo: %s", sim_name)
                grp = h5.create_group(sim_name)

                # -----------------  GEOMETRIA  --------------------------- #
                g_geo = grp.create_group("geometry")
                coords = self._np_load(os.path.join(sim_dir, "coordinates.npy"))
                conn   = self._np_load(os.path.join(sim_dir, "connectivity.npy"))

                # reshape conectividade => (n_elem, nodes_per_elem)
                # nodes_per_elem = deduzido do número de colunas. Ex.: Hexa = 8
                element_types = self._np_load(os.path.join(sim_dir,
                                                           "element_types.npy"))
                nodes_per_elem = int(conn.size // element_types.size)
                conn_2d = conn.reshape((-1, nodes_per_elem))

                # grava
                g_geo.create_dataset("coordinates",
                                     data=coords,
                                     dtype=np.float64,
                                     **flags)
                g_geo.create_dataset("connectivity",
                                     data=conn_2d.astype(np.int32),
                                     dtype=np.int32,
                                     **flags)

                # -----------------  TOPOLOGIA  --------------------------- #
                g_topo = grp.create_group("topology")
                offsets = self._np_load(os.path.join(sim_dir, "offsets.npy"))
                g_topo.create_dataset("element_types", data=element_types.astype(np.uint8),
                                      dtype=np.uint8)
                g_topo.create_dataset("offsets", data=offsets.astype(np.int32),
                                      dtype=np.int32)

                # -----------------  TIME SERIES -------------------------- #
                ts_src = os.path.join(sim_dir, "time_series")
                if not os.path.exists(ts_src):
                    self.logger.warning("time_series não encontrado em %s", sim_dir)
                else:
                    g_ts = grp.create_group("time_series")
                    for step in sorted(os.listdir(ts_src)):
                        step_src = os.path.join(ts_src, step)
                        if not os.path.isdir(step_src):
                            continue
                        g_step = g_ts.create_group(step)
                        for frame in sorted(os.listdir(step_src)):
                            frame_src = os.path.join(step_src, frame)
                            if not os.path.isdir(frame_src):
                                continue
                            g_frame = g_step.create_group(frame)
                            # Cada *.npy dentro do frame vira um DataSet
                            for npy_file in glob.glob(os.path.join(frame_src, "*.npy")):
                                name = os.path.splitext(os.path.basename(npy_file))[0]
                                arr  = self._np_load(npy_file)
                                g_frame.create_dataset(name,
                                                       data=arr.astype(np.float32),
                                                       dtype=np.float32,
                                                       **flags)

                # ----------  meta (para escrever o XDMF depois) ---------- #
                self._meta[sim_name] = dict(
                    n_nodes         = coords.shape[0],
                    n_elems         = conn_2d.shape[0],
                    nodes_per_elem  = nodes_per_elem
                )

    # --------------------------------------------------------------------- #
    # ---------------------------  X D M F  --------------------------------#
    # --------------------------------------------------------------------- #
    def _write_xdmf(self):
        """
        _write_xdmf / (method)
        What it does:
        Uses metadata from self._meta to build a temporal XDMF file for each model, referencing the HDF5 datasets.
        """
        xdmf = Element("Xdmf", Version="3.0")
        domain = SubElement(xdmf, "Domain")

        # Cada modelo recebe um Grid temporal:
        for sim_name, m in self._meta.items():
            g_time = SubElement(domain, "Grid",
                                Name            = f"{sim_name}_TimeSeries",
                                GridType        = "Collection",
                                CollectionType  = "Temporal")
            # Descobre quantos steps/frames há percorrendo o HDF5
            with h5py.File(self.h5_path, "r") as h5:
                ts_grp = h5[sim_name]["time_series"]
                steps = list(ts_grp.keys())

                time_counter = 0
                for s_name in steps:
                    frames = list(ts_grp[s_name].keys())
                    for f_name in frames:
                        # Grid uniforme para este frame ------------------ #
                        g = SubElement(g_time, "Grid",
                                       Name=f"{sim_name}_{s_name}_{f_name}",
                                       GridType="Uniform")

                        SubElement(g, "Time",
                                   Value=str(time_counter))
                        time_counter += 1

                        # ----------- Topologia ------------------------- #
                        topo_type = "Hexahedron" if m["nodes_per_elem"] == 8 else \
                                    "Tetrahedron" if m["nodes_per_elem"] == 4 else "Polyvertex"
                        topo = SubElement(g, "Topology",
                                          TopologyType=topo_type,
                                          NumberOfElements=str(m["n_elems"]))
                        SubElement(topo, "DataItem",
                                   Dimensions=f"{m['n_elems']} {m['nodes_per_elem']}",
                                   NumberType="Int",
                                   Precision="4",
                                   Format="HDF").text = \
                            f"{os.path.basename(self.h5_path)}:/{sim_name}/geometry/connectivity"

                        # ------------- Geometria ----------------------- #
                        geo = SubElement(g, "Geometry", GeometryType="XYZ")
                        SubElement(geo, "DataItem",
                                   Dimensions=f"{m['n_nodes']} 3",
                                   NumberType="Float",
                                   Precision=str(self.precision_coord),
                                   Format="HDF").text = \
                            f"{os.path.basename(self.h5_path)}:/{sim_name}/geometry/coordinates"

                        # ------------- Atributos (campo) --------------- #
                        frame_path = f"/{sim_name}/time_series/{s_name}/{f_name}"
                        with h5py.File(self.h5_path, "r") as h5:
                            for attr_name, dset in h5[frame_path].items():
                                if dset.ndim == 2 and dset.shape[1] == 3:
                                    att_type = "Vector"
                                    dims     = f"{m['n_nodes']} 3"
                                    prec     = self.precision_data
                                elif dset.ndim == 2 and dset.shape[1] == 9:
                                    att_type = "Tensor6"   # para ParaView o campo é tensor
                                    dims     = f"{m['n_nodes']} 9"
                                    prec     = self.precision_data
                                else:                       # escalares
                                    att_type = "Scalar"
                                    dims     = f"{m['n_nodes']}"
                                    prec     = self.precision_data

                                att = SubElement(g, "Attribute",
                                                 Name=attr_name,
                                                 AttributeType=att_type,
                                                 Center="Node")
                                SubElement(att, "DataItem",
                                           Dimensions=dims,
                                           NumberType="Float",
                                           Precision=str(prec),
                                           Format="HDF").text = \
                                    f"{os.path.basename(self.h5_path)}:{frame_path}/{attr_name}"

        # -------------- pretty print + grava ------------------------------ #
        xml_str = tostring(xdmf, 'utf-8')
        reparsed = minidom.parseString(xml_str)
        pretty   = reparsed.toprettyxml(indent="  ")

        with open(self.xdmf_path, "w", encoding="utf-8") as f:
            f.write(pretty)

    # --------------------------------------------------------------------- #
    def convert(self):
        """
        convert / (method)
        What it does:
        Public method. Runs the full conversion: writes HDF5 and then XDMF.
        """
        self.logger.info("Escrevendo HDF5 → %s", self.h5_path)
        self._write_hdf5()
        self.logger.info("HDF5 pronto.")

        self.logger.info("Escrevendo XDMF → %s", self.xdmf_path)
        self._write_xdmf()
        self.logger.info("Conversão concluída!")

# -----------------------------------------------------------------------------#
# (3) BATCH CONVERTER – estilo dos outros scripts
# -----------------------------------------------------------------------------#
class NpyBatchToXdmfConverter(object):
    """
    NpyBatchToXdmfConverter / (class)
    What it does:
    Iterates through all collections (e.g., multiple simulation batches), creating an HDF5/XDMF pair for each top-level folder.
    """
    def __init__(self, input_dir, output_dir, options=None):
        self.input_dir  = input_dir
        self.output_dir = output_dir
        self.options    = options or {}
        self.logger     = setup_logger(self.__class__.__name__)

    def convert_all(self):
        """
        convert_all / (method)
        What it does:
        For each folder containing coordinates.npy, calls the converter to process and generate the output files.
        """
        # Pastas de topo (ex.: Mesh-0_8--*, Mesh-0_9--*, …)
        # Neste batch usaremos um único arquivo HDF5 + XDMF
        conv = Npy2XdmfConverter(self.input_dir,
                                 self.output_dir,
                                 h5_filename="S_batch.h5",
                                 compression=self.options.get("hdf5_compression", True))
        conv.convert()


# -----------------------------------------------------------------------------#
# (4) exemplo de utilização directa
# -----------------------------------------------------------------------------#
if __name__ == "__main__":
    # 1) Carrega parâmetros (mesma filosofia dos outros scripts)
    params_loader = NPY2XDMFParameters(method_type="Contour_Method",
                                       method_type_dir="CM_directory")
    npy_root, out_dir, opts = params_loader.run()
    npy_root = os.path.join(npy_root, "npy_files")
    # 2) Converte em batch
    batch = NpyBatchToXdmfConverter(npy_root, out_dir, opts)
    batch.convert_all()