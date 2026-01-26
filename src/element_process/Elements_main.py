
"""
Elements_main.py
What it does:
Automates the workflow for processing Abaqus mesh input files (*.inp) by extracting nodes, generating residual stress fields, and interpolating element stresses. For each mesh file matching the pattern 'Mesh-*--Lenth-*.inp', it creates a dedicated output directory and runs a sequence of processing steps, logging progress and errors throughout. This script is intended to be run as a standalone module or imported for batch processing of simulation data.

Example of use:
    from Modules_python.Elements_main import Nodes_main
    Nodes_main(base_dir="C:/path/to/meshes")
"""

import os
import glob
from .s1_Ele_Extractor       import run_element_extractor
from .s2_RE_Field            import main as generate_stress
from .s3_RE_Interpolator     import ElementTensionInterpolator
from utils                  import *

# Configure the logger for this module.
logger = setup_logger(__name__, clear=True)

def Nodes_main(base_dir=None, use_s1=True, use_s2=True, use_s3=True):
    """
    Nodes_main / (function)
    What it does:
    Main workflow function for batch processing of Abaqus mesh input files. For each file matching the pattern 'Mesh-*--Lenth-*.inp' in the specified base directory, it:
      1. Extracts nodes using run_element_extractor (if use_s1 is True)
      2. Generates a residual stress field using generate_stress (if use_s2 is True)
      3. Interpolates element stresses using ElementTensionInterpolator (if use_s3 is True)
    Creates a dedicated output directory for each mesh file and logs all steps and errors.
    Parameters:
        base_dir (str, optional): Directory to search for mesh files. Defaults to current working directory.
        use_s1 (bool): Whether to run node extraction. Defaults to True.
        use_s2 (bool): Whether to generate residual stress field. Defaults to True.
        use_s3 (bool): Whether to interpolate stresses. Defaults to True.
    """
    if base_dir is None:
        base_dir = os.getcwd()
    
    # Buscar todos os arquivos .inp com o padrão "Mesh-*--Lenth-*.inp"
    inp_pattern = os.path.join(base_dir, "Mesh-*--Lenth-*.inp")
    inp_files = glob.glob(inp_pattern)
    
    if not inp_files:
        logger.error(f"No .inp file found with pattern 'Mesh-*--Lenth-*.inp' in: {base_dir}")
        return
    
    logger.info(f"Found {len(inp_files)} .inp files to process:")
    for inp_file in inp_files:
        logger.info(f"  - {os.path.basename(inp_file)}")
    logger.info("")
    
    # Processar cada arquivo .inp
    for inp_file in inp_files:
        inp_filename = os.path.basename(inp_file)
        logger.info("="*45 + "\n" + "="*10 + f"  PROCESSING: {inp_filename}" + "\n"+ "="*45 + "\n")
        
        # Criar diretório de output específico para este arquivo
        base_name = os.path.splitext(inp_filename)[0]
        output_dir = os.path.join(base_dir, 'Output', base_name)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Passo 1: Extrair nós do Abaqus
            logger.info("="*10 + " Extracting Abaqus nodes..." + "\n")
            if use_s1:
                run_element_extractor(inp_file, output_dir)
            else:
                logger.info("Node extraction disabled. Skipping this step.\n")
            
            # Passo 2: Gerar campo de tensão residual
            logger.info("="*10 + " Generating residual stress field..." + "\n")
            if use_s2:
                generate_stress(output_dir)
            else:
                logger.info("Residual stress field generation disabled. Skipping this step.\n")
            
            # Passo 3: Interpolar tensões no campo original
            logger.info("="*10 + " Interpolating stresses..." + "\n")
            if use_s3:
                interpolator = ElementTensionInterpolator(output_dir)
                interpolator.Class_runner()
            else:
                logger.info("Stress interpolation disabled. Skipping this step.\n")
            
            logger.info(f"✓ Processing completed for: {inp_filename}")
            
        except Exception as e:
            logger.error(f"✗ Error while processing {inp_filename}: {str(e)}")
            continue
    
    logger.info("="*45 + "\n" + "="*10 + " ALL PROCESSES COMPLETED!" + "\n" + "="*45 + "\n") 



if __name__ == "__main__":
    Nodes_main(base_dir=os.getcwd())