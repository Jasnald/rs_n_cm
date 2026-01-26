
"""
s2_RE_ExnCon.py
What it does:
Maps stress data from HDF5 files to mesh elements for residual stress analysis. 
This module automates the workflow of simulation discovery, HDF5 data extraction, 
mesh reading, stress mapping using KDTree, and output file generation for Abaqus. 
It is optimized for large datasets and batch processing, with robust logging and 
error handling. Supports saving results in JSON, HDF5, and Abaqus input formats for 
further analysis or simulation.

Example of use:
    from Modules_python.s2_RE_ExnCon import StressProcessor
    processor = StressProcessor(base_dir="C:/Simulation3/Residual_Stresses_Analysis")
    results = processor.process_all_simulations(hdf5_folder="C:/Simulation3/Contour_Method/xdmf_hdf5_files")
"""

import os
import h5py
import json
import numpy as np
import pandas as pd
from scipy.spatial import KDTree
import glob
import logging
from typing import Dict, List, Optional, Union, Tuple, Any, Iterator
from functools import lru_cache

from utils import *

class StressProcessor:
    """
    StressProcessor / (class)
    What it does:
    Processes and maps stress data from HDF5 files to mesh elements for residual stress analysis. Supports simulation discovery, efficient HDF5 data extraction, mesh reading, stress mapping using KDTree, and output file generation for Abaqus. Includes batch processing, logging, and error handling for large datasets.
    """
    
    # Class constants
    DEFAULT_TOLERANCE = 5e-2
    DEFAULT_COMBINED_FILE = "S_batch.h5"
    REQUIRED_HDF5_KEYS = ['x', 'y', 'z', 's33']
    DEFAULT_CHUNK_SIZE = 10000
    
    def __init__(self, base_dir: str, 
                 tolerance: float = DEFAULT_TOLERANCE, 
                 chunk_size: int = DEFAULT_CHUNK_SIZE):
        """
        __init__ / (method)
        What it does:
        Initializes the StressProcessor with the base directory, tolerance for z=0 plane detection, and chunk size for large dataset processing.
        Parameters:
            base_dir (str): Base directory containing simulation files.
            tolerance (float): Tolerance for z=0 plane detection.
            chunk_size (int): Size of chunks for processing large datasets.
        """
        self.base_dir = base_dir
        self.tolerance = tolerance
        self.chunk_size = chunk_size
        self.simulation_data = {}
        self.logger = setup_logger(self.__class__.__name__)
        self.logger.propagate = False
        self._kdtree_cache = {}
        
    def find_simulations(self) -> Dict[str, Dict[str, str]]:
        """
        find_simulations / (method)
        What it does:
        Finds all available simulations in the base directory, mapping .inp files to their output folders and checking for required mesh data files. Returns a dictionary of simulation names to file paths and output folders.
        Returns:
            Dict[str, Dict[str, str]]: Mapping of simulation names to file paths and output folders.
        """
        try:
            # Find .inp files
            inp_pattern = os.path.join(self.base_dir, "Mesh-*--Lenth-*.inp")
            inp_files = glob.glob(inp_pattern)
            
            simulations = {}
            
            for inp_file in inp_files:
                inp_filename = os.path.basename(inp_file)
                base_name = os.path.splitext(inp_filename)[0]  # Remove .inp extension
                output_path = os.path.join(self.base_dir, 'Output', base_name)
                
                if os.path.exists(output_path):
                    # Check if the necessary files exist
                    elements_data_file = os.path.join(output_path, "elements_data.txt")
                    
                    if os.path.exists(elements_data_file):
                        simulations[base_name] = {
                            'inp_file': inp_file,
                            'output_path': output_path,
                            'elements_data_file': elements_data_file
                        }
                        self.logger.info(f"Simulation found: {base_name}")
                    else:
                        self.logger.warning(f"elements_data.txt file not found for: {base_name}")
                else:
                    self.logger.warning(f"Output folder not found for: {base_name}")
            
            self.logger.info(f"Found {len(simulations)} valid simulations")
            return simulations
            
        except Exception as e:
            self.logger.error(f"Error finding simulations: {e}")
            return {}

    def read_combined_hdf5_from_folder(self, hdf5_folder: str, 
                                    combined_file_name: str = DEFAULT_COMBINED_FILE):
        data = {}
        file_path = os.path.join(hdf5_folder, combined_file_name)
        
        with h5py.File(file_path, 'r') as hf:
            for sim_name in hf.keys():  # cada simulação
                sim_group = hf[sim_name]
                
                # Coordenadas da geometria
                coords = sim_group["geometry"]["coordinates"][:]
                
                # Pegar o primeiro frame disponível para stress
                ts_group = sim_group["time_series"]
                first_step = list(ts_group.keys())[0]
                first_frame = list(ts_group[first_step].keys())[0]
                                
                frame_grp = ts_group[first_step][first_frame]
                print(list(frame_grp.keys()))

                # Assumir que existe um campo de stress (ajustar nome conforme necessário)
                stress_field = ts_group[first_step][first_frame]["stress_tensor"][:]  # ou "s33"
                
                data[f"{sim_name}.h5"] = {
                    'x': coords[:, 0],
                    'y': coords[:, 1], 
                    'z': coords[:, 2],
                    's33': stress_field[:, 8]  # stress_field ou stress_field[:, 2] se for tensor
                }
        
        return data


    def extract_z0_data_by_z(self, data: Dict[str, Dict[str, np.ndarray]]) -> Dict[float, Dict[str, Dict[str, np.ndarray]]]:
        """
        extract_z0_data_by_z / (method)
        What it does:
        Extracts data from the z=0 plane using vectorized NumPy operations, organizing the results by unique Z values for further mapping to mesh elements.
        Parameters:
            data (Dict[str, Dict[str, np.ndarray]]): Simulation data.
        Returns:
            Dict[float, Dict[str, Dict[str, np.ndarray]]]: Data organized by unique Z values.
        """
        data_by_z = {}
        
        try:
            for file_name, dataset in data.items():
                # Use vectorized filtering for z=0 plane
                z0_mask = np.isclose(dataset['z'], 0, atol=self.tolerance)
                
                if not np.any(z0_mask):
                    self.logger.warning(f"File {file_name}: No points found at the z=0 plane")
                    continue
                
                # Extract data using boolean indexing
                z0_data = {
                    'x': dataset['x'][z0_mask],
                    'y': dataset['y'][z0_mask],
                    'z': dataset['z'][z0_mask],
                    's33': dataset['s33'][z0_mask]
                }
                
                # Organize by Z (maintain structure even for z=0)
                z_key = 0.0
                if z_key not in data_by_z:
                    data_by_z[z_key] = {}
                
                data_by_z[z_key][file_name] = z0_data
                self.logger.info(f"Extracted {len(z0_data['x'])} points at z=0 from {file_name}")
            
            return data_by_z
            
        except Exception as e:
            self.logger.error(f"Error extracting z=0 data: {e}")
            return {}

    def read_mesh_file(self, mesh_file: str) -> Optional[pd.DataFrame]:
        """
        read_mesh_file / (method)
        What it does:
        Reads the mesh file and returns a DataFrame with the element data, including element IDs and centroid coordinates. Returns None if reading fails.
        Parameters:
            mesh_file (str): Path to the mesh file.
        Returns:
            Optional[pd.DataFrame]: DataFrame with mesh element data or None if failed.
        """
        try:
            df = pd.read_csv(mesh_file, sep='\t')
            self.logger.info(f"Mesh file read successfully: {len(df)} elements")
            self.logger.info(f"Columns: {list(df.columns)}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error reading mesh file {mesh_file}: {e}")
            return None

    @lru_cache(maxsize=128)
    def _get_cached_kdtree(self, points_hash: int) -> KDTree:
        """
        _get_cached_kdtree / (method)
        What it does:
        Gets a cached KDTree instance for reuse, based on a hash of the points array. (Placeholder for cache logic; actual cache is managed in create_stress_mapping_by_z.)
        Parameters:
            points_hash (int): Hash of the points array for caching.
        Returns:
            KDTree: Cached KDTree instance.
        """
        # This is a placeholder - the actual points are passed via the calling method
        # The cache is managed in create_stress_mapping_by_z
        pass

    def create_stress_mapping_by_z(self, z0_data: Dict[float, Dict[str, Dict[str, np.ndarray]]], 
                                   mesh_df: pd.DataFrame) -> Optional[Dict[float, Dict[str, List[Dict[str, Any]]]]]:
        """
        create_stress_mapping_by_z / (method)
        What it does:
        Creates a stress mapping by matching mesh element centroids (X, Y) to the nearest stress data points at z=0 using KDTree, organized by unique Z values from the mesh. Returns a mapping of Z coordinates to stress data per element.
        Parameters:
            z0_data (Dict[float, Dict[str, Dict[str, np.ndarray]]]): Stress data at z=0.
            mesh_df (pd.DataFrame): DataFrame with mesh element information.
        Returns:
            Optional[Dict[float, Dict[str, List[Dict[str, Any]]]]]: Mapping of Z coordinates to stress data per element.
        """
        if mesh_df is None or not z0_data:
            self.logger.error("Invalid input data for stress mapping")
            return None
        
        try:
            # Get unique Z values from the mesh
            z_values_mesh = sorted(mesh_df['Z_center'].unique())
            self.logger.info(f"Processing {len(z_values_mesh)} unique Z values")
            
            # Create a data structure organized by Z
            stress_by_z = {}
            
            # For each Z value in the mesh
            for z_mesh in z_values_mesh:
                stress_by_z[z_mesh] = {}
                
                # Filter elements for this Z plane
                elements_z = mesh_df[mesh_df['Z_center'] == z_mesh]
                
                # For each stress data file at z=0
                for file_name, stress_data in z0_data.get(0.0, {}).items():
                    if len(stress_data['x']) == 0:
                        continue
                    
                    # Create cache key for KDTree
                    stress_points = np.column_stack((stress_data['x'], stress_data['y']))
                    cache_key = hash(stress_points.tobytes())
                    
                    # Get or create KDTree (with caching)
                    if cache_key not in self._kdtree_cache:
                        self._kdtree_cache[cache_key] = KDTree(stress_points)
                        self.logger.debug(f"Created new KDTree for {file_name}")
                    
                    tree = self._kdtree_cache[cache_key]
                    
                    # Vectorized query for all elements at once
                    query_points = np.column_stack((elements_z['X_center'].values, elements_z['Y_center'].values))
                    distances, indices = tree.query(query_points, k=1)
                    
                    # Create element data list
                    elements_with_stress = []
                    for idx, (_, element) in enumerate(elements_z.iterrows()):
                        element_data = {
                            'element_id': element['Element'],
                            'x': element['X_center'],
                            'y': element['Y_center'],
                            'z': element['Z_center'],
                            's33': float(stress_data['s33'][indices[idx]]),
                            'distance_to_stress_point': float(distances[idx])
                        }
                        elements_with_stress.append(element_data)
                    
                    stress_by_z[z_mesh][file_name] = elements_with_stress
                    self.logger.info(f"Mapped {len(elements_with_stress)} elements for Z={z_mesh:.2f}")
            
            return stress_by_z
            
        except Exception as e:
            self.logger.error(f"Error creating stress mapping: {e}")
            return None

    def save_organized_data(self, stress_by_z: Dict[float, Dict[str, List[Dict[str, Any]]]], 
                           output_folder: str, format: str = 'json') -> None:
        """
        save_organized_data / (method)
        What it does:
        Saves the organized stress mapping data in JSON or HDF5 format, converting float keys to strings for JSON compatibility and storing element-wise data efficiently for large datasets.
        Parameters:
            stress_by_z (Dict[float, Dict[str, List[Dict[str, Any]]]]): Stress mapping data.
            output_folder (str): Output folder path.
            format (str): Output format ('json' or 'hdf5').
        """
        if not stress_by_z:
            self.logger.warning("No data to save")
            return
        
        try:
            if format.lower() == 'json':
                output_file = os.path.join(output_folder, "stress_mapping_by_z.json")
                
                # Convert float keys to strings for JSON compatibility
                stress_json = {}
                for z_key, files in stress_by_z.items():
                    stress_json[str(z_key)] = files
                
                with open(output_file, 'w') as f:
                    json.dump(stress_json, f, indent=2)
                self.logger.info(f"Data saved in JSON: {output_file}")
                
            elif format.lower() == 'hdf5':
                output_file = os.path.join(output_folder, "stress_mapping_by_z.h5")
                
                with h5py.File(output_file, 'w') as hf:
                    for z_key, files in stress_by_z.items():
                        z_group = hf.create_group(f"z_{z_key}")
                        
                        for file_name, elements in files.items():
                            if not elements:
                                continue
                                
                            file_group = z_group.create_group(file_name.replace('.h5', ''))
                            
                            # Convert to numpy arrays for efficient storage
                            file_group.create_dataset('element_id', data=np.array([e['element_id'] for e in elements]))
                            file_group.create_dataset('x', data=np.array([e['x'] for e in elements]))
                            file_group.create_dataset('y', data=np.array([e['y'] for e in elements]))
                            file_group.create_dataset('z', data=np.array([e['z'] for e in elements]))
                            file_group.create_dataset('s33', data=np.array([e['s33'] for e in elements]))
                            file_group.create_dataset('distance', data=np.array([e['distance_to_stress_point'] for e in elements]))
                
                self.logger.info(f"Data saved in HDF5: {output_file}")
                
        except Exception as e:
            self.logger.error(f"Error saving data in {format} format: {e}")

    def create_abaqus_stress_file(self, stress_by_z: Dict[float, Dict[str, List[Dict[str, Any]]]], 
                                  output_folder: str, file_name: str = "stress_input.txt") -> None:
        """
        create_abaqus_stress_file / (method)
        What it does:
        Creates an input file for Abaqus with the stress values per element, formatted for direct use in simulation input. Each line contains the element ID and mapped stress values.
        Parameters:
            stress_by_z (Dict[float, Dict[str, List[Dict[str, Any]]]]): Stress mapping data.
            output_folder (str): Output folder path.
            file_name (str): Name of the output file.
        """
        output_file = os.path.join(output_folder, file_name)
        
        try:
            with open(output_file, 'w') as f:
                element_count = 0
                for z_key, files in stress_by_z.items():
                    for file_name, elements in files.items():
                        for element in elements:
                            # Format: Element_ID, 0, 0, S33, 0, 0, 0
                            f.write(f"{element['element_id']}, 0, 0, {element['s33']:.6e}, 0, 0, 0\n")
                            element_count += 1
            
            self.logger.info(f"Abaqus stress file saved: {output_file} ({element_count} elements)")
            
        except Exception as e:
            self.logger.error(f"Error creating Abaqus stress file: {e}")

    def process_specific_simulation(self, simulation_name: str, hdf5_folder: str) -> Optional[Dict[float, Dict[str, List[Dict[str, Any]]]]]:
        """
        process_specific_simulation / (method)
        What it does:
        Processes a specific simulation through the complete workflow: simulation discovery, HDF5 reading, z=0 extraction, mesh reading, stress mapping, and output file generation. Returns the processed stress mapping data or None if any step fails.
        Parameters:
            simulation_name (str): Name of the simulation to process.
            hdf5_folder (str): Path to folder containing HDF5 files.
        Returns:
            Optional[Dict[float, Dict[str, List[Dict[str, Any]]]]]: Processed stress mapping data.
        """
        try:
            simulations = self.find_simulations()
            
            if simulation_name not in simulations:
                self.logger.error(f"Simulation '{simulation_name}' not found")
                return None
            
            sim_info = simulations[simulation_name]
            self.logger.info(f"=== PROCESSING SIMULATION: {simulation_name} ===")
            self.logger.info(f"INP File: {sim_info['inp_file']}")
            self.logger.info(f"Output Folder: {sim_info['output_path']}")
            
            # 1. Read HDF5 data
            self.logger.info("1. Reading HDF5 data...")
            hdf5_data = self.read_combined_hdf5_from_folder(hdf5_folder)
            
            if not hdf5_data:
                self.logger.error("No HDF5 data found for this simulation")
                return None
            
            # 2. Extract data from the z=0 plane
            self.logger.info("2. Extracting data from the z=0 plane...")
            z0_data = self.extract_z0_data_by_z(hdf5_data)
            
            if not z0_data:
                self.logger.error("No z=0 data extracted")
                return None
            
            # 3. Read mesh file
            self.logger.info("3. Reading mesh file...")
            mesh_df = self.read_mesh_file(sim_info['elements_data_file'])
            
            if mesh_df is None:
                self.logger.error("Failed to read the mesh file")
                return None
            
            # 4. Create stress mapping
            self.logger.info("4. Creating stress mapping...")
            stress_by_z = self.create_stress_mapping_by_z(z0_data, mesh_df)
            
            if not stress_by_z:
                self.logger.error("Failed to create stress mapping")
                return None
            
            # 5. Save organized data
            self.logger.info("5. Saving organized data...")
            self.save_organized_data(stress_by_z, sim_info['output_path'], format='json')
            self.save_organized_data(stress_by_z, sim_info['output_path'], format='hdf5')
            
            # 6. Create Abaqus input file
            self.logger.info("6. Creating Abaqus input file...")
            self.create_abaqus_stress_file(stress_by_z, sim_info['output_path'])
            
            self.logger.info(f"=== PROCESSING COMPLETED FOR: {simulation_name} ===")
            return stress_by_z
            
        except Exception as e:
            self.logger.error(f"Error processing simulation {simulation_name}: {e}")
            return None

    def process_all_simulations(self, hdf5_folder: str) -> Dict[str, Dict[float, Dict[str, List[Dict[str, Any]]]]]:
        """
        process_all_simulations / (method)
        What it does:
        Processes all found simulations in the base directory, running the complete workflow for each and saving results in the output folder. Returns a dictionary of results for all processed simulations.
        Parameters:
            hdf5_folder (str): Path to folder containing HDF5 files.
        Returns:
            Dict[str, Dict[float, Dict[str, List[Dict[str, Any]]]]]: Results for all processed simulations.
        """
        try:
            simulations = self.find_simulations()
            
            if not simulations:
                self.logger.warning("No simulations found")
                return {}
            
            results = {}
            
            for i, simulation_name in enumerate(simulations.keys(), 1):
                self.logger.info(f"--- Processing simulation {i}/{len(simulations)}: {simulation_name} ---")
                
                try:
                    result = self.process_specific_simulation(simulation_name, hdf5_folder)
                    if result:
                        results[simulation_name] = result
                        self.logger.info(f"✓ Simulation {simulation_name} processed successfully")
                    else:
                        self.logger.error(f"✗ Failed to process simulation {simulation_name}")
                        
                except Exception as e:
                    self.logger.error(f"✗ Error processing simulation {simulation_name}: {e}")
                    continue
            
            self.logger.info(f"PROCESSING COMPLETED: {len(results)} /{len(simulations)} simulations processed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing all simulations: {e}")
            return {}

# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize processor
    base_dir = r"C:\Simulation4\Residual_Stresses_Analysis"
    hdf5_folder = r"C:\Simulation4\Contour_Method\xdmf_hdf5_files"
    
    processor = StressProcessor(base_dir, tolerance=5e-2, chunk_size=10000)
    
    # Option 1: Process all simulations
    results = processor.process_all_simulations(hdf5_folder)
    
    # Option 2: Process a specific simulation
    # result = processor.process_specific_simulation("Mesh-0_9--Lenth-50_0", hdf5_folder)
    
    # Option 3: Just find available simulations
    # simulations = processor.find_simulations()
    # print("Simulations found:", list(simulations.keys()))