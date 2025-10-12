"""Visualization module for iDoE results.

Generates publication-ready plots showing:
- Design space coverage (Doehlert design)
- Experiment paths through the design space
- Combo usage heatmaps
- Per-run timeline profiles
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path

from .models import OptimizationResult


class IDOEVisualizer:
    """
    Generates scientific visualizations for iDoE optimization results.

    All plots use matplotlib defaults for colors and follow publication standards
    with large, readable fonts suitable for print (300 dpi).
    """

    def __init__(
        self,
        result: OptimizationResult,
        combos: np.ndarray,
        total_run_hours: float = 30.0,
        n_stages: int = 3,
        output_dir: str = "plots"
    ):
        """
        Initialize visualizer with optimization results.

        Args:
            result: OptimizationResult object from optimizer
            combos: Array of shape (n_combos, 2) with (mu_set, temperature) pairs
            total_run_hours: Total duration of each experiment run
            n_stages: Number of stages per experiment
            output_dir: Directory to save plot files
        """
        self.result = result
        self.combos = combos
        self.n_combos = len(combos)
        self.total_run_hours = total_run_hours
        self.n_stages = n_stages
        self.per_stage_hours = total_run_hours / n_stages
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Extract solution data
        self.solution_exp_stages = self._extract_solution()
        self.n_experiments = len(self.solution_exp_stages)

        # Configure matplotlib for publication quality
        self._configure_matplotlib()

    def _configure_matplotlib(self):
        """Set matplotlib parameters for publication-quality plots."""
        plt.rcParams.update({
            'font.size': 12,
            'axes.labelsize': 14,
            'axes.titlesize': 16,
            'xtick.labelsize': 11,
            'ytick.labelsize': 11,
            'legend.fontsize': 11,
            'figure.titlesize': 16,
            'figure.dpi': 100,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'axes.grid': False
        })

    def _extract_solution(self) -> Dict[int, List[int]]:
        """
        Extract experiment-to-combo assignments from result.

        Returns:
            Dict mapping 0-based experiment index to list of 3 combo indices (0-based)
        """
        solution = {}
        for exp in self.result.experiments:
            if not exp.is_empty():
                # Convert to 0-based indexing
                exp_idx = exp.experiment_id - 1
                combo_indices = [stage.combination - 1 for stage in exp.stages]
                solution[exp_idx] = combo_indices
        return solution

    def _build_usage_matrix(self) -> np.ndarray:
        """
        Build usage matrix showing how many times each combo appears in each experiment.

        Returns:
            Array of shape (n_combos, n_experiments) with integer counts in {0, 1, 2}
        """
        usage = np.zeros((self.n_combos, self.n_experiments), dtype=int)

        for exp_idx, combo_list in self.solution_exp_stages.items():
            for combo_idx in combo_list:
                usage[combo_idx, exp_idx] += 1

        return usage

    def plot_usage_heatmap(self, filename: str = "heatmap_usage.png"):
        """
        Plot A: Heatmap showing combo usage across experiments.

        Args:
            filename: Output filename for the plot
        """
        usage = self._build_usage_matrix()

        fig, ax = plt.subplots(figsize=(10, 8))

        im = ax.imshow(usage, aspect='auto', cmap='Blues', vmin=0, vmax=2)

        # Configure axes
        ax.set_xlabel("Experiment", fontsize=14)
        ax.set_ylabel("Design Combination", fontsize=14)
        ax.set_title("Heatmap of Combo Usage in iDoE Plan", fontsize=16, pad=20)

        # Set tick labels
        exp_labels = [f"Exp{i+1}" for i in range(self.n_experiments)]
        combo_labels = [f"Combo{i+1}" for i in range(self.n_combos)]

        ax.set_xticks(range(self.n_experiments))
        ax.set_xticklabels(exp_labels)
        ax.set_yticks(range(self.n_combos))
        ax.set_yticklabels(combo_labels)

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Usage count", fontsize=12)

        # Save and display
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Saved: {output_path}")

    def plot_design_paths(self, filename: str = "design_paths.png"):
        """
        Plot B: Doehlert design space with experimental paths.

        Shows all design points and overlays each experiment's 3-stage path
        as a polyline connecting the design points in order.

        Args:
            filename: Output filename for the plot
        """
        fig, ax = plt.subplots(figsize=(12, 10))

        # Extract coordinates
        mu_values = self.combos[:, 0]
        temp_values = self.combos[:, 1]

        # Plot all design points
        ax.scatter(mu_values, temp_values, s=200, marker='D',
                  edgecolors='black', linewidths=2, zorder=3)

        # Annotate points with combo IDs
        # Handle overlapping center points (1, 2, 3)
        for i in range(self.n_combos):
            label = str(i + 1)
            # Check for overlapping points (center replicates)
            if i < 3:  # Combos 1, 2, 3 are center points
                if i == 0:
                    label = "1,2,3"
                    ax.annotate(label, (mu_values[i], temp_values[i]),
                              xytext=(0, -15), textcoords='offset points',
                              ha='center', fontsize=11, fontweight='bold')
            else:
                ax.annotate(label, (mu_values[i], temp_values[i]),
                          xytext=(0, -15), textcoords='offset points',
                          ha='center', fontsize=11, fontweight='bold')

        # Plot experimental paths
        for exp_idx in sorted(self.solution_exp_stages.keys()):
            combo_list = self.solution_exp_stages[exp_idx]
            path_mu = [self.combos[c][0] for c in combo_list]
            path_temp = [self.combos[c][1] for c in combo_list]

            ax.plot(path_mu, path_temp, marker='o', markersize=8,
                   linewidth=2, label=f"Exp{exp_idx+1}")

        # Configure axes and legend
        ax.set_xlabel("Specific Growth Rate μ_set (h^-1)", fontsize=14)
        ax.set_ylabel("Temperature (°C)", fontsize=14)
        ax.set_title("Doehlert Design and iDoE Experimental Paths",
                    fontsize=16, pad=20)
        ax.legend(loc='best', frameon=True, shadow=True)
        ax.grid(True, alpha=0.3, linestyle='--')

        # Save and display
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Saved: {output_path}")

    def plot_usage_heatmap_alt(self, filename: str = "heatmap_usage_alt.png"):
        """
        Plot C: Alternate heatmap with different axis labels.

        Same data as Plot A but with "Runs" and "Combos" terminology
        and a different colormap.

        Args:
            filename: Output filename for the plot
        """
        usage = self._build_usage_matrix()

        fig, ax = plt.subplots(figsize=(10, 8))

        im = ax.imshow(usage, aspect='auto', cmap='viridis', vmin=0, vmax=2)

        # Configure axes
        ax.set_xlabel("Runs", fontsize=14)
        ax.set_ylabel("Combos", fontsize=14)
        ax.set_title("Combo Usage Heatmap (Rows=Combos, Cols=Runs)",
                    fontsize=16, pad=20)

        # Set tick labels
        run_labels = [f"Run {i+1}" for i in range(self.n_experiments)]
        combo_labels = [f"Combo {i+1}" for i in range(self.n_combos)]

        ax.set_xticks(range(self.n_experiments))
        ax.set_xticklabels(run_labels)
        ax.set_yticks(range(self.n_combos))
        ax.set_yticklabels(combo_labels)

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Times used in Run", fontsize=12)

        # Save and display
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Saved: {output_path}")

    def plot_run_timeline(self, run_idx: int, filename: str = None):
        """
        Plot D: Timeline showing μ and Temperature profiles for a specific run.

        Creates a dual y-axis plot with step functions showing how parameters
        change across the 3 stages.

        Args:
            run_idx: 0-based run index
            filename: Optional custom filename (default: run_{N}_timeline.png)
        """
        if run_idx not in self.solution_exp_stages:
            print(f"Warning: Run {run_idx} has no stages assigned")
            return

        combo_list = self.solution_exp_stages[run_idx]

        # Build step vectors for time and parameters
        time_points = []
        mu_values = []
        temp_values = []

        for stage in range(self.n_stages):
            t_start = stage * self.per_stage_hours
            t_end = (stage + 1) * self.per_stage_hours

            combo_idx = combo_list[stage]
            mu, temp = self.combos[combo_idx]

            # Add duplicate points for step function
            time_points.extend([t_start, t_end])
            mu_values.extend([mu, mu])
            temp_values.extend([temp, temp])

        # Create figure with twin y-axes
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Plot μ_set on left y-axis
        color1 = 'tab:blue'
        ax1.set_xlabel("Time (h)", fontsize=14)
        ax1.set_ylabel("μ_set (h⁻¹)", fontsize=14, color=color1)
        line1 = ax1.plot(time_points, mu_values, linewidth=2.5,
                        color=color1, label="μ_set (h⁻¹)")
        ax1.tick_params(axis='y', labelcolor=color1)
        ax1.grid(True, alpha=0.3, linestyle='--')

        # Plot Temperature on right y-axis
        ax2 = ax1.twinx()
        color2 = 'tab:orange'
        ax2.set_ylabel("Temperature (°C)", fontsize=14, color=color2)
        line2 = ax2.plot(time_points, temp_values, linewidth=2.5,
                        color=color2, label="Temperature (°C)")
        ax2.tick_params(axis='y', labelcolor=color2)

        # Add title
        run_number = run_idx + 1
        ax1.set_title(f"Run {run_number}: μ and Temperature vs Time",
                     fontsize=16, pad=20)

        # Combined legend
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper right', frameon=True, shadow=True)

        # Save and display
        if filename is None:
            filename = f"run_{run_number}_timeline.png"
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Saved: {output_path}")

    def plot_all_run_timelines(self):
        """Generate timeline plots for all runs."""
        for run_idx in sorted(self.solution_exp_stages.keys()):
            self.plot_run_timeline(run_idx)

    def generate_all_plots(self):
        """Generate all visualization plots."""
        print("Generating all plots...")
        print()

        print("Plot A: Heatmap of Combo Usage")
        self.plot_usage_heatmap()
        print()

        print("Plot B: Doehlert Design and Experimental Paths")
        self.plot_design_paths()
        print()

        print("Plot C: Alternate Usage Heatmap")
        self.plot_usage_heatmap_alt()
        print()

        print("Plot D: Run Timelines")
        self.plot_all_run_timelines()
        print()

        print(f"All plots saved to: {self.output_dir.absolute()}")
