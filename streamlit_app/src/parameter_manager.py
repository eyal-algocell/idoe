"""Parameter management for the iDoE Streamlit app."""

import itertools
from typing import List, Dict, Tuple
import numpy as np
import pandas as pd


class Parameter:
    """Represents a single experimental parameter."""

    def __init__(self, name: str, units: str, values: List[float]):
        """
        Initialize a parameter.

        Args:
            name: Parameter name (e.g., "Temperature")
            units: Parameter units (e.g., "°C")
            values: List of discrete values for this parameter
        """
        self.name = name
        self.units = units
        self.values = sorted(values)  # Keep values sorted

    def __repr__(self):
        return f"Parameter('{self.name}', '{self.units}', {self.values})"


class ParameterManager:
    """Manages experimental parameters and generates combinations."""

    def __init__(self):
        """Initialize empty parameter manager."""
        self.parameters: List[Parameter] = []

    def add_parameter(self, name: str, units: str, values: List[float]):
        """Add a parameter to the manager."""
        self.parameters.append(Parameter(name, units, values))

    def remove_parameter(self, index: int):
        """Remove a parameter by index."""
        if 0 <= index < len(self.parameters):
            self.parameters.pop(index)

    def clear(self):
        """Remove all parameters."""
        self.parameters.clear()

    def get_num_combinations(self) -> int:
        """Get the total number of combinations."""
        if not self.parameters:
            return 0
        return np.prod([len(p.values) for p in self.parameters])

    def generate_combinations(self) -> np.ndarray:
        """
        Generate all parameter combinations as a 2D array.

        Returns:
            Array of shape (n_combinations, n_parameters)
        """
        if not self.parameters:
            return np.array([])

        # Create Cartesian product of all parameter values
        value_lists = [p.values for p in self.parameters]
        combinations = list(itertools.product(*value_lists))
        return np.array(combinations)

    def get_combinations_dataframe(self) -> pd.DataFrame:
        """
        Get combinations as a pandas DataFrame with parameter names as columns.

        Returns:
            DataFrame with columns for each parameter (with units in header)
        """
        combos = self.generate_combinations()
        if len(combos) == 0:
            return pd.DataFrame()

        # Create column names with units
        columns = [f"{p.name} ({p.units})" if p.units else p.name
                  for p in self.parameters]

        df = pd.DataFrame(combos, columns=columns)
        df.index = df.index + 1  # 1-based combo numbering
        df.index.name = "Combo #"
        return df

    def get_parameter_names(self) -> List[str]:
        """Get list of parameter names."""
        return [p.name for p in self.parameters]

    def get_parameter_units(self) -> List[str]:
        """Get list of parameter units."""
        return [p.units for p in self.parameters]

    def get_parameter_ranges(self) -> Dict[str, Tuple[float, float]]:
        """Get min/max range for each parameter."""
        return {
            p.name: (min(p.values), max(p.values))
            for p in self.parameters
        }

    def validate(self) -> Tuple[bool, str]:
        """
        Validate the parameter configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.parameters:
            return False, "Please add at least one parameter"

        for i, param in enumerate(self.parameters):
            if not param.name:
                return False, f"Parameter {i+1} must have a name"
            if not param.values:
                return False, f"Parameter '{param.name}' must have at least one value"
            if len(param.values) != len(set(param.values)):
                return False, f"Parameter '{param.name}' has duplicate values"

        # Check for duplicate parameter names
        names = [p.name for p in self.parameters]
        if len(names) != len(set(names)):
            return False, "Parameter names must be unique"

        # Warn if too many combinations
        n_combos = self.get_num_combinations()
        if n_combos > 200:
            return False, f"Too many combinations ({n_combos}). Consider reducing parameter values or number of parameters."

        return True, ""


def create_example_parameters() -> ParameterManager:
    """Create example parameter set (Temperature and μ_set)."""
    manager = ParameterManager()
    manager.add_parameter("Temperature", "°C", [29.0, 31.0, 33.0])
    manager.add_parameter("μ_set", "h⁻¹", [0.11, 0.1225, 0.135, 0.1475, 0.16])
    return manager
