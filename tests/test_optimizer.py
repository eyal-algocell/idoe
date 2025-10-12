"""Tests for the MILP optimizer."""

import numpy as np
import pytest

from src.optimizer import IDOEOptimizer
from src.config import FACTOR_VALUES


class TestIDOEOptimizer:
    """Test the iDoE optimizer."""

    def test_initialization_default(self):
        """Test optimizer initialization with default parameters."""
        optimizer = IDOEOptimizer()

        assert optimizer.num_combinations == 9
        assert optimizer.num_factors == 2
        assert optimizer.num_stages == 3
        assert optimizer.num_experiments == 27
        assert np.array_equal(optimizer.factor_values, FACTOR_VALUES)

    def test_initialization_custom(self):
        """Test optimizer initialization with custom parameters."""
        custom_factors = np.array([[0.1, 30.0], [0.15, 32.0]])
        optimizer = IDOEOptimizer(
            factor_values=custom_factors,
            num_stages=2,
            delta_f_max_mu=0.05,
            delta_f_max_temp=3.0,
            delta_f_min_mu=0.02,
            delta_f_min_temp=1.5
        )

        assert optimizer.num_combinations == 2
        assert optimizer.num_stages == 2
        assert optimizer.delta_f_max_mu == 0.05
        assert optimizer.delta_f_max_temp == 3.0
        assert optimizer.delta_f_min_mu == 0.02
        assert optimizer.delta_f_min_temp == 1.5

    def test_optimize_returns_result(self):
        """Test that optimize returns a valid result."""
        optimizer = IDOEOptimizer()
        result = optimizer.optimize(verbose=False)

        assert result is not None
        assert result.status is not None
        assert result.experiments is not None
        assert result.objective_value is not None
        assert result.num_experiments_used >= 0
        assert result.num_stages_used >= 0

    def test_optimize_status_optimal(self):
        """Test that optimization finds an optimal solution."""
        optimizer = IDOEOptimizer()
        result = optimizer.optimize(verbose=False)

        assert result.status == "Optimal", f"Expected Optimal status, got {result.status}"

    def test_all_combinations_covered(self):
        """Test that all DOE combinations are used at least once (C5 constraint)."""
        optimizer = IDOEOptimizer()
        result = optimizer.optimize(verbose=False)

        combinations_used = set()
        for exp in result.experiments:
            for stage in exp.stages:
                combinations_used.add(stage.combination)

        assert len(combinations_used) == 9, f"Expected all 9 combinations to be used, got {len(combinations_used)}"
        assert combinations_used == set(range(1, 10)), "Not all combinations from 1-9 were used"

    def test_combination_used_at_most_twice(self):
        """Test that each combination is used at most twice globally (C4 constraint)."""
        optimizer = IDOEOptimizer()
        result = optimizer.optimize(verbose=False)

        combination_counts = {}
        for exp in result.experiments:
            for stage in exp.stages:
                combo = stage.combination
                combination_counts[combo] = combination_counts.get(combo, 0) + 1

        for combo, count in combination_counts.items():
            assert count <= 2, f"Combination {combo} was used {count} times (max should be 2)"

    def test_one_combination_per_stage(self):
        """Test that each experiment has at most one combination per stage (C1 constraint)."""
        optimizer = IDOEOptimizer()
        result = optimizer.optimize(verbose=False)

        for exp in result.experiments:
            if not exp.is_empty():
                stages_used = [stage.stage for stage in exp.stages]
                assert len(stages_used) == len(set(stages_used)), \
                    f"Experiment {exp.experiment_id} has duplicate stage assignments"

    def test_sequential_changes_within_limits(self):
        """Test that sequential stage changes respect maximum limits (C7 constraint)."""
        optimizer = IDOEOptimizer()
        result = optimizer.optimize(verbose=False)

        for exp in result.experiments:
            if len(exp.stages) >= 2:
                sorted_stages = sorted(exp.stages, key=lambda s: s.stage)
                for i in range(len(sorted_stages) - 1):
                    current = sorted_stages[i]
                    next_stage = sorted_stages[i + 1]

                    mu_diff = abs(current.mu_set - next_stage.mu_set)
                    temp_diff = abs(current.temperature - next_stage.temperature)

                    assert mu_diff <= optimizer.delta_f_max_mu, \
                        f"Mu change {mu_diff} exceeds max {optimizer.delta_f_max_mu} in experiment {exp.experiment_id}"
                    assert temp_diff <= optimizer.delta_f_max_temp, \
                        f"Temp change {temp_diff} exceeds max {optimizer.delta_f_max_temp} in experiment {exp.experiment_id}"

    def test_result_to_dict(self):
        """Test that result can be converted to dictionary."""
        optimizer = IDOEOptimizer()
        result = optimizer.optimize(verbose=False)

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "status" in result_dict
        assert "objective_value" in result_dict
        assert "num_experiments_used" in result_dict
        assert "num_stages_used" in result_dict
        assert "experiments" in result_dict
        assert isinstance(result_dict["experiments"], list)

    def test_experiments_used_count(self):
        """Test that the number of experiments used is counted correctly."""
        optimizer = IDOEOptimizer()
        result = optimizer.optimize(verbose=False)

        non_empty_count = sum(1 for exp in result.experiments if not exp.is_empty())

        assert result.num_experiments_used == non_empty_count, \
            f"Mismatch in experiments used count: {result.num_experiments_used} vs {non_empty_count}"

    def test_stages_used_count(self):
        """Test that the number of stages used is counted correctly."""
        optimizer = IDOEOptimizer()
        result = optimizer.optimize(verbose=False)

        total_stages = sum(len(exp.stages) for exp in result.experiments)

        assert result.num_stages_used == total_stages, \
            f"Mismatch in stages used count: {result.num_stages_used} vs {total_stages}"

    def test_minimum_experiments_used(self):
        """Test that the optimizer minimizes the number of experiments."""
        optimizer = IDOEOptimizer()
        result = optimizer.optimize(verbose=False)

        # With 9 combinations and up to 2 uses per combination,
        # and 3 stages per experiment, we should use fewer than 9 experiments
        assert result.num_experiments_used < 9, \
            f"Expected fewer than 9 experiments due to intensification, got {result.num_experiments_used}"
        assert result.num_experiments_used >= 3, \
            f"Expected at least 3 experiments, got {result.num_experiments_used}"

    def test_objective_value_positive(self):
        """Test that objective value is positive."""
        optimizer = IDOEOptimizer()
        result = optimizer.optimize(verbose=False)

        assert result.objective_value > 0, "Objective value should be positive"

    def test_combination_at_most_twice_per_experiment(self):
        """Test that a combination appears at most twice in a single experiment (C3 constraint)."""
        optimizer = IDOEOptimizer()
        result = optimizer.optimize(verbose=False)

        for exp in result.experiments:
            if not exp.is_empty():
                combo_counts = {}
                for stage in exp.stages:
                    combo = stage.combination
                    combo_counts[combo] = combo_counts.get(combo, 0) + 1

                for combo, count in combo_counts.items():
                    assert count <= 2, \
                        f"Combination {combo} appears {count} times in experiment {exp.experiment_id} (max should be 2)"
