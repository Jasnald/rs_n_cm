
"""
s3_RE_Interpolator.py
What it does:
Manages the interpolation of stress fields between finite element meshes. Loads mesh and stress data, performs coordinate matching, and interpolates stress components using linear and nearest-neighbor methods. Generates output files compatible with Abaqus for simulation or post-processing. Useful for transferring residual stress fields between meshes of different resolutions or topologies.

Example of use:
    from Modules_python.s3_RE_Interpolator import ElementTensionInterpolator
    interpolator = ElementTensionInterpolator(output_dir="./Output/Mesh-0_98--Lenth-50")
    interpolator.Class_runner()
"""

import numpy as np
import os
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
import pandas as pd


class ElementTensionInterpolator:
    """
    ElementTensionInterpolator / (class)
    What it does:
    Manages the interpolation of stress fields between finite element meshes. Loads mesh and stress data, matches coordinates, and interpolates stress components using linear and nearest-neighbor methods. Generates output files compatible with Abaqus.
    """
    
    def __init__(self, output_dir):
        """
        __init__ / (method)
        What it does:
        Initializes the element tension interpolator with the specified output directory. Sets up internal variables for mesh and stress data.
        Parameters:
            output_dir (str): Directory where files are stored and results will be saved.
        """
        self.output_dir = output_dir
        self.target_elements = None
        self.target_coords = None
        self.target_types = None
        self.source_points = None
        self.source_coords = None
        self.source_tensions = None
        self.target_tensions = None
        
    def load_abaqus_elements(self, elements_file=None):
        """
        load_abaqus_elements / (method)
        What it does:
        Loads the original Abaqus mesh elements from a file, extracting element IDs, centroid coordinates, and types. Supports both pandas and manual parsing for robustness. Returns True if successful, False otherwise.
        Parameters:
            elements_file (str, optional): Path to the elements file. If None, attempts to find automatically.
        Returns:
            bool: True if elements were loaded successfully, False otherwise.
        """
        if elements_file is None:
            elements_file = self._find_elements_file()
            if elements_file is None:
                print("Arquivo de elementos não encontrado.")
                return False
        
        elements_file_path = os.path.join(self.output_dir, elements_file)
        print(f"Carregando elementos do arquivo: {elements_file_path}")
        
        try:
            # Tenta carregar usando pandas para melhor desempenho
            df = pd.read_csv(elements_file_path, sep='\t', header=0)
            self.target_elements = df['Element'].values
            self.target_coords = df[['X_center', 'Y_center', 'Z_center']].values
            if 'Type' in df.columns:
                self.target_types = df['Type'].values
            return True
        except Exception:
            # Fallback para o método manual se pandas falhar
            elements = []
            coords = []
            element_types = []
            
            try:
                with open(elements_file_path, 'r') as f:
                    header = f.readline().strip()
                    columns = header.split('\t')
                    has_type = 'Type' in columns
                    x_col = columns.index('X_center') if 'X_center' in columns else 1
                    y_col = columns.index('Y_center') if 'Y_center' in columns else 2
                    z_col = columns.index('Z_center') if 'Z_center' in columns else 3
                    type_col = columns.index('Type') if has_type else -1
                    
                    for line in f:
                        line = line.strip()
                        if line:
                            values = line.replace(',', ' ').split('\t')
                            if len(values) >= 4:
                                try:
                                    element_id = int(values[0])
                                    x = float(values[x_col])
                                    y = float(values[y_col])
                                    z = float(values[z_col])
                                    elements.append(element_id)
                                    coords.append([x, y, z])
                                    if has_type:
                                        element_types.append(values[type_col])
                                except ValueError:
                                    continue
            except Exception as e:
                print(f"Erro ao carregar arquivo de elementos: {e}")
                return False
            
            if not elements:
                print("Nenhum elemento encontrado no arquivo.")
                return False
                
            self.target_elements = np.array(elements)
            self.target_coords = np.array(coords)
            if element_types:
                self.target_types = np.array(element_types)
            return True
    
    def load_tension_field(self, tension_file=None):
        """
        load_tension_field / (method)
        What it does:
        Loads the residual stress field from a file, supporting both Abaqus and cylindrical formats. Extracts stress components and coordinates, converting to cartesian if needed. Returns True if successful, False otherwise.
        Parameters:
            tension_file (str, optional): Path to the tension file. If None, attempts to find automatically.
        Returns:
            bool: True if the stress field was loaded successfully, False otherwise.
        """
        if tension_file is None:
            tension_file = self._find_tension_file()
            if tension_file is None:
                print("Arquivo de tensões não encontrado.")
                return False
        
        tension_file_path = os.path.join(self.output_dir, tension_file)
        print(f"Carregando tensões do arquivo: {tension_file_path}")
        
        points = []
        coordinates = []
        tensions = []
        
        try:
            with open(tension_file_path, 'r') as f:
                lines = f.readlines()
                
                # Identifica o formato do arquivo
                is_abaqus_format = any("*INITIAL CONDITIONS" in line for line in lines[:5])
                
                # Pula linhas de cabeçalho
                start_idx = 0
                for i, line in enumerate(lines):
                    if "**" in line or "*" in line or "ID" in line or "Element" in line:
                        start_idx = i + 1
                    elif i > 5:  # Limita a busca às primeiras linhas
                        break
                
                # Processa as linhas de dados
                for line in lines[start_idx:]:
                    line = line.strip()
                    if not line:
                        continue
                        
                    values = line.replace(',', ' ').split()
                    
                    if is_abaqus_format:
                        # Formato Abaqus: Id, S11, S22, S33, S12, S13, S23
                        if len(values) >= 7:
                            try:
                                point_id = int(values[0])
                                s11 = float(values[1])
                                s22 = float(values[2])
                                s33 = float(values[3])
                                s12 = float(values[4])
                                s13 = float(values[5])
                                s23 = float(values[6])
                                
                                points.append(point_id)
                                tensions.append([s11, s22, s33, s12, s13, s23])
                            except ValueError:
                                continue
                    else:
                        # Formato cilíndrico: Id, X, Y, Z, R, Theta, Sr, St, Sz, Trt, Trz, Ttz
                        if len(values) >= 12:
                            try:
                                point_id = int(values[0])
                                x = float(values[1])
                                y = float(values[2])
                                z = float(values[3])
                                sigma_r = float(values[6])
                                sigma_t = float(values[7])
                                sigma_z = float(values[8])
                                tau_rt = float(values[9])
                                tau_rz = float(values[10])
                                tau_tz = float(values[11])
                                
                                # Converter tensões cilíndricas para cartesianas
                                theta = float(values[5])
                                s11 = sigma_r * np.cos(theta)**2 + sigma_t * np.sin(theta)**2
                                s22 = sigma_r * np.sin(theta)**2 + sigma_t * np.cos(theta)**2
                                s33 = sigma_z
                                s12 = (sigma_r - sigma_t) * np.sin(theta) * np.cos(theta)
                                s13 = tau_rz * np.cos(theta) - tau_tz * np.sin(theta)
                                s23 = tau_rz * np.sin(theta) + tau_tz * np.cos(theta)
                                
                                points.append(point_id)
                                coordinates.append([x, y, z])
                                tensions.append([s11, s22, s33, s12, s13, s23])
                            except ValueError:
                                continue
        except Exception as e:
            print(f"Erro ao carregar arquivo de tensões: {e}")
            return False
        
        if not points:
            print("Nenhum ponto de tensão encontrado no arquivo.")
            return False
            
        self.source_points = np.array(points)
        self.source_tensions = np.array(tensions)
        
        # Se coordenadas não estiverem no arquivo de tensões, tenta associar com os elementos
        if not coordinates:
            if self.target_elements is None:
                print("Coordenadas não encontradas e malha alvo não carregada.")
                return False
                
            print("Coordenadas não encontradas no arquivo de tensões.")
            print("Tentando associar IDs dos pontos com elementos...")
            
            if self._match_points_with_elements():
                return True
            else:
                return False
        else:
            self.source_coords = np.array(coordinates)
            return True
    
    def _match_points_with_elements(self):
        """
        _match_points_with_elements / (method)
        What it does:
        Associates stress points with loaded mesh elements when coordinates are not available in the stress file, matching by element ID. Returns True if matches are found, False otherwise.
        Returns:
            bool: True if matches were found, False otherwise.
        """
        # Tenta encontrar correspondências entre pontos_fonte e elementos_alvo
        matches = []
        coords_list = []
        valid_tensions = []
        
        for i, point_id in enumerate(self.source_points):
            element_indices = np.where(self.target_elements == point_id)[0]
            if element_indices.size > 0:
                idx = element_indices[0]
                matches.append(idx)
                coords_list.append(self.target_coords[idx])
                valid_tensions.append(self.source_tensions[i])
        
        if matches:
            print(f"Encontradas {len(matches)} correspondências entre pontos e elementos.")
            self.source_coords = np.array(coords_list)
            self.source_tensions = np.array(valid_tensions)
            return True
        else:
            print("Nenhuma correspondência encontrada. Impossível interpolar.")
            return False
    
    def interpolate_tensions(self):
        """
        interpolate_tensions / (method)
        What it does:
        Interpolates stress components from the source mesh to the target mesh using linear and nearest-neighbor methods. Handles insufficient data and fallback strategies. Returns True if interpolation is successful, False otherwise.
        Returns:
            bool: True if interpolation was successful, False otherwise.
        """
        if self.source_coords is None or self.target_coords is None or self.source_tensions is None:
            print("Dados insuficientes para interpolação.")
            return False
            
        # Verifica se há pontos suficientes para interpolação
        if len(self.source_coords) < 4:  # Mínimo necessário para interpolação linear 3D
            print("Poucos pontos para interpolação. Usando valores médios.")
            self.target_tensions = np.tile(np.mean(self.source_tensions, axis=0), 
                                         (len(self.target_coords), 1))
            return True
            
        # Componentes de tensão
        components = ['S11', 'S22', 'S33', 'S12', 'S13', 'S23']
        self.target_tensions = np.zeros((len(self.target_coords), 6))
        
        # Para cada componente de tensão, criar um interpolador
        for i in range(6):
            values = self.source_tensions[:, i]
            
            try:
                # Tentar interpolação linear
                interpolator = LinearNDInterpolator(self.source_coords, values)
                interpolated_tensions = interpolator(self.target_coords)
                
                # Se houver valores NaN, usar o interpolador de vizinho mais próximo
                nan_mask = np.isnan(interpolated_tensions)
                if np.any(nan_mask):
                    nn_interpolator = NearestNDInterpolator(self.source_coords, values)
                    interpolated_tensions[nan_mask] = nn_interpolator(self.target_coords[nan_mask])
                    
                self.target_tensions[:, i] = interpolated_tensions
            except Exception as e:
                print(f"Erro na interpolação da componente {components[i]}: {e}")
                try:
                    # Fallback para interpolador de vizinho mais próximo
                    nn_interpolator = NearestNDInterpolator(self.source_coords, values)
                    self.target_tensions[:, i] = nn_interpolator(self.target_coords)
                except Exception as e2:
                    print(f"Erro no fallback para vizinho mais próximo: {e2}")
                    # Em último caso, use valores médios
                    self.target_tensions[:, i] = np.mean(values) * np.ones(len(self.target_coords))
        
        print(f"Interpolação concluída para {len(self.target_coords)} elementos.")
        return True
    
    def generate_interpolated_tension_file(self, output_file=None):
        """
        generate_interpolated_tension_file / (method)
        What it does:
        Generates a file with the interpolated element stresses in Abaqus format. Writes all stress components for each element. Returns the path to the generated file or None if failed.
        Parameters:
            output_file (str, optional): Name of the output file. If None, uses a default name.
        Returns:
            str: Path to the generated file, or None if failed.
        """
        if self.target_elements is None or self.target_tensions is None:
            print("Dados insuficientes para gerar arquivo de tensões.")
            return None
            
        if output_file is None:
            output_file = "interpoladed_element_stresses.txt"
            
        output_path = os.path.join(self.output_dir, output_file)
        
        try:
            with open(output_path, 'w') as f:
                # Escreve cabeçalho
                f.write("*INITIAL CONDITIONS, TYPE=STRESS\n")
                
                # Escreve dados
                for i in range(len(self.target_elements)):
                    element = self.target_elements[i]
                    s11, s22, s33, s12, s13, s23 = self.target_tensions[i]
                    line = f"{int(element)}, {s11:.8f}, {s22:.8f}, {s33:.8f}, {s12:.8f}, {s13:.8f}, {s23:.8f}\n"
                    f.write(line)
            
            print(f"Arquivo de tensão interpolada gerado: {output_path}")
            return output_path
        except Exception as e:
            print(f"Erro ao gerar arquivo de tensões: {e}")
            return None
    
    
    def _find_elements_file(self):
        """
        _find_elements_file / (method)
        What it does:
        Searches for the elements file in the output directory, preferring the standard name but falling back to other candidates if needed. Returns the filename or None if not found.
        Returns:
            str: Name of the found file, or None if not found.
        """
        # Primeiro, procura pelo arquivo gerado pelo script anterior
        elements_file = "elements_data.txt"
        if os.path.isfile(os.path.join(self.output_dir, elements_file)):
            return elements_file
            
        # Se não encontrar, busca outros arquivos de elementos
        for filename in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, filename)
            if os.path.isfile(file_path):
                if 'element' in filename.lower() and '.txt' in filename.lower() and 'tensao' not in filename.lower():
                    try:
                        with open(file_path, 'r') as f:
                            first_lines = ''.join([f.readline() for _ in range(5)])
                            if any(str(i) in first_lines for i in range(1, 10)):
                                return filename
                    except:
                        continue
        return None
    
    def _find_tension_file(self):
        """
        _find_tension_file / (method)
        What it does:
        Searches for the tension (stress) file in the output directory, preferring the standard name but falling back to other candidates if needed. Returns the filename or None if not found.
        Returns:
            str: Name of the found file, or None if not found.
        """
        # Primeiro, procura pelo arquivo gerado pelo script anterior
        tension_file = "residual_stress.txt"
        if os.path.isfile(os.path.join(self.output_dir, tension_file)):
            return tension_file
            
        # Se não encontrar, busca outros arquivos de tensão
        for filename in os.listdir(self.output_dir):
            if os.path.isfile(os.path.join(self.output_dir, filename)):
                if 'tensao' in filename.lower() and '.txt' in filename.lower() and 'interpolada' not in filename.lower():
                    return filename
        return None
    
    def Class_runner(self, output_dir=None):
        """
        Class_runner / (method)
        What it does:
        Auxiliary method to execute the full interpolation process: loads mesh and stress data, performs interpolation, and generates the output file. Can be used for integration with other scripts or systems.
        """
        output_dir = self.output_dir
    
        print("=============================================")
        print("Iniciando interpolação de tensões para elementos...")
        print("=============================================")
        
        # Cria instância do interpolador
        interpolator = ElementTensionInterpolator(output_dir)
        
        # Carrega elementos alvo
        print("Carregando elementos alvo...")
        if not interpolator.load_abaqus_elements():
            print("Falha ao carregar elementos alvo. Encerrando.")
            return False
        
        print(f"Total de elementos na malha alvo: {len(interpolator.target_elements)}")
        
        # Carrega campo de tensão
        print("Carregando campo de tensão fonte...")
        if not interpolator.load_tension_field():
            print("Falha ao carregar campo de tensão fonte. Encerrando.")
            return False
        
        print(f"Total de pontos na malha fonte: {len(interpolator.source_coords)}")
        
        # Interpola tensões
        print("Realizando interpolação...")
        if not interpolator.interpolate_tensions():
            print("Falha na interpolação. Encerrando.")
            return False
        
        # Gera arquivo de saída
        output_file = interpolator.generate_interpolated_tension_file()
        if output_file is None:
            print("Falha ao gerar arquivo de saída. Encerrando.")
            return False
        
        print("=============================================")
        print("Processo concluído com sucesso!")
        print("=============================================")
        return True
        


def main(output_dir=None):
    """
    main / (function)
    What it does:
    Main entry point for running the element tension interpolation process. Instantiates the interpolator and executes the workflow in the specified output directory.
    """
    if output_dir is None:
        output_dir = os.getcwd()
    
    # Cria instância do interpolador
    interpolator = ElementTensionInterpolator(output_dir)
    
    # Executa o processo de interpolação
    interpolator.Class_runner(output_dir)

if __name__ == "__main__":
    main()