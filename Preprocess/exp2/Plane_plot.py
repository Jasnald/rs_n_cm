"""
Plane_plot.py
What it does:
This script visualizes and compares fitted planes (standard and Chebyshev polynomials) from measurement data. It loads plane and step data from JSON files, generates individual and comparison plots with Seaborn and Matplotlib, and saves the results for further analysis. The script supports residual analysis, histogram visualization, and overlays of original and fitted data.

Example of use:
    Run this script directly to generate plots for all plane fits in the 'Sample_postprocess/Planes_data' directory.

    python Plane_plot.py
"""
import os
import glob
import logging
from typing import Dict, Any, Optional

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from plane_data_utils import (
    load_plane_data_from_json, 
    extract_points_from_plane_data, 
    load_steps_data_from_json, 
    extract_points_from_steps_data)  
from plane_plot_utils import plot_plane_reconstruction_on_ax

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set Seaborn style
sns.set_theme(style="whitegrid")

def plot_all_json_files(base_directory: str, z_min: float = 0.0, z_max: float = 0.02) -> None:
    """
    plot_all_json_files / (function)
    What it does:
    Searches for all JSON files in the Planes_data directory, creates individual plots for each plane fit, and generates comparison plots for standard vs. Chebyshev polynomials when available. Saves all plots to the output directory.
    Args:
        base_directory: Base directory containing 'Sample_postprocess/Planes_data'.
        z_min: Lower Z limit for visualization.
        z_max: Upper Z limit for visualization.
    """
    # Directory validation
    sample_postprocess_dir = os.path.join(base_directory, "Sample_postprocess")
    if not os.path.exists(sample_postprocess_dir):
        logging.error(f"Sample_postprocess directory not found at: {base_directory}")
        return
        
    planes_data_dir = os.path.join(sample_postprocess_dir, "Planes_data")
    if not os.path.exists(planes_data_dir):
        logging.error(f"Planes_data directory not found at: {sample_postprocess_dir}")
        return

    # Output directory
    output_dir = os.path.join(base_directory, "Plane_plots")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load all available Steps files (new format)
    steps_data = {}
    steps_files = glob.glob(os.path.join(sample_postprocess_dir, "*_Steps.json"))
    for steps_file in steps_files:
        try:
            side_name = os.path.basename(steps_file).replace("_Steps.json", "")
            # Use the new function to load in updated format
            steps_data[side_name] = load_steps_data_from_json(steps_file)
            logging.info(f"Loaded data from {side_name}_Steps.json (new format)")
        except Exception as e:
            logging.error(f"Error loading {steps_file}: {e}")

    # Process plane JSON files
    json_files = glob.glob(os.path.join(planes_data_dir, "*.json"))
    if not json_files:
        logging.warning(f"No JSON files found in {planes_data_dir}")
        return

    logging.info(f"Found {len(json_files)} JSON files in {planes_data_dir}")

    # Store data for comparison
    comparison_data: Dict[str, Dict[str, Dict[str, Any]]] = {}

    # Process each JSON file
    for json_file in json_files:
        plane_data = load_plane_data_from_json(json_file)
        if not plane_data:
            continue

        # Get the corresponding side
        side = plane_data.get('side', 'UnknownSide')
        
        # Get Steps data corresponding to the side, if available
        current_steps_data = steps_data.get(side)
        
        # Create individual plot
        plot_plane_fit(plane_data, current_steps_data, output_dir, z_min, z_max)

        # Store for comparison
        degree = plane_data.get('degree', 0)
        method = plane_data.get('method_name', 'unknown').lower()

        key = f"{side}__{degree}"
        if key not in comparison_data:
            comparison_data[key] = {}
        comparison_data[key][method] = plane_data

    # Create comparison plots where possible (standard vs. chebyshev)
    logging.info("Generating comparison plots...")
    for key, methods in comparison_data.items():
        if 'standard' in methods and 'chebyshev' in methods:
            create_comparison_plot(methods['standard'], methods['chebyshev'], output_dir, z_min, z_max)

    logging.info("All plots were successfully generated.")


def create_comparison_plot(
    standard_data: Dict[str, Any],
    chebyshev_data: Dict[str, Any],
    output_dir: str,
    z_min: float = 0.0,
    z_max: float = 0.02
) -> None:
    """
    create_comparison_plot / (function)
    What it does:
    Generates a side-by-side comparison plot of residuals and their histograms for standard and Chebyshev polynomial fits. Calculates RMSE and improvement, and saves the figure to the output directory.
    Args:
        standard_data: Plane fit data for the standard polynomial.
        chebyshev_data: Plane fit data for the Chebyshev polynomial.
        output_dir: Directory to save the output plot.
        z_min: Lower Z limit for visualization.
        z_max: Upper Z limit for visualization.
    """

    if not standard_data or not chebyshev_data:
        logging.warning("Insufficient data for comparison (standard/chebyshev).")
        return

    side_std = standard_data.get('side')
    side_cheb = chebyshev_data.get('side')
    deg_std = standard_data.get('degree')
    deg_cheb = chebyshev_data.get('degree')

    if side_std != side_cheb or deg_std != deg_cheb:
        logging.warning("Cannot compare different sides or degrees.")
        return

    side = side_std
    degree = deg_std

    X_std, Y_std, Z_orig_std, Z_fit_std, residuals_std = extract_points_from_plane_data(standard_data)
    X_cheb, Y_cheb, Z_orig_cheb, Z_fit_cheb, residuals_cheb = extract_points_from_plane_data(chebyshev_data)

    rmse_std = np.sqrt(np.mean(residuals_std**2)) if residuals_std.size else 0.0
    rmse_cheb = np.sqrt(np.mean(residuals_cheb**2)) if residuals_cheb.size else 0.0
    max_err_std = np.max(np.abs(residuals_std)) if residuals_std.size else 0.0
    max_err_cheb = np.max(np.abs(residuals_cheb)) if residuals_cheb.size else 0.0

    # Create a figure with a nice Seaborn style
    with sns.axes_style("whitegrid"):
        fig = plt.figure(figsize=(15, 10))

        # Create a custom colormap with better perceptual properties
        cmap = sns.diverging_palette(240, 10, as_cmap=True)  # Blue to Red

        ax1 = fig.add_subplot(2, 2, 1)
        ax2 = fig.add_subplot(2, 2, 2)

        abs_max_residual = max(
            abs(residuals_std.min()) if residuals_std.size else 0.0,
            abs(residuals_std.max()) if residuals_std.size else 0.0,
            abs(residuals_cheb.min()) if residuals_cheb.size else 0.0,
            abs(residuals_cheb.max()) if residuals_cheb.size else 0.0
        )

        # Residuals - Standard Polynomial
        sc1 = ax1.scatter(
            X_std, Y_std,
            c=residuals_std,
            cmap=cmap,
            s=30, alpha=0.8, edgecolor='none',
            vmin=-abs_max_residual, vmax=abs_max_residual
        )
        ax1.set_xlabel('X', fontsize=12)
        ax1.set_ylabel('Y', fontsize=12)
        ax1.set_title(f'Standard Polynomial - Residuals (RMSE={rmse_std:.6f})', fontsize=13)
        cbar1 = plt.colorbar(sc1, ax=ax1)
        cbar1.set_label('Residual', fontsize=12)

        # Residuals - Chebyshev Polynomial
        sc2 = ax2.scatter(
            X_cheb, Y_cheb,
            c=residuals_cheb,
            cmap=cmap,
            s=30, alpha=0.8, edgecolor='none',
            vmin=-abs_max_residual, vmax=abs_max_residual
        )
        ax2.set_xlabel('X', fontsize=12)
        ax2.set_ylabel('Y', fontsize=12)
        ax2.set_title(f'Chebyshev Polynomial - Residuals (RMSE={rmse_cheb:.6f})', fontsize=13)
        cbar2 = plt.colorbar(sc2, ax=ax2)
        cbar2.set_label('Residual', fontsize=12)

        # Histograms of residuals using Seaborn
        ax3 = fig.add_subplot(2, 2, 3)
        ax4 = fig.add_subplot(2, 2, 4)

        if residuals_std.size:
            sns.histplot(
                residuals_std, 
                bins=30, 
                kde=True,
                color='royalblue',
                ax=ax3,
                stat='count',
                label=f'Standard (RMSE={rmse_std:.6f})'
            )
        ax3.set_xlabel('Residual Value', fontsize=12)
        ax3.set_ylabel('Frequency', fontsize=12)
        ax3.set_title('Standard Polynomial - Residual Distribution', fontsize=13)
        ax3.legend()

        if residuals_cheb.size:
            sns.histplot(
                residuals_cheb, 
                bins=30, 
                kde=True,
                color='seagreen',
                ax=ax4,
                stat='count',
                label=f'Chebyshev (RMSE={rmse_cheb:.6f})'
            )
        ax4.set_xlabel('Residual Value', fontsize=12)
        ax4.set_ylabel('Frequency', fontsize=12)
        ax4.set_title('Chebyshev Polynomial - Residual Distribution', fontsize=13)
        ax4.legend()

        # Calculate improvement percentage
        if rmse_std > 0:
            improvement = (1 - rmse_cheb / rmse_std) * 100
            if improvement > 0:
                comparison_text = f"Chebyshev improves RMSE by {improvement:.2f}%"
            else:
                comparison_text = f"Standard is better by {-improvement:.2f}%"
        else:
            comparison_text = "Cannot calculate improvement (Standard RMSE = 0)"

        # Comparison text with better styling
        plt.figtext(
            0.5, 0.01,
            comparison_text + f"\nStandard: RMSE={rmse_std:.6f}, Max Err={max_err_std:.6f}"
            f"\nChebyshev: RMSE={rmse_cheb:.6f}, Max Err={max_err_cheb:.6f}",
            horizontalalignment='center',
            fontsize=11,
            bbox=dict(facecolor='lavender', alpha=0.7, boxstyle='round,pad=0.5')
        )
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # Better title styling
        plt.suptitle(f'{side} - Comparison (Degree {degree})', fontsize=16, y=0.98)

        filename = f"Comparison_{side}_{degree}.png"
        output_path = os.path.join(output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

    logging.info(f"Comparison chart saved for {side} (degree={degree})")


def plot_plane_fit(
    plane_data: Dict[str, Any],
    steps_data: Optional[Dict[str, Any]],
    output_dir: str,
    z_min: float = 0.0,
    z_max: float = 0.02,
    xy_margin: float = 0.05
) -> None:
    """
    plot_plane_fit / (function)
    What it does:
    Plots a detailed multi-panel visualization for a single plane fit, including fitted Z scatter, original data, reconstructed surface, residuals, histogram, and equation/statistics. Saves the figure to the output directory.
    Args:
        plane_data: Plane fit data dictionary.
        steps_data: Step data dictionary (optional).
        output_dir: Directory to save the output plot.
        z_min: Lower Z limit for visualization.
        z_max: Upper Z limit for visualization.
        xy_margin: Margin for XY grid in the reconstruction plot.
    """
    if not plane_data:
        logging.warning("No plane data provided for plotting.")
        return

    side = plane_data.get('side', 'UnknownSide')
    degree = plane_data.get('degree', 0)
    method = plane_data.get('method_name', 'UnknownMethod')

    # Extract data from fitted plane
    X, Y, Z_orig, Z_fit, residuals = extract_points_from_plane_data(plane_data)
    if X.size == 0:
        logging.warning(f"No points for {side} ({method}, degree={degree}). Skipping.")
        return

    # Clip values to visualize only [z_min, z_max]
    Z_orig_clipped = np.clip(Z_orig, z_min, z_max)
    Z_fit_clipped = np.clip(Z_fit, z_min, z_max)

    # Create figure with Seaborn styling
    with sns.axes_style("whitegrid"):
        fig = plt.figure(figsize=(18, 10))
        
        # Custom color palette for better visibility
        jet_palette = sns.color_palette("viridis", as_cmap=True)
        residual_palette = sns.diverging_palette(240, 10, as_cmap=True)  # Blue to Red

        # =============== SUBPLOT 1 ===============
        # 2D color scatter (fitted Z)
        ax1 = fig.add_subplot(2, 3, 1)
        sc1 = ax1.scatter(X, Y, c=Z_fit_clipped, cmap=jet_palette, s=30, alpha=0.8, edgecolor='none',
                        vmin=z_min, vmax=z_max)
        ax1.set_xlabel('X', fontsize=12)
        ax1.set_ylabel('Y', fontsize=12)
        ax1.set_title(f'{side} ({method}, degree={degree}) - Fitted Z Scatter', fontsize=13)
        cbar1 = plt.colorbar(sc1, ax=ax1)
        cbar1.set_label('Fitted Z', fontsize=12)

        # =============== SUBPLOT 2 ===============
        # 2D scatter of original data (Side_Steps)
        ax2 = fig.add_subplot(2, 3, 2)
        if steps_data is not None and 'steps' in steps_data:
            X_steps, Y_steps, Z_steps = extract_points_from_steps_data(steps_data)
            
            if X_steps.size > 0:
                Z_steps_clipped = np.clip(Z_steps, z_min, z_max)
                sc2 = ax2.scatter(X_steps, Y_steps, c=Z_steps_clipped, cmap=jet_palette, s=30, alpha=0.8, edgecolor='none',
                                vmin=z_min, vmax=z_max)
                cbar2 = plt.colorbar(sc2, ax=ax2)
                cbar2.set_label('Original Z', fontsize=12)
                ax2.set_title(f'{side} - Original Data (Steps)', fontsize=13)
            else:
                ax2.text(0.5, 0.5, "No points found in Steps data", 
                        ha='center', va='center', transform=ax2.transAxes, fontsize=12)
        else:
            ax2.text(0.5, 0.5, f"{side}_Steps data not found", 
                    ha='center', va='center', transform=ax2.transAxes, fontsize=12)
            ax2.set_title(f'{side} - Original Data (unavailable)', fontsize=13)
        
        ax2.set_xlabel('X', fontsize=12)
        ax2.set_ylabel('Y', fontsize=12)

        # =============== SUBPLOT 3 ===============
        # Fitted plane using JSON parameters to reconstruct the surface
        ax3 = fig.add_subplot(2, 3, 3)

        # Call the utility function to handle the logic:
        cont3 = plot_plane_reconstruction_on_ax(
            ax=ax3,
            plane_data=plane_data,
            z_min=z_min,
            z_max=z_max,
            xy_margin=xy_margin,
            use_t_shape=True  # or False, if you don't want the T mask
        )
        if cont3 is not None:
            cbar3 = plt.colorbar(cont3, ax=ax3)
            cbar3.set_label('Model Z', fontsize=12)

        # =============== SUBPLOT 4 (2D scatter - residuals) ===============
        ax4 = fig.add_subplot(2, 3, 4)
        abs_max_residual = max(abs(residuals.min()), abs(residuals.max()))
        sc4 = ax4.scatter(X, Y, c=residuals, cmap=residual_palette, s=30, alpha=0.8, edgecolor='none',
                        vmin=-abs_max_residual, vmax=abs_max_residual)
        ax4.set_xlabel('X', fontsize=12)
        ax4.set_ylabel('Y', fontsize=12)
        ax4.set_title(f'Residuals (Z_orig - Z_fit)', fontsize=13)
        cbar4 = plt.colorbar(sc4, ax=ax4)
        cbar4.set_label('Residual', fontsize=12)

        # =============== SUBPLOT 5 (residuals histogram) ===============
        ax5 = fig.add_subplot(2, 3, 5)
        
        # Using Seaborn for better histogram visualization
        rmse_val = np.sqrt(np.mean(residuals**2))
        sns.histplot(
            residuals, 
            bins=30, 
            kde=True,
            color='royalblue',
            ax=ax5,
            stat='count'
        )
        
        # Add vertical line for mean and std dev
        mean_residual = np.mean(residuals)
        std_residual = np.std(residuals)
        ax5.axvline(mean_residual, color='red', linestyle='--', alpha=0.8, 
                   label=f'Mean: {mean_residual:.6f}')
        ax5.axvline(mean_residual + std_residual, color='green', linestyle=':', alpha=0.8,
                   label=f'±1σ: {std_residual:.6f}')
        ax5.axvline(mean_residual - std_residual, color='green', linestyle=':', alpha=0.8)
        
        ax5.set_xlabel('Residual Value', fontsize=12)
        ax5.set_ylabel('Frequency', fontsize=12)
        ax5.set_title(f'Residuals Histogram - RMSE={rmse_val:.6f}', fontsize=13)
        ax5.legend(fontsize=10)

        # Additional information/statistics
        ax6 = fig.add_subplot(2, 3, 6)
        ax6.axis('off')
        equation_text = plane_data.get('equation', 'Equation unavailable')
        # Avoid very long texts (if needed)
        if len(equation_text) > 500:
            equation_text = equation_text[:500] + '...'
            
        text_info = (
            f"Equation:\n{equation_text}\n\n"
            f"RMSE: {rmse_val:.6f}\n"
            f"MaxErr: {np.max(np.abs(residuals)):.6f}\n"
            f"Mean Residual: {mean_residual:.6f}\n"
            f"Std Dev: {std_residual:.6f}"
        )
        
        # Better text box styling
        ax6.text(0.05, 0.95, text_info, ha='left', va='top', fontsize=10,
                bbox=dict(facecolor='lavender', alpha=0.7, boxstyle='round,pad=0.5'))

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # Better title styling
        plt.suptitle(f'{side} - {method} (Degree {degree})', fontsize=16, y=0.98, 
                    fontweight='bold', color='darkblue')

        # Save the figure
        filename = f"{side}_{degree}_{method.lower()}_seaborn_layout.png"
        output_path = os.path.join(output_dir, filename)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

    logging.info(f"Modified plot of {side} ({method}, degree={degree})")


def main() -> None:
    """
    main / (function)
    What it does:
    Main execution function. Sets Z limits, configures Seaborn context, and calls the function to process and plot all plane fit JSON files.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    z_min_val = -0.01
    z_max_val = 0.02

    # Set Seaborn context for better overall styling
    sns.set_context("notebook", font_scale=1.1)
    
    plot_all_json_files(base_dir, z_min=z_min_val, z_max=z_max_val)

if __name__ == "__main__":
    main()