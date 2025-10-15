"""Tests for parameter_manager module."""

import pytest
import numpy as np
import pandas as pd
import io
from src.parameter_manager import Parameter, ParameterManager, create_example_parameters, generate_example_csv


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


class TestCSVFunctionality:
    """Test CSV import/export functionality."""

    def test_generate_example_csv(self):
        """Test that example CSV is generated correctly."""
        csv_string = generate_example_csv()

        assert csv_string is not None
        assert "Combo #" in csv_string
        assert "Temperature" in csv_string
        assert "μ_set" in csv_string

        # Verify it can be read back as DataFrame
        df = pd.read_csv(io.StringIO(csv_string))
        assert len(df) == 15  # 3 temps x 5 mu values
        assert len(df.columns) == 3  # Combo #, Temperature, μ_set

    def test_load_from_dataframe_with_index_column(self):
        """Test loading parameters from DataFrame with index column."""
        csv_data = """Combo #,Temperature (°C),pH
1,29.0,6.5
2,29.0,7.0
3,31.0,6.5
4,31.0,7.0
"""
        df = pd.read_csv(io.StringIO(csv_data))
        manager = ParameterManager()

        success, error_msg = manager.load_from_dataframe(df)

        assert success
        assert error_msg == ""
        assert len(manager.parameters) == 2
        assert manager.parameters[0].name == "Temperature"
        assert manager.parameters[0].units == "°C"
        assert manager.parameters[0].values == [29.0, 31.0]
        assert manager.parameters[1].name == "pH"
        assert manager.parameters[1].units == ""
        assert manager.parameters[1].values == [6.5, 7.0]

    def test_load_from_dataframe_without_index_column(self):
        """Test loading parameters from DataFrame without index column."""
        csv_data = """Temperature (°C),pH
29.0,6.5
29.0,7.0
31.0,6.5
31.0,7.0
"""
        df = pd.read_csv(io.StringIO(csv_data))
        manager = ParameterManager()

        success, error_msg = manager.load_from_dataframe(df)

        assert success
        assert error_msg == ""
        assert len(manager.parameters) == 2
        assert manager.parameters[0].name == "Temperature"
        assert manager.parameters[0].units == "°C"
        assert manager.parameters[0].values == [29.0, 31.0]

    def test_load_from_dataframe_case_insensitive_index(self):
        """Test that index column detection is case-insensitive."""
        csv_data = """combo #,Temperature (°C),pH
1,29.0,6.5
2,31.0,7.0
"""
        df = pd.read_csv(io.StringIO(csv_data))
        manager = ParameterManager()

        success, error_msg = manager.load_from_dataframe(df)

        assert success
        assert len(manager.parameters) == 2
        # Should skip the "combo #" column

    def test_load_from_dataframe_no_units(self):
        """Test loading parameters without units."""
        csv_data = """Combo #,Temperature,pH
1,29.0,6.5
2,31.0,7.0
"""
        df = pd.read_csv(io.StringIO(csv_data))
        manager = ParameterManager()

        success, error_msg = manager.load_from_dataframe(df)

        assert success
        assert manager.parameters[0].units == ""
        assert manager.parameters[1].units == ""

    def test_load_from_dataframe_replaces_existing(self):
        """Test that loading CSV replaces existing parameters."""
        manager = ParameterManager()
        manager.add_parameter("OldParam", "unit", [1.0, 2.0])

        csv_data = """Temperature (°C)
29.0
31.0
"""
        df = pd.read_csv(io.StringIO(csv_data))
        success, error_msg = manager.load_from_dataframe(df)

        assert success
        assert len(manager.parameters) == 1
        assert manager.parameters[0].name == "Temperature"

    def test_load_from_dataframe_invalid_non_numeric(self):
        """Test error handling for non-numeric values."""
        csv_data = """Temperature (°C)
29.0
hot
31.0
"""
        df = pd.read_csv(io.StringIO(csv_data))
        manager = ParameterManager()

        success, error_msg = manager.load_from_dataframe(df)

        assert not success
        assert "non-numeric" in error_msg.lower()

    def test_load_from_dataframe_empty_column(self):
        """Test error handling for empty parameter column."""
        csv_data = """Temperature (°C),pH


"""
        df = pd.read_csv(io.StringIO(csv_data))
        manager = ParameterManager()

        success, error_msg = manager.load_from_dataframe(df)

        assert not success
        assert "no values" in error_msg.lower()

    def test_load_from_dataframe_three_parameters(self):
        """Test loading with three parameters."""
        csv_data = """Combo #,Temp (°C),pH,DO (%)
1,29.0,6.5,20.0
2,29.0,6.5,40.0
3,29.0,7.0,20.0
4,29.0,7.0,40.0
5,31.0,6.5,20.0
6,31.0,6.5,40.0
7,31.0,7.0,20.0
8,31.0,7.0,40.0
"""
        df = pd.read_csv(io.StringIO(csv_data))
        manager = ParameterManager()

        success, error_msg = manager.load_from_dataframe(df)

        assert success
        assert len(manager.parameters) == 3
        assert manager.get_num_combinations() == 8

    def test_roundtrip_csv_export_import(self):
        """Test that exporting and importing CSV preserves parameters."""
        # Create original manager
        original = ParameterManager()
        original.add_parameter("Temperature", "°C", [29.0, 31.0, 33.0])
        original.add_parameter("pH", "", [6.5, 7.0])

        # Export to CSV
        df_exported = original.get_combinations_dataframe()
        csv_string = df_exported.to_csv()

        # Import into new manager
        df_imported = pd.read_csv(io.StringIO(csv_string))
        new_manager = ParameterManager()
        success, error_msg = new_manager.load_from_dataframe(df_imported)

        # Verify
        assert success
        assert len(new_manager.parameters) == len(original.parameters)
        assert new_manager.get_num_combinations() == original.get_num_combinations()

        for orig_param, new_param in zip(original.parameters, new_manager.parameters):
            assert orig_param.name == new_param.name
            assert orig_param.units == new_param.units
            assert orig_param.values == new_param.values
