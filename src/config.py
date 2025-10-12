"""Configuration and constants for the iDoE planner."""

import numpy as np
from typing import Dict


# DOE factor values (mu_set and temperature combinations)
FACTOR_VALUES = np.array([
    [0.135, 31.0],   # Combination 1 (center point)
    [0.135, 31.0],   # Combination 2 (center point)
    [0.135, 31.0],   # Combination 3 (center point)
    [0.16, 31.0],    # Combination 4
    [0.1475, 33.0],  # Combination 5
    [0.11, 31.0],    # Combination 6
    [0.1225, 29.0],  # Combination 7
    [0.1475, 29.0],  # Combination 8
    [0.1225, 33.0]   # Combination 9
])

# Problem parameters
NUM_STAGES = 3

# Maximum step change allowed between sequential stages
DELTA_F_MAX_MU = 0.03      # mu_set maximum difference
DELTA_F_MAX_TEMP = 2       # temperature maximum difference (°C)

# Minimum step change required between sequential stages
DELTA_F_MIN_MU = 0.01      # mu_set minimum difference
DELTA_F_MIN_TEMP = 1       # temperature minimum difference (°C)

# Stage weights for C6 constraint (weighted stage repetition)
STAGE_WEIGHTS: Dict[int, int] = {1: 1, 2: 1, 3: 1}

# Big-M constants for C8 constraint (minimum variation)
BIG_M = 1000
BIG_L = 500


def get_repetition_targets(num_combinations: int) -> Dict[int, int]:
    """
    Get the minimum repetition target for each DOE combination.

    Center-point combinations (1-3) have lower targets as they were
    replicated in the original DOE.

    Args:
        num_combinations: Total number of DOE combinations

    Returns:
        Dictionary mapping combination index to repetition target
    """
    targets = {j: 2 for j in range(1, num_combinations + 1)}
    # Lower targets for center-point combinations
    targets[1] = targets[2] = targets[3] = 1
    return targets
