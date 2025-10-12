"""MILP optimizer for intensified Design of Experiments (iDoE)."""

import numpy as np
import pulp
from typing import Optional

from .config import (
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
from .models import OptimizationResult, Experiment, StageAssignment


class IDOEOptimizer:
    """
    Optimizer for intensified Design of Experiments (iDoE).

    This optimizer minimizes the number of experiments needed while ensuring
    all DOE combinations are covered and constraints are satisfied.
    """

    def __init__(
        self,
        factor_values: Optional[np.ndarray] = None,
        num_stages: int = NUM_STAGES,
        delta_f_max_mu: float = DELTA_F_MAX_MU,
        delta_f_max_temp: float = DELTA_F_MAX_TEMP,
        delta_f_min_mu: float = DELTA_F_MIN_MU,
        delta_f_min_temp: float = DELTA_F_MIN_TEMP
    ):
        """
        Initialize the optimizer with problem parameters.

        Args:
            factor_values: Array of DOE combinations [mu_set, temperature]
            num_stages: Number of stages per experiment
            delta_f_max_mu: Maximum allowed mu_set change between stages
            delta_f_max_temp: Maximum allowed temperature change between stages
            delta_f_min_mu: Minimum required mu_set change per experiment
            delta_f_min_temp: Minimum required temperature change per experiment
        """
        self.factor_values = factor_values if factor_values is not None else FACTOR_VALUES
        self.num_combinations = len(self.factor_values)
        self.num_factors = self.factor_values.shape[1]
        self.num_stages = num_stages
        self.num_experiments = self.num_combinations * self.num_stages

        self.delta_f_max_mu = delta_f_max_mu
        self.delta_f_max_temp = delta_f_max_temp
        self.delta_f_min_mu = delta_f_min_mu
        self.delta_f_min_temp = delta_f_min_temp

        self.problem: Optional[pulp.LpProblem] = None
        self.x: Optional[dict] = None
        self.z: Optional[dict] = None
        self.q: Optional[dict] = None

    def _create_decision_variables(self) -> None:
        """Create binary decision variables for the MILP problem."""
        # Main variable: x[i][j][k] = 1 if combo j is used at stage k of experiment i
        self.x = pulp.LpVariable.dicts(
            'x',
            (
                range(1, self.num_experiments + 1),
                range(1, self.num_combinations + 1),
                range(1, self.num_stages + 1)
            ),
            lowBound=0,
            upBound=1,
            cat='Binary'
        )

        # Helper variables for C8 constraint (minimum variation)
        self.z = pulp.LpVariable.dicts(
            'z',
            (range(1, self.num_experiments + 1), range(1, self.num_factors + 1)),
            lowBound=0,
            upBound=1,
            cat='Binary'
        )

        self.q = pulp.LpVariable.dicts(
            'q',
            (
                range(1, self.num_stages),
                range(1, self.num_experiments + 1),
                range(1, self.num_factors + 1)
            ),
            lowBound=0,
            upBound=1,
            cat='Binary'
        )

    def _add_objective_function(self) -> None:
        """Add the objective function to minimize experiment cost."""
        weights = (np.arange(1, self.num_experiments + 1) / float(self.num_combinations + 1)) ** 3

        self.problem += pulp.lpSum(
            weights[i - 1] * self.x[i][j][k]
            for i in range(1, self.num_experiments + 1)
            for j in range(1, self.num_combinations + 1)
            for k in range(1, self.num_stages + 1)
        ), "Minimize_Experiments_Cost"

    def _add_constraint_c1(self) -> None:
        """C1: Only one DOE combination per stage of an experiment."""
        for i in range(1, self.num_experiments + 1):
            for k in range(1, self.num_stages + 1):
                self.problem += (
                    pulp.lpSum(self.x[i][j][k] for j in range(1, self.num_combinations + 1)) <= 1,
                    f"C1_one_comb_per_stage(i{i}_k{k})"
                )

    def _add_constraint_c2(self) -> None:
        """C2: A DOE combination appears at most once at any stage position."""
        for j in range(1, self.num_combinations + 1):
            for k in range(1, self.num_stages + 1):
                self.problem += (
                    pulp.lpSum(self.x[i][j][k] for i in range(1, self.num_experiments + 1)) <= 1,
                    f"C2_unique_at_stage(j{j}_k{k})"
                )

    def _add_constraint_c3(self) -> None:
        """C3: A DOE combination may be used at most twice in a single experiment."""
        for i in range(1, self.num_experiments + 1):
            for j in range(1, self.num_combinations + 1):
                self.problem += (
                    pulp.lpSum(self.x[i][j][k] for k in range(1, self.num_stages + 1)) <= 2,
                    f"C3_max2_per_expt(i{i}_j{j})"
                )

    def _add_constraint_c4(self) -> None:
        """C4: A DOE combination may be used at most twice across all experiments."""
        for j in range(1, self.num_combinations + 1):
            self.problem += (
                pulp.lpSum(
                    self.x[i][j][k]
                    for i in range(1, self.num_experiments + 1)
                    for k in range(1, self.num_stages + 1)
                ) <= 2,
                f"C4_max2_global(j{j})"
            )

    def _add_constraint_c5(self) -> None:
        """C5: Every DOE combination must be used at least once."""
        for j in range(1, self.num_combinations + 1):
            self.problem += (
                pulp.lpSum(
                    self.x[i][j][k]
                    for i in range(1, self.num_experiments + 1)
                    for k in range(1, self.num_stages + 1)
                ) >= 1,
                f"C5_cover_all(j{j})"
            )

    def _add_constraint_c6(self) -> None:
        """C6: Weighted stage repetition for strategic distribution."""
        repetition_targets = get_repetition_targets(self.num_combinations)

        for j in range(1, self.num_combinations + 1):
            self.problem += (
                pulp.lpSum(
                    STAGE_WEIGHTS[k] * self.x[i][j][k]
                    for i in range(1, self.num_experiments + 1)
                    for k in range(1, self.num_stages + 1)
                ) >= repetition_targets[j],
                f"C6_weighted_repetition(j{j})"
            )

    def _add_constraint_c7(self) -> None:
        """C7: Sequential change limits between stages."""
        for i in range(1, self.num_experiments + 1):
            for k in range(1, self.num_stages):
                # Mu_set difference constraints
                self.problem += (
                    pulp.lpSum(self.factor_values[j - 1, 0] * self.x[i][j][k]
                              for j in range(1, self.num_combinations + 1))
                    - pulp.lpSum(self.factor_values[j - 1, 0] * self.x[i][j][k + 1]
                                for j in range(1, self.num_combinations + 1))
                    <= self.delta_f_max_mu,
                    f"C7_mu_diff(i{i}_stage{k}-{k + 1})"
                )

                self.problem += (
                    pulp.lpSum(self.factor_values[j - 1, 0] * self.x[i][j][k]
                              for j in range(1, self.num_combinations + 1))
                    - pulp.lpSum(self.factor_values[j - 1, 0] * self.x[i][j][k + 1]
                                for j in range(1, self.num_combinations + 1))
                    >= -self.delta_f_max_mu,
                    f"C7_mu_diff_neg(i{i}_stage{k}-{k + 1})"
                )

                # Temperature difference constraints
                self.problem += (
                    pulp.lpSum(self.factor_values[j - 1, 1] * self.x[i][j][k]
                              for j in range(1, self.num_combinations + 1))
                    - pulp.lpSum(self.factor_values[j - 1, 1] * self.x[i][j][k + 1]
                                for j in range(1, self.num_combinations + 1))
                    <= self.delta_f_max_temp,
                    f"C7_temp_diff(i{i}_stage{k}-{k + 1})"
                )

                self.problem += (
                    pulp.lpSum(self.factor_values[j - 1, 1] * self.x[i][j][k]
                              for j in range(1, self.num_combinations + 1))
                    - pulp.lpSum(self.factor_values[j - 1, 1] * self.x[i][j][k + 1]
                                for j in range(1, self.num_combinations + 1))
                    >= -self.delta_f_max_temp,
                    f"C7_temp_diff_neg(i{i}_stage{k}-{k + 1})"
                )

    def _add_constraint_c8(self) -> None:
        """C8: Minimum variation per experiment using Big-M formulation."""
        for i in range(1, self.num_experiments + 1):
            for l, delta_f_min in [(1, self.delta_f_min_mu), (2, self.delta_f_min_temp)]:
                # Compute factor differences between stages
                diff1 = (
                    pulp.lpSum(self.factor_values[j - 1, l - 1] * self.x[i][j][1]
                              for j in range(1, self.num_combinations + 1))
                    - pulp.lpSum(self.factor_values[j - 1, l - 1] * self.x[i][j][2]
                                for j in range(1, self.num_combinations + 1))
                )

                diff2 = (
                    pulp.lpSum(self.factor_values[j - 1, l - 1] * self.x[i][j][2]
                              for j in range(1, self.num_combinations + 1))
                    - pulp.lpSum(self.factor_values[j - 1, l - 1] * self.x[i][j][3]
                                for j in range(1, self.num_combinations + 1))
                )

                # Big-M constraints for k=1
                self.problem += (
                    diff1 + BIG_M * self.z[i][l] + BIG_L * (self.q[1][i][l] + self.q[2][i][l])
                    >= delta_f_min,
                    f"C8_min_var_k1(i{i}_l{l})"
                )

                self.problem += (
                    diff1 - BIG_M * self.z[i][l] + BIG_L * (self.q[1][i][l] + self.q[2][i][l])
                    >= delta_f_min - BIG_M,
                    f"C8_min_var_k1_alt(i{i}_l{l})"
                )

                # Big-M constraints for k=2
                self.problem += (
                    diff2 + BIG_M * self.z[i][l] - BIG_L * self.q[1][i][l] + BIG_L * self.q[2][i][l]
                    >= delta_f_min - BIG_L,
                    f"C8_min_var_k2(i{i}_l{l})"
                )

                self.problem += (
                    diff2 - BIG_M * self.z[i][l] - BIG_L * self.q[1][i][l] + BIG_L * self.q[2][i][l]
                    >= delta_f_min - BIG_M - BIG_L,
                    f"C8_min_var_k2_alt(i{i}_l{l})"
                )

    def _build_problem(self) -> None:
        """Build the complete MILP problem with all constraints."""
        self.problem = pulp.LpProblem("iDoE_Planner", pulp.LpMinimize)
        self._create_decision_variables()
        self._add_objective_function()
        self._add_constraint_c1()
        self._add_constraint_c2()
        self._add_constraint_c3()
        self._add_constraint_c4()
        self._add_constraint_c5()
        self._add_constraint_c6()
        self._add_constraint_c7()
        self._add_constraint_c8()

    def _extract_results(self) -> OptimizationResult:
        """Extract and format the optimization results."""
        experiments = []
        num_stages_used = 0

        for i in range(1, self.num_experiments + 1):
            stages = []
            for k in range(1, self.num_stages + 1):
                for j in range(1, self.num_combinations + 1):
                    if pulp.value(self.x[i][j][k]) == 1:
                        stage = StageAssignment(
                            stage=k,
                            combination=j,
                            mu_set=self.factor_values[j - 1, 0],
                            temperature=self.factor_values[j - 1, 1]
                        )
                        stages.append(stage)
                        num_stages_used += 1

            experiments.append(Experiment(experiment_id=i, stages=stages))

        non_empty_experiments = [exp for exp in experiments if not exp.is_empty()]

        return OptimizationResult(
            status=pulp.LpStatus[self.problem.status],
            experiments=experiments,
            objective_value=pulp.value(self.problem.objective),
            num_experiments_used=len(non_empty_experiments),
            num_stages_used=num_stages_used
        )

    def optimize(self, verbose: bool = False) -> OptimizationResult:
        """
        Run the MILP optimization to find the optimal iDoE plan.

        Args:
            verbose: If True, print solver output

        Returns:
            OptimizationResult containing the optimal experiment assignments
        """
        self._build_problem()
        self.problem.solve(pulp.PULP_CBC_CMD(msg=verbose))
        return self._extract_results()
