# -*- coding: utf-8 -*-
"""
"""

import os, sys, inspect

sys.dont_write_bytecode = True
_here      = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
_parent_1  = os.path.dirname(_here)
_parent_2  = os.path.dirname(_parent_1)
for p in (_here, _parent_1, _parent_2):
    if p not in sys.path:
        sys.path.append(p)

from _modules import *          #  ≤  todas as “service-classes”
from _u_json import JsonReader

class ContourAnalysisExtended(LoggerMixin,object):
    """
    """

    def __init__(self, mesh, comprimento, output,
                 initialInc, maxInc, maxNumInc, minInc,
                 nlgeom, time,
                 step_name      = "Material-Removal",
                 mat_name       = 'WORK_PIECE_MATERIAL',
                 section_name   = 'WORK_PIECE_Section'):
        
        super(ContourAnalysisExtended, self).__init__()

        # ❶  ARMAZENAR PARÂMETROS GERAIS
        self.mesh_size      = mesh
        self.comprimento    = comprimento
        self.output_dir     = output

        # step / material / section
        self.step_name      = step_name
        self.mat_name       = mat_name
        self.section_name   = section_name

        # step-params
        self.initialInc     = initialInc
        self.maxInc         = maxInc
        self.maxNumInc      = maxNumInc
        self.minInc         = minInc
        self.nlgeom         = nlgeom
        self.time           = time

        self.step_name1     = 'BC-Removal'
        self.step_name2     = 'BC-Removal_Nodes'

        _here            = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        par_dir          = os.path.join(_here,'params.json')
        self.reader      = JsonReader(par_dir)

        self.comprimento = 10#self.reader.load()['analysis']['comprimento']

        self.largura     = 4

        # ❷  GEOMETRIA (geometry/sim_two/_set_geometry2.py)
        self._geometry = GeometrySetterThree()
        self.model, self.t_part = self._geometry._geometry(
            depth   = self.comprimento,
            height  = 50)
        self.instance_name = self.t_part.name + '-1'

        self.bind_context(model           = self.model, 
                          t_part          = self.t_part, 
                          instance_name   = self.instance_name)
        


        # ❸  SERVICE-OBJECTS (core / assigment / geometry_setup …)
        self._stepper       = StepSetter()
        self._mesher        = MeshSetter()
        self._job           = JobSetter()
        self._material      = MaterialSetter()
        self._section       = SectionSetter()
        self._instance      = InstanceSetter()
        self._datum         = DatumSetter()
        # objetos “extended”
        self._plane_info    = PlaneGetter()
        self._datum_rm      = RemoveDatumSetter()
        self._region        = RemovalRegionSetter()
        self._set_creator   = SetSetter()
        self._node_bc       = NodeBCSetter()
        self._model_change  = ModelChangeSetter()
        self._shape         = ShapeGetterTwo()

        self._cut           = PartitionYZSetter()
        self._edge          = EdgeSetCreator()
        self._cell          = CellSetCreator()
        self._mesher_seed   = MeshSetterSeed()
        self._mesher_bias   = MeshSetterBias()
        self._mesher_sc8r   = MeshSetterSC8R()
        self.BCBelowSetter  = BCBelowSetter()

        self.nbc            = NodeBCBuilder()
        
        self.propagate_to(
            self._mesher, self._job, self._material, self._section,
            self._instance, self._datum, self._shape, self._cell,
            self._cut, self._edge, self._mesher_seed, self._mesher_bias,
            self.BCBelowSetter, self.nbc, self._node_bc, self._mesher_sc8r
        )

        self.cord1 = self.reader.load()['analysis']['geometry']['cord1']
        self.cord2 = self.reader.load()['analysis']['geometry']['cord2']
        self.cord3 = self.reader.load()['analysis']['geometry']['cord3']

    def points(self, s_name):
        """
        """

        self.nbc.build(
            point_coords    = (0.0, 0.0, 0.0),
            u1 = 0, u2 = 0, u3 = 0, ur1 = None, ur2 = None, ur3 = None,
            bc_name         = "BC-Point1-Pinned",
            step_name       = s_name)
        
        self.nbc.build(
            point_coords    = (self.largura, 0.0, 0.0),
            u1 = None, u2 = 0, u3 = 0, ur1 = None, ur2 = None, ur3 = None,  
            bc_name         = "BC-Point2-YZ-Fixed",
            step_name       = s_name)
        
        self.nbc.build(
            point_coords    =(0.0, 0.0, self.comprimento),
            u1 = None, u2 = 0, u3 = None, ur1 = None, ur2 = None, ur3 = None,
            bc_name         = "BC-Point3-Y-Fixed",
            step_name       = s_name)
        
        self.nbc.build(
            point_coords    = (self.largura, 0.0, self.comprimento),
            u1 = None, u2 = 0, u3 = None, ur1 = None, ur2 = None, ur3 = None,  
            bc_name         = "BC-Point4-Y-Fixed",
            step_name       = s_name)
        
        print("Boundary conditions applied to all specified points in step '{}'.".format(self.step_name))


    def mesh_tree(self):

        """
        """
        self._edge.set(name='Edge_Set_1', xMin=0,     xMax=self.cord1)
        self._edge.set(name='Edge_Set_2', xMin=self.cord2, xMax=self.cord3
                       )
        self._edge.set(name='Edge_Set_3', xMin=self.cord3, xMax=4)
        self._edge.set(name='Edge_Set_4', xMin=self.cord1, xMax=self.cord2)

        self._mesher_seed.mesh(edge_set_name='Edge_Set_1', num_elements=1)
        self._mesher_seed.mesh(edge_set_name='Edge_Set_2', num_elements=1)
        self._mesher_seed.mesh(edge_set_name='Edge_Set_3', num_elements=1)



        self._mesher_bias.mesh(
            edge_set_name='Edge_Set_4',
            maxS=0.2, minS=0.15, method=DOUBLE)

        self._mesher.mesh_size = 0.15 #self.reader.load()['analysis']['mesh_size']
        self._mesher.mesh()

    def _create_steps(self):
        """
        """
        previous = 'Initial'
        for s in (self.step_name1, self.step_name2):
            stepper = StepSetter()
            self.propagate_to(stepper)

            stepper.step_name  = s
            stepper.initialInc = self.initialInc
            stepper.maxInc     = self.maxInc
            stepper.maxNumInc  = self.maxNumInc
            stepper.minInc     = self.minInc
            stepper.nlgeom     = self.nlgeom
            stepper.time       = self.time
            stepper.previous   = previous

            stepper.create()
            previous = s

    def set_boundary_conditions(self, model_change=True):
        
        byy             = self.BCBelowSetter

        y_cut           = 4 / 8

        byy.y_cutoff    = y_cut
        byy.remove      = True
        byy.remove_step = self.step_name2
        byy.set()

        if model_change: self.modelChange()
        else: self.logger.info("Model change for material removal is skipped.")

    def set_symmetry_bc(self, face_position='X0'):
        """
        Aplica condição de simetria em uma face plana.
        face_position: 'X0' para face em X=0, 'Z0' para Z=0, etc.
        """
        self.logger.info("Applying symmetry BC at {}".format(face_position))

        # Tolerância para encontrar a face
        tol = 1e-4

        # Dimensões grandes para bounding box
        L = 1e6

        faces = None
        bc_type = None
        bc_name = 'Symmetry-BC-' + face_position

        # Lógica para encontrar a face e definir o tipo de simetria
        if face_position == 'X0':  # Face no plano YZ (Normal X)
            faces = self.t_part.faces.getByBoundingBox(
                xMin=-tol, xMax=tol, yMin=-L, yMax=L, zMin=-L, zMax=L
            )
            # Simetria X (U1=0, UR2=0, UR3=0)
            bc_func = self.model.XsymmBC

        elif face_position == 'Y0':  # Face no plano XZ (Normal Y)
            faces = self.t_part.faces.getByBoundingBox(
                xMin=-L, xMax=L, yMin=-tol, yMax=tol, zMin=-L, zMax=L
            )
            # Simetria Y (U2=0, UR1=0, UR3=0)
            bc_func = self.model.YsymmBC

        elif face_position == 'Z0':  # Face no plano XZ (Normal Y)
            faces = self.t_part.faces.getByBoundingBox(
                xMin=-L, xMax=L, yMin=-L, yMax=L, zMin=-tol, zMax=tol
            )
            bc_func = self.model.ZsymmBC

        # Cria o Set na PEÇA (Part)
        set_name = 'Set-Symmetry-' + face_position
        if len(faces) > 0:
            self.t_part.Set(faces=faces, name=set_name)

            # Recupera a região na INSTÂNCIA (Assembly) para aplicar a BC
            region = self.model.rootAssembly.instances[self.instance_name].sets[set_name]

            # Aplica a BC
            bc_func(
                name=bc_name,
                createStepName='Initial',
                region=region,
                localCsys=None
            )
            self.logger.info("Symmetry BC '{}' applied successfully.".format(bc_name))
        else:
            self.logger.warning("No faces found for symmetry at {}!".format(face_position))

    def run_extended_analysis(self):
        """
        Orquestra todo o processo de forma sequencial.
        """

        self.logger.info("Starting extended analysis workflow")

        self.logger.info("Creating material and section")
        self._material.material(
            self.mat_name, 141000.0, 0.3)

        self._cut.coord = self.cord1
        self._cut.set()
        self._cut.coord = self.cord2
        self._cut.set()
        self._cut.coord = self.cord3
        self._cut.set()

        self._cell.set(name='SHL_Rgn_1',
                       xMax=self.cord1)
        self._cell.set(name='SLD_Rgn_2',
                       xMin=self.cord1, xMax=self.cord2)
        self._cell.set(name='SHL_Rgn_2',
                       xMin=self.cord2, #xMax=self.cord3
                       )
        self._cell.set(name='SHL_Rgn_3',
                       xMin=self.cord3)

        self._section.create(
            self.mat_name, 'SLD_Rgn_2', self.section_name)

        self._section.create(
            self.mat_name, 'SHL_Rgn_1', self.section_name + "Shell1",
            False, self.cord1, 11)

        shl_rgn_2_thickness = self.largura - self.cord2

        shl_rgn_l3_thickness = self.largura - self.cord3
        shl_rgn_32_thickness = self.cord3 - self.cord2


        self._section.create(
            self.mat_name, 'SHL_Rgn_2', self.section_name + "Shell2",
            False, shl_rgn_l3_thickness, 11)
        self._section.create(
            self.mat_name, 'SHL_Rgn_3', self.section_name + "Shell3",
            False, shl_rgn_32_thickness, 11)


        self.logger.info("Creating instance")
        self._instance.create()

        #self.set_symmetry_bc(face_position='Z0')

        self.mesh_tree()

        self._mesher_sc8r.set('SHL_Rgn_1')
        self._mesher_sc8r.set('SHL_Rgn_2')
        self._mesher_sc8r.set('SHL_Rgn_3')

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

    from _modules import ParametersGetter   # → utilitary/_get_parameters.py
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
        mesh        = parameters.get('mesh_size', 0.8),
        comprimento = 10,
        output      = _out,
        initialInc  = 1,
        maxInc      = 1.0,
        maxNumInc   = 1,
        minInc      = 1,
        nlgeom      = parameters.get('nlgeom', OFF),
        time        = 1.0
    )
    analysis.run_extended_analysis()