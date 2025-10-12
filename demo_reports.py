"""Demo script to test visualization and table generation without dependencies.

This creates a simple test to verify the modules work correctly.
"""

from src.optimizer import IDOEOptimizer
from src.config import FACTOR_VALUES
from src.visualization import IDOEVisualizer
from src.tables import IDOETableGenerator


def main():
    """Run a simple demo of the reporting functionality."""
    print("=" * 80)
    print("iDoE REPORTING DEMO")
    print("=" * 80)
    print()

    # Step 1: Run optimization
    print("Running optimization...")
    optimizer = IDOEOptimizer()
    result = optimizer.optimize(verbose=False)

    print(f"\nOptimization complete:")
    print(f"  Status: {result.status}")
    print(f"  Experiments: {result.num_experiments_used}")
    print(f"  Stages: {result.num_stages_used}")
    print(f"  Objective: {result.objective_value:.6f}")
    print()

    # Step 2: Generate tables (doesn't require matplotlib)
    print("=" * 80)
    print("GENERATING TABLES")
    print("=" * 80)

    table_gen = IDOETableGenerator(
        result=result,
        combos=FACTOR_VALUES,
        total_run_hours=30.0,
        output_dir="demo_tables"
    )

    # Display tables
    table_gen.display_all_run_tables()
    table_gen.display_combined_table()

    # Save to files
    print("Saving tables...")
    table_gen.save_to_csv()
    table_gen.save_to_excel()
    print()

    # Validate
    table_gen.validate_tables()
    print()

    # Step 3: Generate plots (requires matplotlib)
    try:
        print("=" * 80)
        print("GENERATING PLOTS")
        print("=" * 80)
        print()

        visualizer = IDOEVisualizer(
            result=result,
            combos=FACTOR_VALUES,
            total_run_hours=30.0,
            output_dir="demo_plots"
        )

        visualizer.generate_all_plots()

    except ImportError as e:
        print(f"Skipping plots (matplotlib not installed): {e}")
    except Exception as e:
        print(f"Error generating plots: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
