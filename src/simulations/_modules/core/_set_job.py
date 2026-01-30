# -*- coding: utf-8 -*-
# _set_job.py

from ..utilitary import *
from ..imports import *

class JobSetter(LoggerMixin):

    def create_and_move_job(self):
        """
        create_and_move_job / (method)
        What it does:
        Creates an Abaqus job, writes the .inp file with a name based on mesh and length, and moves it to the specified output directory.
        """
        # Define o nome do Job a partir dos parâmetros da análise
        job_name = "Mesh-{0}--Lenth-{1}".format(
            self.mesh_size, 
            self.comprimento)
        job_name = job_name.replace('.', '_')
        self.job_name = job_name  # Atualiza a propriedade, se for utilizado em outros métodos

        # Cria o job utilizando o nome definido
        job = mdb.Job(
            name    = job_name, 
            model   = self.model.name)
        job.writeInput()  # Gera o arquivo .inp
        
        # Define os caminhos dos arquivos
        inp_original = job_name + ".inp"
        inp_target   = os.path.join(
            self.output_dir, 
            inp_original)
        
        # Se o arquivo de destino já existir, remove-o
        if os.path.exists(inp_target): os.remove(inp_target)
        
        try:    shutil.move(inp_original, inp_target)
        except  Exception as e: 
                print("Erro ao mover o arquivo: {}".format(e))
        else:   print("Arquivo movido com sucesso para:", inp_target)
        
        return inp_target
