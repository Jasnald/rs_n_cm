
"""
Elements_plot.py
What it does:
Provides functions for loading element and stress data from simulation output files and visualizing them using 2D and 3D plots. Enables comparison between original residual stress fields and interpolated stress fields for finite element models, supporting both full 3D scatter plots and 2D slices at specified Z-levels. Useful for post-processing and validation of stress interpolation routines.

Example of use:
    from Modules_python.Elements_plot import plot_3d_comparison, plot_2d_slice
    plot_3d_comparison(
        element_data_file="elements_data.txt",
        residual_stress_file="residual_stress.txt",
        interpolated_stress_file="stress_input.txt"
    )
    plot_2d_slice(
        element_data_file="elements_data.txt",
        residual_stress_file="residual_stress.txt",
        interpolated_stress_file="stress_input.txt",
        z_slice=0.01
    )
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import os

def load_element_data(filepath):
    """
    load_element_data / (function)
    What it does:
    Loads element centroid coordinates from a tab-separated file, renaming columns to standard X, Y, Z labels. Returns a pandas DataFrame with element positions for further analysis or plotting.
    """
    try:
        df = pd.read_csv(filepath, sep='\t')
        df.rename(columns={
            'X_center': 'X',
            'Y_center': 'Y',
            'Z_center': 'Z'
        }, inplace=True)
        return df
    except Exception as e:
        print(f"Error loading elements: {e}")
        return pd.DataFrame()

def load_residual_stress(filepath):
    """
    load_residual_stress / (function)
    What it does:
    Loads residual stress data from a text file in cylindrical format, parses element IDs and stress components, and computes the Von Mises equivalent stress for each element. Returns a DataFrame with element coordinates and Von Mises values.
    """
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('**') or line.startswith('ID') or ',' not in line:
                continue
            parts = line.strip().split(',')
            if len(parts) >= 12:
                try:
                    element_id = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])
                    sigma_r = float(parts[6])
                    sigma_theta = float(parts[7])
                    sigma_z = float(parts[8])
                    von_mises = np.sqrt(
                        0.5 * ((sigma_r - sigma_theta)**2 + 
                              (sigma_theta - sigma_z)**2 + 
                              (sigma_z - sigma_r)**2)
                    )
                    data.append([element_id, x, y, z, von_mises])
                except (ValueError, IndexError):
                    continue
    return pd.DataFrame(data, columns=['Element', 'X', 'Y', 'Z', 'VonMises'])

def load_interpolated_stress(filepath):
    """
    load_interpolated_stress / (function)
    What it does:
    Loads interpolated stress data from a text file in cartesian format, parses element IDs and stress tensor components, and computes the Von Mises equivalent stress for each element. Returns a DataFrame with element IDs and Von Mises values.
    """
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('*') or ',' not in line:
                continue
            parts = line.strip().split(',')
            if len(parts) >= 7:
                try:
                    element_id = int(parts[0])
                    s11 = float(parts[1])
                    s22 = float(parts[2])
                    s33 = float(parts[3])
                    s12 = float(parts[4])
                    s13 = float(parts[5])
                    s23 = float(parts[6])
                    von_mises = np.sqrt(
                        0.5 * ((s11 - s22)**2 + 
                              (s22 - s33)**2 + 
                              (s33 - s11)**2 + 
                              6 * (s12**2 + s13**2 + s23**2))
                    )
                    data.append([element_id, von_mises])
                except (ValueError, IndexError):
                    continue
    return pd.DataFrame(data, columns=['Element', 'VonMises'])

def plot_3d_comparison(element_data_file, residual_stress_file, interpolated_stress_file, 
                     plot_width=20, plot_height=12, sample_rate1=5, sample_rate2=5):
    """
    plot_3d_comparison / (function)
    What it does:
    Creates side-by-side 3D scatter plots comparing the Von Mises stress distribution from the original residual stress field and the interpolated stress field. Allows independent sampling rates for each dataset to improve visualization performance. Useful for visually validating the quality of stress interpolation.
    Parameters:
        element_data_file (str): Path to the file with element centroid coordinates.
        residual_stress_file (str): Path to the file with original residual stress data.
        interpolated_stress_file (str): Path to the file with interpolated stress data.
        plot_width (int): Width of the plot in inches.
        plot_height (int): Height of the plot in inches.
        sample_rate1 (int): Sampling rate for residual stress points.
        sample_rate2 (int): Sampling rate for interpolated stress points.
    """
    # Load data
    print("Loading elements...")
    elements_df = load_element_data(element_data_file)
    
    print("Loading residual stress...")
    residual_df = load_residual_stress(residual_stress_file)
    
    print("Loading interpolated stress...")
    interp_df = load_interpolated_stress(interpolated_stress_file)
    
    # Merge interpolated data with element coordinates
    merged_interp = pd.merge(elements_df, interp_df, on='Element', how='inner')
    
    # Apply separate sampling
    residual_sampled = residual_df.iloc[::sample_rate1]
    interp_sampled = merged_interp.iloc[::sample_rate2]
    
    # Configure plot
    fig = plt.figure(figsize=(plot_width, plot_height))
    
    # Residual Stress Plot
    ax1 = fig.add_subplot(121, projection='3d')
    scatter1 = ax1.scatter(
        residual_sampled['X'], residual_sampled['Y'], residual_sampled['Z'],
        c=residual_sampled['VonMises'], s=10, cmap='viridis'
    )
    ax1.set_title(f'Residual Stress (1/{sample_rate1} points)')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    plt.colorbar(scatter1, ax=ax1, label='Von Mises (MPa)')
    
    # Interpolated Stress Plot
    ax2 = fig.add_subplot(122, projection='3d')
    scatter2 = ax2.scatter(
        interp_sampled['X'], interp_sampled['Y'], interp_sampled['Z'],
        c=interp_sampled['VonMises'], s=10, cmap='viridis'
    )
    ax2.set_title(f'Interpolated Stress (1/{sample_rate2} elements)')
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_zlabel('Z')
    plt.colorbar(scatter2, ax=ax2, label='Von Mises (MPa)')
    
    plt.tight_layout()
    #plt.savefig('stress_comparison_3d.png', dpi=300)
    plt.show()

def plot_2d_slice(element_data_file, residual_stress_file, interpolated_stress_file,
                 z_slice=0.0, tolerance=0.001,
                 plot_width=12, plot_height=6):
    """
    plot_2d_slice / (function)
    What it does:
    Plots a 2D slice at a specified Z-level, showing the Von Mises stress distribution for both the original residual and interpolated stress fields, using a unified color scale for direct comparison. Useful for detailed inspection of stress interpolation accuracy at specific cross-sections.
    Parameters:
        element_data_file (str): Path to the file with element centroid coordinates.
        residual_stress_file (str): Path to the file with original residual stress data.
        interpolated_stress_file (str): Path to the file with interpolated stress data.
        z_slice (float): Z-coordinate value for the slice.
        tolerance (float): Tolerance for selecting elements near the Z-slice.
        plot_width (int): Width of the plot in inches.
        plot_height (int): Height of the plot in inches.
    """
    # Load data
    elements_df = load_element_data(element_data_file)
    residual_df = load_residual_stress(residual_stress_file)
    interp_df = load_interpolated_stress(interpolated_stress_file)
    merged_interp = pd.merge(elements_df, interp_df, on='Element', how='inner')

    # Filter slices
    residual_slice = residual_df[
        (residual_df['Z'] >= z_slice - tolerance) & 
        (residual_df['Z'] <= z_slice + tolerance)
    ]
    interp_slice = merged_interp[
        (merged_interp['Z'] >= z_slice - tolerance) &
        (merged_interp['Z'] <= z_slice + tolerance)
    ]

    # Calculate common limits for color scale
    vmin = min(residual_slice['VonMises'].min(), interp_slice['VonMises'].min())
    vmax = max(residual_slice['VonMises'].max(), interp_slice['VonMises'].max())

    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(plot_width, plot_height))

    # Residual Plot
    sc1 = ax1.scatter(
        residual_slice['X'], residual_slice['Y'],
        c=residual_slice['VonMises'], s=15, cmap='viridis',
        vmin=vmin, vmax=vmax  # Force same scale
    )
    ax1.set_title(f'Z-slice at {z_slice:.2f} - Residual')
    plt.colorbar(sc1, ax=ax1, label='Von Mises (MPa)')

    # Interpolated Plot
    sc2 = ax2.scatter(
        interp_slice['X'], interp_slice['Y'],
        c=interp_slice['VonMises'], s=15, cmap='viridis',
        vmin=vmin, vmax=vmax  # Same scale here
    )
    ax2.set_title(f'Z-slice at {z_slice:.2f} - Interpolated')
    plt.colorbar(sc2, ax=ax2, label='Von Mises (MPa)')

    plt.tight_layout()
    #plt.savefig(f'stress_slice_z_{z_slice:.2f}.png', dpi=300)
    plt.show()

def main():
    """
    main / (function)
    What it does:
    Example entry point for running 3D and 2D stress comparison plots using hardcoded file paths and parameters. Checks for required files and demonstrates usage of the plotting functions. Intended for quick testing or as a template for custom scripts.
    """
    output_dir = r"C:\Simulation\Residual_Stresses_Analysis\Output\Mesh-0_98--Lenth-50"
    
    element_data_file = os.path.join(output_dir, "elements_data.txt")
    residual_stress_file = os.path.join(output_dir, "residual_stress.txt")

    interpolated_stress_file = os.path.join(output_dir, "interpoladed_element_stresses.txt")
    interpolated_stress_file = os.path.join(output_dir, "stress_input.txt")
    # File verification
    required_files = [
        (element_data_file, "element data file"),
        (residual_stress_file, "residual stress file"),
        (interpolated_stress_file, "interpolated stress file")
    ]
    
    missing = [msg for file, msg in required_files if not os.path.exists(file)]
    if missing:
        print("Missing files:")
        for msg in missing: print(f"- {msg}")
        return
    
    # Customizable parameters
    plot_3d_comparison(
        element_data_file, 
        residual_stress_file, 
        interpolated_stress_file,
        plot_width=18,
        plot_height=8,
        sample_rate1=3,  # 1 in every 3 residual points
        sample_rate2=1   # 1 in every 5 interpolated elements
    )

    # Uncomment to plot 2D slices at different Z levels
    #plot_2d_slice(element_data_file, residual_stress_file, interpolated_stress_file, z_slice=0.01, tolerance=0.001)
    # plot_2d_slice(element_data_file, residual_stress_file, interpolated_stress_file, z_slice=0.02, tolerance=0.001)
    # plot_2d_slice(element_data_file, residual_stress_file, interpolated_stress_file, z_slice=0.03, tolerance=0.001)
    # plot_2d_slice(element_data_file, residual_stress_file, interpolated_stress_file, z_slice=0.04, tolerance=0.001)

if __name__ == "__main__":
    main()