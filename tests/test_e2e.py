"""End-to-end tests for the complete iDoE workflow."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestE2E:
    """End-to-end tests for the complete application."""

    def test_main_module_runs(self):
        """Test that the main module can be run successfully."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        assert result.returncode == 0, f"Main module failed with: {result.stderr}"
        assert "Optimization Status: Optimal" in result.stdout
        assert "Experiment" in result.stdout

    def test_main_with_output_file(self, tmp_path):
        """Test that the main module can save results to a file."""
        output_file = tmp_path / "test_results.json"

        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--output", str(output_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        assert result.returncode == 0, f"Main module failed with: {result.stderr}"
        assert output_file.exists(), "Output file was not created"

        # Verify the output file is valid JSON
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert "status" in data
        assert "experiments" in data
        assert "objective_value" in data
        assert data["status"] == "Optimal"

    def test_output_file_structure(self, tmp_path):
        """Test that the output file has the correct structure."""
        output_file = tmp_path / "test_results.json"

        subprocess.run(
            [sys.executable, "-m", "src.main", "--output", str(output_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        with open(output_file, 'r') as f:
            data = json.load(f)

        # Check top-level structure
        assert isinstance(data["status"], str)
        assert isinstance(data["objective_value"], (int, float))
        assert isinstance(data["num_experiments_used"], int)
        assert isinstance(data["num_stages_used"], int)
        assert isinstance(data["experiments"], list)

        # Check experiment structure
        for exp in data["experiments"]:
            if len(exp["stages"]) > 0:  # Only check non-empty experiments
                assert "experiment_id" in exp
                assert "stages" in exp
                assert isinstance(exp["stages"], list)

                # Check stage structure
                for stage in exp["stages"]:
                    assert "stage" in stage
                    assert "combination" in stage
                    assert "mu_set" in stage
                    assert "temperature" in stage
                    assert isinstance(stage["stage"], int)
                    assert isinstance(stage["combination"], int)
                    assert isinstance(stage["mu_set"], (int, float))
                    assert isinstance(stage["temperature"], (int, float))

    def test_experiment_assignments_valid(self, tmp_path):
        """Test that experiment assignments are valid."""
        output_file = tmp_path / "test_results.json"

        subprocess.run(
            [sys.executable, "-m", "src.main", "--output", str(output_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        with open(output_file, 'r') as f:
            data = json.load(f)

        # Collect all combinations used
        combinations_used = set()
        for exp in data["experiments"]:
            for stage in exp["stages"]:
                combinations_used.add(stage["combination"])
                # Verify values are in expected ranges
                assert 0.1 <= stage["mu_set"] <= 0.2, f"Invalid mu_set value: {stage['mu_set']}"
                assert 29.0 <= stage["temperature"] <= 33.0, f"Invalid temperature: {stage['temperature']}"
                assert 1 <= stage["stage"] <= 3, f"Invalid stage number: {stage['stage']}"
                assert 1 <= stage["combination"] <= 9, f"Invalid combination number: {stage['combination']}"

        # Verify all 9 combinations are used at least once
        assert len(combinations_used) == 9, f"Expected 9 combinations, got {len(combinations_used)}"

    def test_verbose_output(self):
        """Test that verbose mode produces solver output."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--verbose"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        assert result.returncode == 0, f"Main module failed with: {result.stderr}"
        # In verbose mode, we should see more output or at least the same output
        assert len(result.stdout) > 0

    def test_help_option(self):
        """Test that help option works."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        assert result.returncode == 0
        assert "iDoE" in result.stdout or "Intensified Design of Experiments" in result.stdout
        assert "--output" in result.stdout or "-o" in result.stdout
        assert "--verbose" in result.stdout or "-v" in result.stdout

    def test_multiple_runs_consistent(self, tmp_path):
        """Test that multiple runs produce consistent results."""
        output_file_1 = tmp_path / "results1.json"
        output_file_2 = tmp_path / "results2.json"

        # Run twice
        for output_file in [output_file_1, output_file_2]:
            subprocess.run(
                [sys.executable, "-m", "src.main", "--output", str(output_file)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )

        # Load both results
        with open(output_file_1, 'r') as f:
            data1 = json.load(f)
        with open(output_file_2, 'r') as f:
            data2 = json.load(f)

        # Results should be identical (deterministic solver)
        assert data1["status"] == data2["status"]
        assert data1["num_experiments_used"] == data2["num_experiments_used"]
        assert data1["num_stages_used"] == data2["num_stages_used"]
        # Objective values should be very close (allowing for floating point differences)
        assert abs(data1["objective_value"] - data2["objective_value"]) < 1e-6

    def test_efficiency_check(self, tmp_path):
        """Test that intensification actually reduces the number of experiments."""
        output_file = tmp_path / "results.json"

        subprocess.run(
            [sys.executable, "-m", "src.main", "--output", str(output_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        with open(output_file, 'r') as f:
            data = json.load(f)

        # We have 9 combinations. Without intensification, we'd need 9 experiments.
        # With intensification (3 stages), we should need fewer.
        assert data["num_experiments_used"] < 9, \
            f"Expected fewer than 9 experiments, got {data['num_experiments_used']}"

        # We should have at least 9 stages total (one per combination minimum)
        assert data["num_stages_used"] >= 9, \
            f"Expected at least 9 stages, got {data['num_stages_used']}"
