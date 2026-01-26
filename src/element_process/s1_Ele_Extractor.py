
"""
s1_Ele_Extractor.py
What it does:
Extracts element and node information from Abaqus .inp files, computes element centroid coordinates, and saves the results for further analysis or visualization. Provides functions for parsing element connectivity, node coordinates, and exporting structured data to text and CSV files. Useful for preprocessing finite element models for post-processing or machine learning tasks.

Example of use:
    from Modules_python.s1_Ele_Extractor import run_element_extractor
    run_element_extractor("Mesh-0_98--Lenth-50.inp", "./Output/Mesh-0_98--Lenth-50")
"""

from utils import *
import numpy as np
import os
import pandas as pd

# Initialize the logger for this module
logger = setup_logger(__name__)

def extract_elements_from_inp(input_file):
    """
    extract_elements_from_inp / (function)
    What it does:
    Parses an Abaqus .inp file to extract element IDs, element types, and the list of connected node IDs for each element. Returns arrays and lists suitable for further processing or coordinate calculation.
    Parameters:
        input_file (str): Path to the .inp file.
    Returns:
        tuple: (elements, element_types, connected_nodes)
            - elements: NumPy array of element IDs
            - element_types: NumPy array of element types
            - connected_nodes: List of lists of connected node IDs
    """
    elements = []
    element_types = []
    connected_nodes = []
    extracting = False
    current_type = None

    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('*Element'):
                extracting = True
                if 'type=' in line.lower():
                    current_type = line.split('=')[1].strip().strip(',')
                continue
            if line.startswith('*') and not line.startswith('*Element'):
                extracting = False
                continue
            if extracting and line and not line.startswith('*'):
                parts = line.replace(',', ' ').split()
                if len(parts) >= 2:  # At least one element and one node
                    try:
                        elements.append(int(parts[0]))
                        element_types.append(current_type)
                        # The remaining values are connected nodes
                        connected_nodes.append([int(p) for p in parts[1:]])
                    except ValueError:
                        pass

    return np.array(elements), np.array(element_types), connected_nodes

def get_element_coordinates(connected_nodes, node_coords):
    """
    get_element_coordinates / (function)
    What it does:
    Calculates the centroid (average) coordinates for each element based on its connected node IDs and a dictionary of node coordinates. Returns arrays of x, y, and z centroids for all elements.
    Parameters:
        connected_nodes (list): List of lists of node IDs connected to each element.
        node_coords (dict): Dictionary mapping node IDs to (x, y, z) coordinates.
    Returns:
        tuple: (avg_x, avg_y, avg_z) as NumPy arrays.
    """
    x_coords = []
    y_coords = []
    z_coords = []
    
    for nodes in connected_nodes:
        x_vals = []
        y_vals = []
        z_vals = []
        
        for node in nodes:
            if node in node_coords:
                x_vals.append(node_coords[node][0])
                y_vals.append(node_coords[node][1])
                z_vals.append(node_coords[node][2])
        
        if x_vals:  # If valid values exist
            x_coords.append(np.mean(x_vals))
            y_coords.append(np.mean(y_vals))
            z_coords.append(np.mean(z_vals))
        else:
            x_coords.append(np.nan)
            y_coords.append(np.nan)
            z_coords.append(np.nan)
    
    return np.array(x_coords), np.array(y_coords), np.array(z_coords)

def extract_node_coordinates(input_file):
    """
    extract_node_coordinates / (function)
    What it does:
    Parses an Abaqus .inp file to extract node IDs and their (x, y, z) coordinates, returning a dictionary for fast lookup during element centroid calculation.
    Parameters:
        input_file (str): Path to the .inp file.
    Returns:
        dict: Mapping from node ID to (x, y, z) coordinates.
    """
    node_coords = {}
    extracting = False
    
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('*Node'):
                extracting = True
                continue
            if line.startswith('*') and not line.startswith('*Node'):
                extracting = False
                continue
            if extracting and line and not line.startswith('*'):
                parts = line.replace(',', ' ').split()
                if len(parts) >= 4:
                    try:
                        node_id = int(parts[0])
                        node_coords[node_id] = (float(parts[1]), float(parts[2]), float(parts[3]))
                    except ValueError:
                        pass
    
    return node_coords

def save_element_info(elements, element_types, x, y, z, output_dir):
    """
    save_element_info / (function)
    What it does:
    Saves element IDs, types, and centroid coordinates to both a summary text file and a tab-separated CSV file in the specified output directory. Also logs coordinate ranges and element type distribution for reference.
    Parameters:
        elements (np.array): Array of element IDs.
        element_types (np.array): Array of element types.
        x (np.array): Array of average x coordinates.
        y (np.array): Array of average y coordinates.
        z (np.array): Array of average z coordinates.
        output_dir (str): Output directory path.
    """
    info_path = os.path.join(output_dir, 'element_info.txt')
    data_path = os.path.join(output_dir, 'elements_data.txt')
    
    with open(info_path, 'w') as f:
        f.write(f"Total elements: {len(elements)}\n")
        f.write("Coordinate ranges:\n")
        f.write(f"X: {np.nanmin(x):.4f} to {np.nanmax(x):.4f}\n")
        f.write(f"Y: {np.nanmin(y):.4f} to {np.nanmax(y):.4f}\n")
        f.write(f"Z: {np.nanmin(z):.4f} to {np.nanmax(z):.4f}\n")
        
        # Count by element type
        unique_types, counts = np.unique(element_types, return_counts=True)
        f.write("\nElement type distribution:\n")
        for t, c in zip(unique_types, counts):
            f.write(f"{t}: {c} elements\n")
    
    df = pd.DataFrame({
        'Element': elements, 
        'Type': element_types, 
        'X_center': x, 
        'Y_center': y, 
        'Z_center': z
    })
    df.to_csv(data_path, index=False, sep='\t')
    logger.info(f"Data saved in: {data_path}")

def run_element_extractor(input_file, output_dir):
    """
    run_element_extractor / (function)
    What it does:
    Orchestrates the extraction of node coordinates and element connectivity from an Abaqus .inp file, computes element centroids, and saves the results to the output directory. Ensures the output directory exists and logs the process.
    Parameters:
        input_file (str): Path to the .inp file.
        output_dir (str): Output directory for saving extracted data.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # First, extract node coordinates from the .inp file
    node_coords = extract_node_coordinates(input_file)
    
    # Next, extract element information
    elements, element_types, connected_nodes = extract_elements_from_inp(input_file)
    
    # Calculate the average coordinates for each element
    x, y, z = get_element_coordinates(connected_nodes, node_coords)
    
    # Save the extracted information
    save_element_info(elements, element_types, x, y, z, output_dir)