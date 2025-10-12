"""Table generation module for iDoE experimental plans.

Generates bench-ready tables showing:
- Per-run parameter schedules
- Combined summary table for all runs
- Export to CSV and Excel formats
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path

from .models import OptimizationResult


class IDOETableGenerator:
    """
    Generates experimental design tables for laboratory implementation.

    Tables include time windows, combo IDs, and parameter setpoints
    for each stage of each experiment.
    """

    def __init__(
        self,
        result: OptimizationResult,
        combos: np.ndarray,
        total_run_hours: float = 30.0,
        n_stages: int = 3,
        output_dir: str = "tables"
    ):
        """
        Initialize table generator with optimization results.

        Args:
            result: OptimizationResult object from optimizer
            combos: Array of shape (n_combos, 2) with (mu_set, temperature) pairs
            total_run_hours: Total duration of each experiment run
            n_stages: Number of stages per experiment
            output_dir: Directory to save table files
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

    def _format_time_window(self, stage: int) -> str:
        """
        Format time window string for a given stage.

        Args:
            stage: Stage number (0-based)

        Returns:
            Time window string in format "start–end" (e.g., "0.0–10.0")
        """
        t_start = stage * self.per_stage_hours
        t_end = (stage + 1) * self.per_stage_hours
        return f"{t_start:.1f}–{t_end:.1f}"

    def generate_run_table(self, run_idx: int) -> pd.DataFrame:
        """
        Generate parameter schedule table for a single run.

        Args:
            run_idx: 0-based run index

        Returns:
            DataFrame with columns: Run, Stage, Time (h), Combo #, μ_set (h⁻¹), Temperature (°C)
        """
        if run_idx not in self.solution_exp_stages:
            raise ValueError(f"Run {run_idx} has no stages assigned")

        combo_list = self.solution_exp_stages[run_idx]
        run_number = run_idx + 1

        rows = []
        for stage in range(self.n_stages):
            combo_idx = combo_list[stage]
            combo_number = combo_idx + 1  # 1-based
            mu_set, temperature = self.combos[combo_idx]

            row = {
                "Run": f"Run {run_number}",
                "Stage": f"Stage {stage + 1}",
                "Time (h)": self._format_time_window(stage),
                "Combo #": combo_number,
                "μ_set (h⁻¹)": round(mu_set, 4),
                "Temperature (°C)": round(temperature, 1)
            }
            rows.append(row)

        return pd.DataFrame(rows)

    def generate_all_run_tables(self) -> Dict[int, pd.DataFrame]:
        """
        Generate parameter schedule tables for all runs.

        Returns:
            Dict mapping run index to its DataFrame
        """
        tables = {}
        for run_idx in sorted(self.solution_exp_stages.keys()):
            tables[run_idx] = self.generate_run_table(run_idx)
        return tables

    def generate_combined_table(self) -> pd.DataFrame:
        """
        Generate combined summary table with all runs and stages.

        Returns:
            DataFrame with all runs concatenated, sorted by Run then Stage
        """
        all_tables = self.generate_all_run_tables()
        combined = pd.concat(all_tables.values(), ignore_index=True)
        return combined

    def display_run_table(self, run_idx: int):
        """
        Display parameter schedule table for a single run.

        Args:
            run_idx: 0-based run index
        """
        table = self.generate_run_table(run_idx)
        run_number = run_idx + 1
        print(f"\n{'=' * 80}")
        print(f"Run {run_number} - Parameter Schedule")
        print(f"{'=' * 80}")
        print(table.to_string(index=False))
        print()

    def display_all_run_tables(self):
        """Display parameter schedule tables for all runs."""
        for run_idx in sorted(self.solution_exp_stages.keys()):
            self.display_run_table(run_idx)

    def display_combined_table(self):
        """Display combined summary table."""
        combined = self.generate_combined_table()
        print(f"\n{'=' * 80}")
        print("Combined Summary - All Runs and Stages")
        print(f"{'=' * 80}")
        print(combined.to_string(index=False))
        print()

    def save_to_csv(self, filename: str = "idoe_plan_combined.csv"):
        """
        Save combined table to CSV file.

        Args:
            filename: Output CSV filename
        """
        combined = self.generate_combined_table()
        output_path = self.output_dir / filename
        combined.to_csv(output_path, index=False)
        print(f"Saved combined table to: {output_path}")

    def save_to_excel(self, filename: str = "idoe_plan_workbook.xlsx"):
        """
        Save tables to Excel workbook with multiple sheets.

        Creates a workbook with:
        - "Summary" sheet containing the combined table
        - One sheet per run (Run_1, Run_2, etc.)

        Args:
            filename: Output Excel filename
        """
        output_path = self.output_dir / filename

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Write combined summary sheet
            combined = self.generate_combined_table()
            combined.to_excel(writer, sheet_name='Summary', index=False)

            # Write individual run sheets
            run_tables = self.generate_all_run_tables()
            for run_idx in sorted(run_tables.keys()):
                run_number = run_idx + 1
                sheet_name = f'Run_{run_number}'
                run_tables[run_idx].to_excel(writer, sheet_name=sheet_name, index=False)

        print(f"Saved Excel workbook to: {output_path}")

    def validate_tables(self) -> bool:
        """
        Validate generated tables for correctness.

        Checks:
        - Row count matches expected (n_experiments * n_stages)
        - All combo numbers are in valid range [1, n_combos]
        - Time windows partition total_run_hours correctly
        - No missing values

        Returns:
            True if all validations pass
        """
        print("\nValidating tables...")

        combined = self.generate_combined_table()

        # Check row count
        expected_rows = self.n_experiments * self.n_stages
        actual_rows = len(combined)
        if actual_rows != expected_rows:
            print(f"❌ Row count mismatch: expected {expected_rows}, got {actual_rows}")
            return False
        print(f"✓ Row count correct: {actual_rows} rows")

        # Check combo numbers
        combo_numbers = combined["Combo #"].values
        if not all(1 <= c <= self.n_combos for c in combo_numbers):
            print(f"❌ Invalid combo numbers found")
            return False
        print(f"✓ All combo numbers in valid range [1, {self.n_combos}]")

        # Check for missing values
        if combined.isnull().any().any():
            print("❌ Missing values found")
            return False
        print("✓ No missing values")

        # Check time windows for each run
        for run_idx in sorted(self.solution_exp_stages.keys()):
            run_table = self.generate_run_table(run_idx)
            time_windows = run_table["Time (h)"].values

            # Parse time windows and check they partition correctly
            starts = []
            ends = []
            for tw in time_windows:
                start, end = tw.split('–')
                starts.append(float(start))
                ends.append(float(end))

            # Check continuity and coverage
            if starts[0] != 0.0:
                print(f"❌ Run {run_idx + 1}: first stage doesn't start at 0.0")
                return False

            if ends[-1] != self.total_run_hours:
                print(f"❌ Run {run_idx + 1}: last stage doesn't end at {self.total_run_hours}")
                return False

            for i in range(len(starts) - 1):
                if ends[i] != starts[i + 1]:
                    print(f"❌ Run {run_idx + 1}: gap or overlap between stages")
                    return False

        print(f"✓ Time windows partition {self.total_run_hours} hours correctly")

        # Validate combo parameter values match
        for _, row in combined.iterrows():
            combo_idx = row["Combo #"] - 1  # Convert to 0-based
            expected_mu, expected_temp = self.combos[combo_idx]

            actual_mu = row["μ_set (h⁻¹)"]
            actual_temp = row["Temperature (°C)"]

            if abs(actual_mu - expected_mu) > 1e-6:
                print(f"❌ μ_set mismatch for combo {row['Combo #']}")
                return False

            if abs(actual_temp - expected_temp) > 0.1:
                print(f"❌ Temperature mismatch for combo {row['Combo #']}")
                return False

        print("✓ All parameter values match combo definitions")

        print("\n✅ All validations passed!")
        return True

    def generate_all_outputs(self):
        """Generate all table outputs: display, CSV, and Excel."""
        print("=" * 80)
        print("GENERATING iDoE EXPERIMENTAL DESIGN TABLES")
        print("=" * 80)

        # Display per-run tables
        self.display_all_run_tables()

        # Display combined table
        self.display_combined_table()

        # Save to files
        print("Saving tables to files...")
        self.save_to_csv()
        self.save_to_excel()
        print()

        # Validate
        self.validate_tables()

        print(f"\nAll tables saved to: {self.output_dir.absolute()}")
