"""Main entry point for the iDoE planner application."""

import argparse
import json
import sys
from pathlib import Path

from .optimizer import IDOEOptimizer


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Intensified Design of Experiments (iDoE) Optimizer"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path for results (JSON format)",
        default=None
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose solver output"
    )
    return parser.parse_args()


def save_results(result, output_path: str) -> None:
    """
    Save optimization results to a JSON file.

    Args:
        result: OptimizationResult object
        output_path: Path to save the JSON file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)

    print(f"\nResults saved to: {output_file}")


def main() -> int:
    """
    Main function to run the iDoE optimization.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = parse_arguments()

    try:
        print("Initializing iDoE Optimizer...")
        optimizer = IDOEOptimizer()

        print("Running optimization...")
        result = optimizer.optimize(verbose=args.verbose)

        print("\n" + "=" * 80)
        print(result)
        print("=" * 80)

        if args.output:
            save_results(result, args.output)

        if result.status != "Optimal":
            print(f"\nWarning: Optimization status is '{result.status}'", file=sys.stderr)
            return 1

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
