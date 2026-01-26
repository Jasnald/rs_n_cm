
"""
s2_RE_Field.py
What it does:
Generates a synthetic residual stress field in cylindrical coordinates for a given mesh, based on coordinate limits extracted from an information file or default values. The script creates a homogeneous node mesh, computes geometric center, calculates stresses, and saves the results in a text file. Useful for testing, benchmarking, or initializing simulation workflows when real stress data is unavailable.

Example of use:
    from Modules_python.s2_RE_Field import main
    main(output_dir="./Output/Mesh-0_98--Lenth-50")
"""

import numpy as np
import os
import re
import pandas as pd
from dataclasses import dataclass

@dataclass
class CoordinateLimits:
    """
    CoordinateLimits / (class)
    What it does:
    Stores the minimum and maximum values for x, y, z coordinates and the total number of nodes for a mesh. Provides class methods to create an instance from an information file or to return default values if extraction fails.
    """
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float
    total_nodes: int

    @classmethod
    def from_info_file(cls, file_path):
        """
        from_info_file / (method)
        What it does:
        Creates a CoordinateLimits object from an information file by extracting coordinate limits and total node count. Returns None if extraction fails.
        """
        limits = extract_coordinate_limits(file_path)
        if not limits:
            return None
        return cls(
            limits.get('x_min', 0.0),
            limits.get('x_max', 0.04),
            limits.get('y_min', 24.94),
            limits.get('y_max', 25.0),
            limits.get('z_min', 0.0),
            limits.get('z_max', 0.048),
            limits.get('total_nodes', 39150)
        )

    @classmethod
    def default_values(cls):
        """
        default_values / (method)
        What it does:
        Returns a CoordinateLimits object with default values if extraction from file is not possible.
        """
        return cls(0.0, 0.04, 24.94, 25.0, 0.0, 0.048, 39150)


def find_info_file(directory='.'):
    """
    find_info_file / (function)
    What it does:
    Searches for a node information file in the specified directory by looking for filenames and content patterns related to node or coordinate information. Returns the path of the found file or None if not found.
    """
    search_terms = ['info', 'nos', 'node']
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path) and any(term in file.lower() for term in search_terms):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(1000)  # Read only the beginning of the file for verification
                    if 'Total de' in content and ('coordenadas' in content or 'Intervalos' in content):
                        return file_path
            except Exception:
                continue
    return None


def extract_coordinate_limits(file_path):
    """
    extract_coordinate_limits / (function)
    What it does:
    Extracts coordinate limits and total node count from an information file using regular expressions. Returns a dictionary with the extracted values or an empty dictionary if extraction fails.
    """
    limits = {}
    patterns = {
        'total_nodes': [
            r'Total de n[oóуňòô]s(?:\s+extra[ií]dos)?\s*:?\s*(\d+)',
            r'Total nodes\s*:?\s*(\d+)'
        ],
        'x': [r'X\s*:?\s*([-\d.]+)\s*(?:a|to)\s*([-\d.]+)'],
        'y': [r'Y\s*:?\s*([-\d.]+)\s*(?:a|to)\s*([-\d.]+)'],
        'z': [r'Z\s*:?\s*([-\d.]+)\s*(?:a|to)\s*([-\d.]+)']
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            for key, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, content)
                    if match:
                        if key == 'total_nodes':
                            limits[key] = int(match.group(1))
                        else:
                            limits[f'{key}_min'] = float(match.group(1))
                            limits[f'{key}_max'] = float(match.group(2))
                        break
        return limits
    except Exception as e:
        print(f"Extraction error: {e}")
        return {}


def generate_mesh(limits, target_density=15):
    """
    generate_mesh / (function)
    What it does:
    Generates a node mesh with homogeneous density based on the provided coordinate limits. The number of divisions for each axis is scaled to maintain uniform node spacing. Returns a NumPy array with columns [ID, X, Y, Z].
    """
    # Calculate ranges for each coordinate
    x_range = limits.x_max - limits.x_min
    y_range = limits.y_max - limits.y_min
    z_range = limits.z_max - limits.z_min
    
    # Find the smallest range to use as reference
    min_range = min(x_range, y_range, z_range)
    
    # Calculate number of divisions for each axis to maintain homogeneous density
    x_divisions = max(2, int(target_density * x_range / min_range))
    y_divisions = max(2, int(target_density * y_range / min_range))
    z_divisions = max(2, int(target_density * z_range / min_range))
    
    print(f"Mesh divisions - X: {x_divisions}, Y: {y_divisions}, Z: {z_divisions}")
    
    x = np.linspace(limits.x_min, limits.x_max, x_divisions)
    y = np.linspace(limits.y_min, limits.y_max, y_divisions)
    z = np.linspace(limits.z_min, limits.z_max, z_divisions)
    
    total_nodes = x_divisions * y_divisions * z_divisions
    nodes = np.zeros((total_nodes, 4))
    
    idx = 0
    for z_val in z:
        for y_val in y:
            for x_val in x:
                nodes[idx] = [idx + 1, x_val, y_val, z_val]
                idx += 1
                
    return nodes


def calculate_geometric_center(limits):
    """
    calculate_geometric_center / (function)
    What it does:
    Calculates the geometric center of the part based on the coordinate limits. Returns a tuple with the center coordinates (x, y, z).
    """
    return (
        (limits.x_min + limits.x_max) / 2,
        (limits.y_min + limits.y_max) / 2,
        (limits.z_min + limits.z_max) / 2
    )


def calculate_cylindrical_stress(nodes, center):
    """
    calculate_cylindrical_stress / (function)
    What it does:
    Calculates synthetic residual stresses in cylindrical coordinates for each node, based on its distance from the geometric center. Returns a list of dictionaries with node coordinates and stress components.
    """
    dx = nodes[:, 1] - center[0]
    dy = nodes[:, 2] - center[1]
    dz = nodes[:, 3] - center[2]
    
    # Cylindrical coordinates
    r = np.sqrt(dx**2 + dy**2)
    theta = np.arctan2(dy, dx)
    
    # 3D distance from center
    distance_3d = np.sqrt(r**2 + dz**2)
    max_distance = np.max(distance_3d) if len(distance_3d) else 1.0
    distance_norm = distance_3d / max_distance
    
    # Example stress calculation based on normalized distances
    sigma_r = 5000.0 * (distance_norm**2)
    sigma_theta = 5000.0 * distance_norm
    sigma_z = 5000.0 * (distance_norm**1.5)
    
    # Tau (shear) as zero, if desired
    tau_rt = 0.0 * distance_norm
    tau_rz = 0.0 * distance_norm
    tau_tz = 0.0 * distance_norm
    
    results = []
    for i in range(len(nodes)):
        results.append({
            'id': int(nodes[i, 0]),
            'x': nodes[i, 1],
            'y': nodes[i, 2],
            'z': nodes[i, 3],
            'r': r[i],
            'theta': theta[i],
            'sigma_r': sigma_r[i],
            'sigma_theta': sigma_theta[i],
            'sigma_z': sigma_z[i],
            'tau_rt': tau_rt[i],
            'tau_rz': tau_rz[i],
            'tau_tz': tau_tz[i]
        })
    return results


def save_stress_field(results, output_dir):
    """
    save_stress_field / (function)
    What it does:
    Saves the calculated stress field to a text file in the specified output directory, including node coordinates and all stress components in cylindrical coordinates.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "residual_stress.txt")
    
    with open(output_path, 'w') as f:
        f.write("** Residual stress field in cylindrical coordinates\n")
        f.write("ID, X, Y, Z, R, Theta, Sigma_r, Sigma_theta, Sigma_z, Tau_r_theta, Tau_r_z, Tau_theta_z\n")
        
        for result in results:
            line = (
                f"{result['id']}, {result['x']:.8f}, {result['y']:.8f}, {result['z']:.8f}, "
                f"{result['r']:.8f}, {result['theta']:.8f}, "
                f"{result['sigma_r']:.8f}, {result['sigma_theta']:.8f}, "
                f"{result['sigma_z']:.8f}, {result['tau_rt']:.8f}, "
                f"{result['tau_rz']:.8f}, {result['tau_tz']:.8f}\n"
            )
            f.write(line)
    
    print(f"File generated: {os.path.abspath(output_path)}")


def main(output_dir=None):
    """
    main / (function)
    What it does:
    Main entry point for generating a synthetic residual stress field. Loads coordinate limits from an information file if available, generates a node mesh, computes geometric center, calculates stresses, and saves the results to a text file in the output directory.
    """
    if output_dir is None:
        output_dir = os.path.dirname(__file__)
    
    # Try to find node information file in the output directory
    info_file = find_info_file(output_dir)
    
    if info_file:
        print(f"Information file found: {info_file}")
        limits = CoordinateLimits.from_info_file(info_file)
        if limits is None:
            print("Could not extract limits from file. Using default values.")
            limits = CoordinateLimits.default_values()
    else:
        print("Information file not found. Using default values.")
        limits = CoordinateLimits.default_values()
    
    # Display limits
    print("Coordinate limits:")
    print(f"  X: {limits.x_min:.4f} to {limits.x_max:.4f}")
    print(f"  Y: {limits.y_min:.4f} to {limits.y_max:.4f}")
    print(f"  Z: {limits.z_min:.4f} to {limits.z_max:.4f}")
    
    # Generate node mesh
    print("Generating mesh...")
    t0 = __import__('time').time()
    nodes = generate_mesh(limits)
    print(f"Mesh generated with {len(nodes)} nodes in {__import__('time').time() - t0:.2f} s")
    
    # Calculate geometric center
    center = calculate_geometric_center(limits)
    print(f"Geometric center: ({center[0]:.4f}, {center[1]:.4f}, {center[2]:.4f})")
    
    # Calculate stresses
    print("Calculating stresses...")
    t0 = __import__('time').time()
    stress_results = calculate_cylindrical_stress(nodes, center)
    print(f"Stresses calculated in {__import__('time').time() - t0:.2f} s")
    
    # Save results
    save_stress_field(stress_results, output_dir)
    
    print("Process completed!")


if __name__ == "__main__":
    main()