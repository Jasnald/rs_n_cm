# -*- coding: utf-8 -*-

import os, sys, inspect, json, shutil
sys.dont_write_bytecode = True

current_dir = os.path.dirname(
            os.path.abspath(
            inspect.getfile(
            inspect.currentframe())))
dir_1 = os.path.dirname(current_dir)
dir_2 = os.path.dirname(dir_1)
dir_3 = os.path.dirname(dir_2)

sys.path.append(current_dir)
sys.path.append(dir_1)
sys.path.append(dir_2)
sys.path.append(dir_3)

from utils import *
from _modules import *


class ContourAnalysis(object):
    """
    Automatiza a criação, malha e geração de .inp para uma peça em T (Contour Method).
    Agora delega as responsabilidades para classes auxiliares injetadas/internas.

    Parâmetros de __init__ mantidos para compatibilidade.
    """

    def __init__(self, mesh, comprimento, output,
                 initialInc,
                 maxInc,
                 maxNumInc,
                 minInc,
                 nlgeom,
                 time,
                 step_name="Step-1", job_name="ContourMethodAnalysis",
                 mat_name='WORK_PIECE_MATERIAL', section_name='WORK_PIECE_Section'):
        # Armazenar parâmetros
        self.mesh_size   = mesh
        self.comprimento = comprimento
        self.output_dir  = output

        self.step_name   = step_name
        self.job_name    = job_name
        self.mat_name    = mat_name
        self.section_name= section_name

        # Step params
        self.initialInc  = initialInc
        self.maxInc      = maxInc
        self.maxNumInc   = maxNumInc
        self.minInc      = minInc
        self.nlgeom      = nlgeom
        self.time        = time

        # Logger
        self.logger = setup_logger(self.__class__.__name__)
        self.logger.info("ContourAnalysis inicializada.")

        # Criar geometria (via GeometrySetter)
        self._geometry = GeometrySetter()
        self.model, self.t_part = self._geometry._geometry(depth=self.comprimento)
        self.instance_name = self.t_part.name + '-1'

        # Instanciar serviços (configuração será feita quando usados)
        self._stepper     = StepSetter()
        self._material    = MaterialSetter()
        self._section     = SectionSetter()
        self._instance    = InstanceSetter()
        self._mesher      = MeshSetter()
        self._job         = JobSetter()
        self._partitioner = PartitionSetter()
        self._datum       = DatumSetter()
        self._shape       = ShapeGetterI()
        self._nodes       = NodeSetCreator()
        self._bcset       = BCSet()

    # Wrapper utilitário
    def get_t_shape(self):  
        return self._shape.t_shape()

    def partition(self):
        return self.partition_geometry()

    # Step
    def create_static_step(self): 
        # Configurar stepper apenas quando necessário
        self._stepper.model      = self.model
        self._stepper.step_name  = self.step_name
        self._stepper.initialInc = self.initialInc
        self._stepper.maxInc     = self.maxInc
        self._stepper.maxNumInc  = self.maxNumInc
        self._stepper.minInc     = self.minInc
        self._stepper.nlgeom     = self.nlgeom
        self._stepper.time       = self.time
        self._stepper.previous   = 'Initial'  # Add this line
        
        self._stepper.create()

    # Instância
    def create_instance(self):
        # Configurar instance apenas quando necessário
        self._instance.model         = self.model
        self._instance.t_part        = self.t_part
        self._instance.instance_name = self.instance_name
        
        return self._instance.create()

    # Datum helper (compat)
    def datum_planes_cnp(
            self, coord, 
            datum_name       = None, 
            coordinate_plane = XZPLANE, 
            create_partition = True):
        # Configurar datum apenas quando necessário
        self._datum.t_part = self.t_part
        
        self._datum.create_part(
            coord            = coord, 
            datum_name       = datum_name,                          
            coordinate_plane = coordinate_plane, 
            create_partition = create_partition)

    # Particionamento
    def partition_geometry(self):
        # Configurar partitioner apenas quando necessário
        self._partitioner._datum.t_part = self.t_part
        
        self._partitioner.partition()

    # Material/Seção (wrappers)
    def c_material(self, mat_name, E_Modulus, P_ratio):
        # Configurar material apenas quando necessário
        self._material.model = self.model
        
        self._material.material(mat_name, E_Modulus, P_ratio)

    def c_section(self, mat_name, bounds, section_name):
        # Configurar section apenas quando necessário
        self._section.model  = self.model
        self._section.t_part = self.t_part
        if hasattr(self._section, "_section"):
            self._section._section.t_part = self.t_part
            
        self._section.create(mat_name, bounds, section_name)


    # Malha
    def mesh_part(self):
        # Configurar mesher apenas quando necessário
        self._mesher.t_part    = self.t_part
        self._mesher.mesh_size = self.mesh_size

        self._mesher.mesh()

    # Job
    def create_and_move_job(self):
        # Configurar job apenas quando necessário
        self._job.mesh_size   = self.mesh_size
        self._job.comprimento = self.comprimento
        self._job.model       = self.model
        self._job.output_dir  = self.output_dir
        
        return self._job.create_and_move_job()

    # Pipeline principal
    def run_analysis(self):
        self.create_static_step()

        # Não altere E e nu (necessário por compatibilidade com INP_BC_Final.py)
        self.c_material(
            self.mat_name, 
            210000.0, 0.3)
        
        self.c_section(
            self.mat_name, 
            None, 
            self.section_name)
        
        self.create_instance()

        self.partition()

        self.mesh_part()

        self._nodes.t_part = self.t_part
        self._nodes.set(
            name='Set_Enc', zMin=self.comprimento)
        self._nodes.set(
            name='Set_Disp', zMax=0)

        self._bcset.model         = self.model
        self._bcset.instance_name = self.instance_name

        self._bcset.set(
            set_name  = 'Set_Enc',       # nome do set de nós
            bc_name   = 'Enc_Set_Enc',   # nome da BC (opcional)
            step_name = 'Initial'        # passo onde a BC é criada
        )


        inp_path = self.create_and_move_job()
        print("Processo concluído. Arquivo .inp localizado em:", inp_path)
        return inp_path


# Execução direta, semelhante ao script original
if __name__ == "__main__":

    current_dir = os.path.dirname(
                os.path.abspath(
                inspect.getfile(
                inspect.currentframe())))

    dir_1 = os.path.dirname(current_dir)
    dir_2 = os.path.dirname(dir_1)
    dir_3 = os.path.dirname(dir_2)
    CONFIG_PATH = os.path.join(dir_3, "data", "config.json")
    
    from _modules import *  
    

    parameters = ParametersGetter()


    with open(CONFIG_PATH, "r") as f: config_data = json.load(f)

    work_dir = config_data.get("directories", {}).get("work_directory", "C:/Simulation4")
    output_dir = os.path.join(work_dir, "Contour_Method")


    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    analysis = ContourAnalysis(
        mesh        = parameters.get('mesh_size'),
        comprimento = parameters.get('comprimento'),
        output      = output_dir,
        initialInc  = parameters.get('initialInc'),
        maxInc      = parameters.get('maxInc'),
        maxNumInc   = parameters.get('maxNumInc'),
        minInc      = parameters.get('minInc'),
        nlgeom      = parameters.get('nlgeom'),
        time        = parameters.get('time')
    )
    analysis.run_analysis()