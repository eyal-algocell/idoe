"""Tests for parameter_manager module."""

import pytest
import numpy as np
from src.parameter_manager import Parameter, ParameterManager, create_example_parameters


class TestParameter:
    """Test Parameter class."""

    def test_parameter_creation(self):
        """Test creating a parameter."""
        param = Parameter("Temperature", "°C", [29, 31, 33])

        assert param.name == "Temperature"
        assert param.units == "°C"
        assert param.values == [29, 31, 33]

    def test_parameter_values_sorted(self):
        """Test that parameter values are sorted."""
        param = Parameter("pH", "", [7.5, 6.5, 7.0])

        assert param.values == [6.5, 7.0, 7.5]


class TestParameterManager:
    """Test ParameterManager class."""

    def test_empty_manager(self):
        """Test empty parameter manager."""
        manager = ParameterManager()

        assert len(manager.parameters) == 0
        assert manager.get_num_combinations() == 0

    def test_add_parameter(self):
        """Test adding parameters."""
        manager = ParameterManager()
        manager.add_parameter("Temp", "°C", [29, 31])

        assert len(manager.parameters) == 1
        assert manager.parameters[0].name == "Temp"

    def test_add_multiple_parameters(self):
        """Test adding multiple parameters."""
        manager = ParameterManager()
        manager.add_parameter("Temp", "°C", [29, 31])
        manager.add_parameter("pH", "", [6.5, 7.0])

        assert len(manager.parameters) == 2
        assert manager.get_num_combinations() == 4  # 2 x 2

    def test_remove_parameter(self):
        """Test removing parameters."""
        manager = ParameterManager()
        manager.add_parameter("Temp", "°C", [29, 31])
        manager.add_parameter("pH", "", [6.5, 7.0])

        manager.remove_parameter(0)

        assert len(manager.parameters) == 1
        assert manager.parameters[0].name == "pH"

    def test_clear(self):
        """Test clearing all parameters."""
        manager = ParameterManager()
        manager.add_parameter("Temp", "°C", [29, 31])
        manager.add_parameter("pH", "", [6.5, 7.0])

        manager.clear()

        assert len(manager.parameters) == 0

    def test_combination_generation(self):
        """Test combination generation."""
        manager = ParameterManager()
        manager.add_parameter("Temp", "°C", [29, 31])
        manager.add_parameter("pH", "", [6.5, 7.0])

        combos = manager.generate_combinations()

        assert combos.shape == (4, 2)
        assert len(combos) == 4

        # Check all combinations present
        expected = np.array([
            [29, 6.5],
            [29, 7.0],
            [31, 6.5],
            [31, 7.0]
        ])

        np.testing.assert_array_equal(combos, expected)

    def test_combinations_dataframe(self):
        """Test DataFrame generation."""
        manager = ParameterManager()
        manager.add_parameter("Temp", "°C", [29, 31])
        manager.add_parameter("pH", "", [6.5, 7.0])

        df = manager.get_combinations_dataframe()

        assert len(df) == 4
        assert "Temp (°C)" in df.columns
        assert "pH" in df.columns
        assert df.index.name == "Combo #"
        assert df.index[0] == 1  # 1-based indexing

    def test_parameter_names(self):
        """Test getting parameter names."""
        manager = ParameterManager()
        manager.add_parameter("Temp", "°C", [29, 31])
        manager.add_parameter("pH", "", [6.5, 7.0])

        names = manager.get_parameter_names()

        assert names == ["Temp", "pH"]

    def test_parameter_units(self):
        """Test getting parameter units."""
        manager = ParameterManager()
        manager.add_parameter("Temp", "°C", [29, 31])
        manager.add_parameter("pH", "", [6.5, 7.0])

        units = manager.get_parameter_units()

        assert units == ["°C", ""]

    def test_parameter_ranges(self):
        """Test getting parameter ranges."""
        manager = ParameterManager()
        manager.add_parameter("Temp", "°C", [29, 31, 33])
        manager.add_parameter("pH", "", [6.5, 7.0])

        ranges = manager.get_parameter_ranges()

        assert ranges["Temp"] == (29, 33)
        assert ranges["pH"] == (6.5, 7.0)

    def test_validation_empty(self):
        """Test validation with no parameters."""
        manager = ParameterManager()

        is_valid, msg = manager.validate()

        assert not is_valid
        assert "at least one parameter" in msg.lower()

    def test_validation_no_name(self):
        """Test validation with missing name."""
        manager = ParameterManager()
        manager.add_parameter("", "°C", [29, 31])

        is_valid, msg = manager.validate()

        assert not is_valid
        assert "must have a name" in msg.lower()

    def test_validation_no_values(self):
        """Test validation with no values."""
        manager = ParameterManager()
        manager.add_parameter("Temp", "°C", [])

        is_valid, msg = manager.validate()

        assert not is_valid
        assert "at least one value" in msg.lower()

    def test_validation_duplicate_values(self):
        """Test validation with duplicate values."""
        manager = ParameterManager()
        manager.add_parameter("Temp", "°C", [29, 31, 29])

        is_valid, msg = manager.validate()

        assert not is_valid
        assert "duplicate" in msg.lower()

    def test_validation_duplicate_names(self):
        """Test validation with duplicate parameter names."""
        manager = ParameterManager()
        manager.add_parameter("Temp", "°C", [29, 31])
        manager.add_parameter("Temp", "K", [300, 310])

        is_valid, msg = manager.validate()

        assert not is_valid
        assert "unique" in msg.lower()

    def test_validation_too_many_combos(self):
        """Test validation with too many combinations."""
        manager = ParameterManager()
        # Create 201 combinations (> 200 limit)
        manager.add_parameter("P1", "", list(range(201)))

        is_valid, msg = manager.validate()

        assert not is_valid
        assert "too many" in msg.lower()

    def test_validation_success(self):
        """Test validation with valid configuration."""
        manager = ParameterManager()
        manager.add_parameter("Temp", "°C", [29, 31, 33])
        manager.add_parameter("pH", "", [6.5, 7.0])

        is_valid, msg = manager.validate()

        assert is_valid
        assert msg == ""

    def test_example_parameters(self):
        """Test example parameter creation."""
        manager = create_example_parameters()

        assert len(manager.parameters) == 2
        assert manager.get_num_combinations() == 15  # 3 temps x 5 mu values

        is_valid, _ = manager.validate()
        assert is_valid
