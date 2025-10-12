"""Tests for data models."""

import pytest

from src.models import StageAssignment, Experiment, OptimizationResult


class TestStageAssignment:
    """Test StageAssignment model."""

    def test_creation(self):
        """Test creating a stage assignment."""
        stage = StageAssignment(stage=1, combination=5, mu_set=0.135, temperature=31.0)

        assert stage.stage == 1
        assert stage.combination == 5
        assert stage.mu_set == 0.135
        assert stage.temperature == 31.0

    def test_string_representation(self):
        """Test string representation of stage assignment."""
        stage = StageAssignment(stage=2, combination=3, mu_set=0.1475, temperature=33.0)
        expected = "Stage 2: Combo 3 (μ_set=0.1475, Temp=33.0°C)"

        assert str(stage) == expected


class TestExperiment:
    """Test Experiment model."""

    def test_creation_empty(self):
        """Test creating an empty experiment."""
        exp = Experiment(experiment_id=1, stages=[])

        assert exp.experiment_id == 1
        assert len(exp.stages) == 0
        assert exp.is_empty()

    def test_creation_with_stages(self):
        """Test creating an experiment with stages."""
        stages = [
            StageAssignment(stage=1, combination=1, mu_set=0.135, temperature=31.0),
            StageAssignment(stage=2, combination=2, mu_set=0.14, temperature=32.0)
        ]
        exp = Experiment(experiment_id=1, stages=stages)

        assert exp.experiment_id == 1
        assert len(exp.stages) == 2
        assert not exp.is_empty()

    def test_string_representation(self):
        """Test string representation of experiment."""
        stages = [
            StageAssignment(stage=1, combination=1, mu_set=0.135, temperature=31.0)
        ]
        exp = Experiment(experiment_id=1, stages=stages)
        result = str(exp)

        assert "Experiment 1:" in result
        assert "Stage 1: Combo 1" in result


class TestOptimizationResult:
    """Test OptimizationResult model."""

    def test_creation(self):
        """Test creating an optimization result."""
        stages = [
            StageAssignment(stage=1, combination=1, mu_set=0.135, temperature=31.0)
        ]
        experiments = [Experiment(experiment_id=1, stages=stages)]
        result = OptimizationResult(
            status="Optimal",
            experiments=experiments,
            objective_value=0.123,
            num_experiments_used=1,
            num_stages_used=1
        )

        assert result.status == "Optimal"
        assert len(result.experiments) == 1
        assert result.objective_value == 0.123
        assert result.num_experiments_used == 1
        assert result.num_stages_used == 1

    def test_to_dict(self):
        """Test converting result to dictionary."""
        stages = [
            StageAssignment(stage=1, combination=1, mu_set=0.135, temperature=31.0)
        ]
        experiments = [Experiment(experiment_id=1, stages=stages)]
        result = OptimizationResult(
            status="Optimal",
            experiments=experiments,
            objective_value=0.123,
            num_experiments_used=1,
            num_stages_used=1
        )

        result_dict = result.to_dict()

        assert result_dict["status"] == "Optimal"
        assert result_dict["objective_value"] == 0.123
        assert result_dict["num_experiments_used"] == 1
        assert result_dict["num_stages_used"] == 1
        assert len(result_dict["experiments"]) == 1
        assert result_dict["experiments"][0]["experiment_id"] == 1
        assert len(result_dict["experiments"][0]["stages"]) == 1

    def test_string_representation(self):
        """Test string representation of result."""
        stages = [
            StageAssignment(stage=1, combination=1, mu_set=0.135, temperature=31.0)
        ]
        experiments = [Experiment(experiment_id=1, stages=stages)]
        result = OptimizationResult(
            status="Optimal",
            experiments=experiments,
            objective_value=0.123456,
            num_experiments_used=1,
            num_stages_used=1
        )

        result_str = str(result)

        assert "Optimization Status: Optimal" in result_str
        assert "Objective Value: 0.123456" in result_str
        assert "Number of Experiments Used: 1" in result_str
        assert "Total Stages Used: 1" in result_str
        assert "Experiment 1:" in result_str
