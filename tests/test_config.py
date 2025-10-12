"""Tests for configuration module."""

import numpy as np
import pytest

from src.config import (
    FACTOR_VALUES,
    NUM_STAGES,
    DELTA_F_MAX_MU,
    DELTA_F_MAX_TEMP,
    DELTA_F_MIN_MU,
    DELTA_F_MIN_TEMP,
    STAGE_WEIGHTS,
    BIG_M,
    BIG_L,
    get_repetition_targets
)


class TestConfig:
    """Test configuration constants and functions."""

    def test_factor_values_shape(self):
        """Test that factor values have correct shape."""
        assert FACTOR_VALUES.shape == (9, 2), "Factor values should have 9 combinations with 2 factors"

    def test_factor_values_content(self):
        """Test that factor values are within expected ranges."""
        mu_values = FACTOR_VALUES[:, 0]
        temp_values = FACTOR_VALUES[:, 1]

        assert np.all(mu_values >= 0.1) and np.all(mu_values <= 0.2), "Mu values out of expected range"
        assert np.all(temp_values >= 29.0) and np.all(temp_values <= 33.0), "Temperature values out of expected range"

    def test_num_stages(self):
        """Test that number of stages is correct."""
        assert NUM_STAGES == 3, "Number of stages should be 3"

    def test_delta_constraints(self):
        """Test that delta constraints are positive and max > min."""
        assert DELTA_F_MAX_MU > 0, "Max mu delta should be positive"
        assert DELTA_F_MAX_TEMP > 0, "Max temp delta should be positive"
        assert DELTA_F_MIN_MU > 0, "Min mu delta should be positive"
        assert DELTA_F_MIN_TEMP > 0, "Min temp delta should be positive"
        assert DELTA_F_MAX_MU > DELTA_F_MIN_MU, "Max mu delta should be greater than min"
        assert DELTA_F_MAX_TEMP > DELTA_F_MIN_TEMP, "Max temp delta should be greater than min"

    def test_stage_weights(self):
        """Test that stage weights are defined correctly."""
        assert len(STAGE_WEIGHTS) == NUM_STAGES, "Stage weights should match number of stages"
        assert all(w > 0 for w in STAGE_WEIGHTS.values()), "All stage weights should be positive"

    def test_big_m_constants(self):
        """Test that Big-M constants are properly sized."""
        assert BIG_M > BIG_L > 0, "Big-M constants should satisfy M > L > 0"
        assert BIG_M >= 100, "BIG_M should be sufficiently large"

    def test_get_repetition_targets(self):
        """Test repetition target generation."""
        targets = get_repetition_targets(9)

        assert len(targets) == 9, "Should have targets for all 9 combinations"
        assert targets[1] == targets[2] == targets[3] == 1, "Center points should have target of 1"
        assert all(targets[j] == 2 for j in range(4, 10)), "Other combinations should have target of 2"

    def test_get_repetition_targets_different_size(self):
        """Test repetition target generation with different number of combinations."""
        targets = get_repetition_targets(5)

        assert len(targets) == 5, "Should have targets for all combinations"
        assert targets[1] == targets[2] == targets[3] == 1, "Center points should have target of 1"
