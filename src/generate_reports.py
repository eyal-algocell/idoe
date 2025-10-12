"""Generate complete visualization and documentation reports for iDoE results.

This script runs the optimizer and generates:
1. All visualization plots (heatmaps, design paths, timelines)
2. All experimental design tables (per-run and combined)
3. Export to CSV and Excel formats

Usage:
    python -m src.generate_reports [--output-dir DIR]
"""

import argparse
import sys
from pathlib import Path

from .optimizer import IDOEOptimizer
from .config import FACTOR_VALUES
from .visualization import IDOEVisualizer
from .tables import IDOETableGenerator


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate iDoE visualization plots and experimental design tables"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="reports",
        help="Base directory for output files (default: reports)"
    )
    parser.add_argument(
        "--total-hours",
        type=float,
        default=30.0,
        help="Total run hours for each experiment (default: 30.0)"
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip plot generation"
    )
    parser.add_argument(
        "--no-tables",
        action="store_true",
        help="Skip table generation"
    )
    return parser.parse_args()


def main() -> int:
    """
    Main function to generate reports.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = parse_arguments()

    try:
        print("=" * 80)
        print("iDoE OPTIMIZER - REPORT GENERATION")
        print("=" * 80)
        print()

        # Step 1: Run optimization
        print("Step 1: Running optimization...")
        optimizer = IDOEOptimizer()
        result = optimizer.optimize(verbose=False)

        print(f"  Status: {result.status}")
        print(f"  Experiments used: {result.num_experiments_used}")
        print(f"  Total stages: {result.num_stages_used}")
        print(f"  Objective value: {result.objective_value:.6f}")
        print()

        if result.status != "Optimal":
            print(f"Warning: Optimization status is '{result.status}'", file=sys.stderr)

        # Create output directories
        base_dir = Path(args.output_dir)
        base_dir.mkdir(parents=True, exist_ok=True)
        plots_dir = base_dir / "plots"
        tables_dir = base_dir / "tables"

        # Step 2: Generate visualizations
        if not args.no_plots:
            print("Step 2: Generating visualization plots...")
            visualizer = IDOEVisualizer(
                result=result,
                combos=FACTOR_VALUES,
                total_run_hours=args.total_hours,
                output_dir=str(plots_dir)
            )
            visualizer.generate_all_plots()
            print()

        # Step 3: Generate tables
        if not args.no_tables:
            print("Step 3: Generating experimental design tables...")
            table_gen = IDOETableGenerator(
                result=result,
                combos=FACTOR_VALUES,
                total_run_hours=args.total_hours,
                output_dir=str(tables_dir)
            )
            table_gen.generate_all_outputs()
            print()

        # Summary
        print("=" * 80)
        print("REPORT GENERATION COMPLETE")
        print("=" * 80)
        print(f"\nOutput directory: {base_dir.absolute()}")

        if not args.no_plots:
            print(f"  Plots: {plots_dir.absolute()}")
        if not args.no_tables:
            print(f"  Tables: {tables_dir.absolute()}")

        print("\nGenerated files:")
        if not args.no_plots:
            print("  - heatmap_usage.png")
            print("  - design_paths.png")
            print("  - heatmap_usage_alt.png")
            for i in range(1, result.num_experiments_used + 1):
                print(f"  - run_{i}_timeline.png")

        if not args.no_tables:
            print("  - idoe_plan_combined.csv")
            print("  - idoe_plan_workbook.xlsx")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
