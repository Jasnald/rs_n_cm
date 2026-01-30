# -*- coding: utf-8 -*-
"""
"""

import os, sys, inspect

sys.dont_write_bytecode = True
_here = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
_parent_1 = os.path.dirname(_here)
_parent_2 = os.path.dirname(_parent_1)
for p in (_here, _parent_1, _parent_2):
    if p not in sys.path:
        sys.path.append(p)

from _modules import *  # ≤  todas as “service-classes”
from _u_json import JsonReader


class ContourAnalysisExtended(LoggerMixin, object):
    """
    """

    def __init__(self, mesh, comprimento, output,
                 initialInc, maxInc, maxNumInc, minInc,
                 nlgeom, time,
                 step_name="Material-Removal",
                 mat_name='WORK_PIECE_MATERIAL',
                 section_name='WORK_PIECE_Section'):

        super(ContourAnalysisExtended, self).__init__()

        # ❶  ARMAZENAR PARÂMETROS GERAIS
        self.mesh_size = mesh
        self.comprimento = comprimento
        self.output_dir = output

        # step / material / section
        self.step_name = step_name
        self.mat_name = mat_name
        self.section_name = section_name

        # step-params
        self.initialInc = initialInc
        self.maxInc = maxInc
        self.maxNumInc = maxNumInc
        self.minInc = minInc
        self.nlgeom = nlgeom
        self.time = time

        self.step_name1 = 'BC-Removal'
        self.step_name2 = 'BC-Removal_Nodes'

        _here = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        par_dir = os.path.join(_here, 'params.json')
        self.reader = JsonReader(par_dir)

        # Carregar coordenadas para self para uso global na classe
        self.cord1 = self.reader.load()['analysis']['geometry']['cord1']
        self.cord2 = self.reader.load()['analysis']['geometry']['cord2']
        self.cord3 = self.reader.load()['analysis']['geometry']['cord3']

        # Ajuste de comprimento/largura conforme lógica original do IV
        self.comprimento = 13
        self.largura = 4

        print(self.comprimento)

        # ❷  GEOMETRIA (geometry/sim_two/_set_geometry2.py)
        # Mantém GeometrySetterIV como no original
        self._geometry = GeometrySetterIV()
        self.model, self.t_part = self._geometry._geometry(
            depth=self.comprimento,
            height=54)
        self.instance_name = self.t_part.name + '-1'

        self.bind_context(model=self.model,
                          t_part=self.t_part,
                          instance_name=self.instance_name)

        # ❸  SERVICE-OBJECTS (core / assigment / geometry_setup …)
        self._stepper = StepSetter()
        self._mesher = MeshSetter()
        self._job = JobSetter()
        self._material = MaterialSetter()
        self._section = SectionSetter()
        self._instance = InstanceSetter()
        self._datum = DatumSetter()
        # objetos “extended”
        self._plane_info = PlaneGetter()
        self._datum_rm = RemoveDatumSetter()
        self._region = RemovalRegionSetter()
        self._set_creator = SetSetter()
        self._node_bc = NodeBCSetter()
        self._model_change = ModelChangeSetter()
        self._shape = ShapeGetterTwo()

        self._cut = PartitionYZSetter()
        self._cutY = PartitionXZSetter()
        self._edge = EdgeSetCreator()
        self._cell = CellSetCreator()
        self._mesher_seed = MeshSetterSeed()
        self._mesher_bias = MeshSetterBias()
        self._mesher_sweep = MeshSetterSweep()

        # ADICIONADO: Setter para elementos SC8R (Continuum Shell)
        self._mesher_sc8r = MeshSetterSC8R()

        self.BCBelowSetter = BCBelowSetter()

        self.nbc = NodeBCBuilder()

        self.propagate_to(
            self._mesher, self._job, self._material, self._section,
            self._instance, self._datum, self._shape,
            self._cut, self._cutY, self._edge, self._mesher_seed,
            self._mesher_bias, self._mesher_sweep, self._cell,
            self.BCBelowSetter, self.nbc, self._node_bc,
            self._mesher_sc8r  # Propagar o novo mesher
        )

    def points(self, s_name):
        """
        """

        self.nbc.build(
            point_coords=(0.0, 0.0, 0.0),
            u1=0, u2=0, u3=0, ur1=None, ur2=None, ur3=None,
            bc_name="BC-Point1-Pinned",
            step_name=s_name)

        self.nbc.build(
            point_coords=(25, 0.0, 0.0),
            u1=None, u2=0, u3=0, ur1=None, ur2=None, ur3=None,
            bc_name="BC-Point2-YZ-Fixed",
            step_name=s_name)

        self.nbc.build(
            point_coords=(0.0, 0.0, self.comprimento),
            u1=None, u2=0, u3=None, ur1=None, ur2=None, ur3=None,
            bc_name="BC-Point3-Y-Fixed",
            step_name=s_name)

        self.nbc.build(
            point_coords=(25, 0.0, self.comprimento),
            u1=None, u2=0, u3=None, ur1=None, ur2=None, ur3=None,
            bc_name="BC-Point4-Y-Fixed",
            step_name=s_name)

        print("Boundary conditions applied to all specified points in step '{}'.".format(self.step_name))

    def mesh_tree(self):
        # Offset específico da geometria IV
        ofs = float(25 - self.largura) / 2

        # Usando as coordenadas carregadas no __init__
        cord0 = ofs
        cord1 = ofs + self.cord1
        cord2 = ofs + self.cord2
        cord3 = ofs + self.cord3
        cordL = float(ofs + self.largura)

        # Partições YZ (Cortes verticais ao longo de X)
        self._cut.coord = cord0
        self._cut.set()
        self._cut.coord = cord1
        self._cut.set()
        self._cut.coord = cord2
        self._cut.set()
        self._cut.coord = cord3
        self._cut.set()
        self._cut.coord = cordL
        self._cut.set()

        ofs2 = 2
        self._cut.coord = cordL + ofs2
        self._cut.set()
        self._cut.coord = cord0 - ofs2
        self._cut.set()

        # Partições XZ (Cortes horizontais ao longo de Y)
        cordY = 10
        self._cutY.coord = cordY
        self._cutY.set()
        self._cutY.coord = cordY - ofs2
        self._cutY.set()

        # Sets de Arestas (Mantidos da lógica original IV)
        self._edge.set(name='Edge_Set_1', xMin=ofs, xMax=cord1, yMin=cordY - ofs2)
        self._edge.set(name='Edge_Set_2', xMin=cord2, xMax=cord3, yMin=cordY - ofs2)
        self._edge.set(name='Edge_Set_3', xMin=cord3, xMax=cordL, yMin=cordY - ofs2)
        self._edge.set(name='Edge_Set_4', xMin=cord1, xMax=cord2, yMin=cordY - ofs2)

        self._edge.set(name='Edge_bdr_1', xMax=0.1)
        self._edge.set(name='Edge_bdr_2', xMin=25 - 0.1)
        self._edge.set(name='Edge_bdr_3L', yMax=0.1, xMax=cord0)
        self._edge.set(name='Edge_bdr_3R', yMax=0.1, xMin=cordL)
        self._edge.set(name='Edge_bdr_3C', yMax=0.1, xMin=cord0, xMax=cordL)
        self._edge.set(name='Edge_bdr_3C2', yMax=0.1, xMin=cord1, xMax=cord2)

        self._edge.set(name='Edge_swp_1',
                       xMin=cord0 - ofs2, xMax=cordL + ofs2,
                       yMin=cordY - ofs2, yMax=cordY)
        self._edge.set(name='Edge_swp_2',
                       xMin=cord0 - ofs2, xMax=cordL + ofs2,
                       yMin=0, yMax=cordY - ofs2)

        # Sets de Células Originais (Mantidos para lógica de Mesh Sweep)
        self._cell.set(name='Cell_Sweep_1',
                       xMin=cord0 - ofs2, xMax=cordL + ofs2,
                       yMin=cordY - ofs2, yMax=cordY)
        self._cell.set(name='Cell_Sweep_2',
                       xMin=cord0 - ofs2, xMax=cordL + ofs2,
                       yMax=cordY - ofs2)

        # -------------------------------------------------------------
        # NOVOS SETS DE CÉLULAS (Lógica trazida do sim.py)
        # Define regiões para Shell vs Solid baseadas nos cortes realizados
        # Ajustado para usar 'ofs' pois a peça está centralizada em 25
        # -------------------------------------------------------------
        self._cell.set(name='SHL_Rgn_1',
                       xMin=cord0, xMax=cord1, yMin=0)  # Região Esquerda

        self._cell.set(name='SLD_Rgn_2',
                       xMin=cord1, xMax=cord2, yMin=0)  # Miolo Sólido

        self._cell.set(name='Base1',
                       xMax=cord0, yMax=cordY)  # Miolo Sólido
        self._cell.set(name='Base2',
                       xMin=cordL, yMax=cordY)  # Miolo Sólido

        self._cell.set(name='SHL_Rgn_2',
                       xMin=cord2, xMax=cord3, yMin=0)  # Região Direita (Opcional/Transição)

        self._cell.set(name='SHL_Rgn_3',
                       xMin=cord3, xMax=cordL, yMin=0)  # Região Direita Extrema

        # -------------------------------------------------------------
        # SEMENTES DE MALHA
        # -------------------------------------------------------------
        self._mesher_seed.mesh(edge_set_name='Edge_Set_1', num_elements=5)
        self._mesher_seed.mesh(edge_set_name='Edge_Set_3', num_elements=1)
        self._mesher_seed.mesh(edge_set_name='Edge_bdr_1', num_elements=10)
        self._mesher_seed.mesh(edge_set_name='Edge_bdr_2', num_elements=10)
        self._mesher_seed.mesh(edge_set_name='Edge_bdr_3R', num_elements=5)
        self._mesher_seed.mesh(edge_set_name='Edge_bdr_3L', num_elements=5)
        self._mesher_seed.mesh(edge_set_name='Edge_bdr_3C', num_elements=1)

        self._mesher_seed.mesh(edge_set_name='Edge_swp_1', num_elements=30)
        self._mesher_seed.mesh(edge_set_name='Edge_swp_2', num_elements=30)

        self._mesher_sweep.set(cell_set_name='Cell_Sweep_1')
        self._mesher_sweep.set(cell_set_name='Cell_Sweep_2')

        self._mesher_bias.mesh(
            edge_set_name='Edge_Set_2',
            maxS=0.014, minS=0.010,
            method=SINGLE, flip=True)

        self._mesher_bias.mesh(
            edge_set_name='Edge_Set_4',
            maxS=0.20, minS=0.014,
            method=DOUBLE)

        self._mesher_seed.mesh(edge_set_name='Edge_bdr_3C2', num_elements=5)

        self._mesher.mesh_size = 0.45
        self._mesher.mesh()

    def _create_steps(self):
        """
        """
        previous = 'Initial'
        for s in (self.step_name1, self.step_name2):
            stepper = StepSetter()
            self.propagate_to(stepper)

            stepper.step_name = s
            stepper.initialInc = self.initialInc
            stepper.maxInc = self.maxInc
            stepper.maxNumInc = self.maxNumInc
            stepper.minInc = self.minInc
            stepper.nlgeom = self.nlgeom
            stepper.time = self.time
            stepper.previous = previous

            stepper.create()
            previous = s

    def set_boundary_conditions(self, model_change=True):

        byy = self.BCBelowSetter

        y_cut = 4 / 8

        byy.y_cutoff = y_cut
        byy.remove = True
        byy.remove_step = self.step_name2
        byy.set()

        if model_change:
            self.modelChange()
        else:
            self.logger.info("Model change for material removal is skipped.")

    def run_extended_analysis(self):
        """

        """

        self.logger.info("Starting extended analysis workflow")

        self.logger.info("Creating material and section")
        # ATUALIZAÇÃO: Material atualizado para 141000.0 (sim.py)
        self._material.material(
            self.mat_name, 141000.0, 0.3)

        # Criação da Instância primeiro (para ter a peça disponível para Sets)
        self.logger.info("Creating instance")
        self._instance.create()

        # Roda mesh_tree para gerar particionamento e sets
        self.mesh_tree()

        # -------------------------------------------------------------
        # DEFINIÇÃO DE SEÇÕES HÍBRIDAS (Copiado lógica do sim.py)
        # -------------------------------------------------------------

        # 1. Seção Sólida Central
        self._section.create(
            self.mat_name, 'SLD_Rgn_2', self.section_name+"1")
        self._section.create(
            self.mat_name, 'Base1', self.section_name+"2")
        self._section.create(
            self.mat_name, 'Base2', self.section_name+"3")

        # 2. Seção Shell Esquerda (Thickness = cord1)
        self._section.create(
            self.mat_name, 'SHL_Rgn_1', self.section_name + "Shell1",
            False, self.cord1, 11)

        # Cálculos de espessura (considerando o offset relativo à largura total 4)
        # Nota: cord2 e cord3 são relativos à largura de 4mm
        shl_rgn_l3_thickness = self.largura - self.cord3
        shl_rgn_32_thickness = self.cord3 - self.cord2

        # 3. Seções Shell Direita
        self._section.create(
            self.mat_name, 'SHL_Rgn_2', self.section_name + "Shell2",
            False, shl_rgn_l3_thickness,
            11)  # Atenção aqui: verifique se Shell2 corresponde ao Rgn_2 ou 3 na lógica original

        # No sim.py: Rgn_2 usa l3_thickness e Rgn_3 usa 32_thickness. Seguirei o sim.py:
        # Mas os nomes das regiões lá parecem invertidos com os índices.
        # Vou aplicar conforme sim.py: 'SHL_Rgn_2' -> thickness(largura-cord3)

        self._section.create(
            self.mat_name, 'SHL_Rgn_3', self.section_name + "Shell3",
            False, shl_rgn_32_thickness, 11)

        # -------------------------------------------------------------
        # ATRIBUIÇÃO DE ELEMENTOS (Continuum Shell)
        # -------------------------------------------------------------
        self._mesher_sc8r.set('SHL_Rgn_1')
        self._mesher_sc8r.set('SHL_Rgn_2')
        self._mesher_sc8r.set('SHL_Rgn_3')

        # Regenera a malha para aplicar os novos tipos de elemento
        self.t_part.generateMesh()

        self.logger.info("Creating analysis steps")
        self._create_steps()

        self.logger.info("Setting boundary conditions")
        self.set_boundary_conditions(model_change=False)

        self.points(self.step_name2)

        self.logger.info("Creating and moving job file")
        inp_path = self._job.create_and_move_job()

        self.logger.info("INP file created at: {}".format(inp_path))
        self.logger.info("Extended analysis completed successfully")
        """
        """


if __name__ == '__main__':

    from _modules import ParametersGetter  # → utilitary/_get_parameters.py

    parameters = ParametersGetter()

    _list_disk = [r"Z:", r"T:", r"V:"]
    _part_server = r"02_SHK\05_dgl_gm\06_Simulation\_out"
    for item in _list_disk:
        guess_path = os.path.join(item, _part_server)
        if os.path.isdir(guess_path):
            base_dir = guess_path
            break

    _out = os.path.join(base_dir)
    if not os.path.isdir(_out):
        os.makedirs(_out)

    analysis = ContourAnalysisExtended(
        mesh=parameters.get('mesh_size', 0.8),
        comprimento=70,
        output=_out,
        initialInc=1,
        maxInc=1.0,
        maxNumInc=1,
        minInc=1,
        nlgeom=parameters.get('nlgeom', OFF),
        time=1.0
    )
    analysis.run_extended_analysis()