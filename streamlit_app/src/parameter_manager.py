"""Parameter management for the iDoE Streamlit app."""

import itertools
from typing import List, Dict, Tuple
import numpy as np
import pandas as pd
import io


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

    def load_from_dataframe(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Load combinations from a DataFrame and extract parameters.

        Expected format:
        - First column is ignored (Combo #)
        - Other columns: "Parameter Name (Unit)" or just "Parameter Name"
        - Each row is a combination

        Args:
            df: DataFrame with combinations

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Clear existing parameters
            self.clear()

            # Skip first column if it looks like an index
            data_df = df.copy()
            if data_df.columns[0].lower() in ['combo #', 'combo', '#', 'index']:
                data_df = data_df.iloc[:, 1:]

            # Parse parameter names and units from columns
            for col in data_df.columns:
                col_str = str(col)

                # Extract name and units
                if '(' in col_str and ')' in col_str:
                    name = col_str[:col_str.index('(')].strip()
                    units = col_str[col_str.index('(') + 1:col_str.index(')')].strip()
                else:
                    name = col_str.strip()
                    units = ""

                # Get unique values for this parameter
                values = sorted(data_df[col].dropna().unique())

                if len(values) == 0:
                    return False, f"Parameter '{name}' has no values"

                # Convert to float
                try:
                    values = [float(v) for v in values]
                except ValueError:
                    return False, f"Parameter '{name}' contains non-numeric values"

                self.add_parameter(name, units, values)

            return True, ""

        except Exception as e:
            return False, f"Error loading CSV: {str(e)}"


def create_example_parameters() -> ParameterManager:
    """Create example parameter set (Temperature and μ_set)."""
    manager = ParameterManager()
    manager.add_parameter("Temperature", "°C", [29.0, 31.0, 33.0])
    manager.add_parameter("μ_set", "h⁻¹", [0.11, 0.1225, 0.135, 0.1475, 0.16])
    return manager


def generate_example_csv() -> str:
    """
    Generate an example CSV string showing the expected format.

    Returns:
        CSV string with example data
    """
    manager = create_example_parameters()
    df = manager.get_combinations_dataframe()
    return df.to_csv()
