"""Optimizer wrapper for the iDoE Streamlit app."""

import numpy as np
import pulp
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Constraints:
    """Container for all C1-C8 constraints."""

    # C1: Always enforced
    c1_enabled: bool = True

    # C2: Unique combo per stage position
    c2_enabled: bool = True

    # C3: Max repeats per run
    c3_enabled: bool = True
    c3_max_per_run: int = 2

    # C4: Max repeats globally
    c4_enabled: bool = True
    c4_max_global: int = 2

    # C5: Cover all combos at least once
    c5_enabled: bool = True

    # C6: Weighted stage repetition
    c6_enabled: bool = True
    c6_target_stages: int = 2
    c6_stage_weights: Optional[Dict[int, float]] = None

    # C7: Max step change between stages (per parameter)
    c7_enabled: bool = True
    c7_max_changes: Optional[Dict[str, float]] = None

    # C8: Min total change per run (per parameter)
    c8_enabled: bool = True
    c8_min_changes: Optional[Dict[str, float]] = None


@dataclass
class OptimizationResult:
    """Container for optimization results."""

    status: str
    feasible: bool
    runs_used: int
    total_stages: int
    objective_value: float
    assignments: Dict[int, List[int]]  # run_idx -> [combo_idx per stage]
    infeasibility_hints: List[str]


class IDOEOptimizerWrapper:
    """
    Wrapper around MILP optimizer for Streamlit app.

    Provides parameter-agnostic optimization with configurable C1-C8 constraints.
    """

    def __init__(
        self,
        combinations: np.ndarray,
        parameter_names: List[str],
        num_runs: int,
        num_stages: int,
        constraints: Constraints
    ):
        """
        Initialize optimizer wrapper.

        Args:
            combinations: Array of shape (n_combos, n_params) with parameter values
            parameter_names: List of parameter names
            num_runs: Maximum number of runs
            num_stages: Number of stages per run
            constraints: Constraints configuration
        """
        self.combinations = combinations
        self.parameter_names = parameter_names
        self.n_combos = len(combinations)
        self.n_params = combinations.shape[1] if len(combinations) > 0 else 0
        self.num_runs = num_runs
        self.num_stages = num_stages
        self.constraints = constraints

        self.problem: Optional[pulp.LpProblem] = None
        self.x: Optional[dict] = None
        self.z: Optional[dict] = None
        self.q: Optional[dict] = None

    def _create_decision_variables(self):
        """Create binary decision variables."""
        # Main variable: x[i][j][k] = 1 if combo j used at stage k of run i
        self.x = pulp.LpVariable.dicts(
            'x',
            (range(self.num_runs), range(self.n_combos), range(self.num_stages)),
            cat='Binary'
        )

        # Helper variables for C8 (Big-M formulation)
        if self.constraints.c8_enabled:
            self.z = pulp.LpVariable.dicts(
                'z',
                (range(self.num_runs), range(self.n_params)),
                cat='Binary'
            )
            self.q = pulp.LpVariable.dicts(
                'q',
                (range(self.num_stages - 1), range(self.num_runs), range(self.n_params)),
                cat='Binary'
            )

    def _add_objective(self):
        """Add objective function to minimize number of runs used."""
        # Weight by run index to prefer using earlier runs
        weights = [(i + 1.0) / (self.num_runs + 1.0) ** 2
                   for i in range(self.num_runs)]

        self.problem += pulp.lpSum(
            weights[i] * self.x[i][j][k]
            for i in range(self.num_runs)
            for j in range(self.n_combos)
            for k in range(self.num_stages)
        ), "Minimize_Runs_Used"

    def _add_constraint_c1(self):
        """C1: Only one combo per stage per run."""
        for i in range(self.num_runs):
            for k in range(self.num_stages):
                self.problem += (
                    pulp.lpSum(self.x[i][j][k] for j in range(self.n_combos)) <= 1,
                    f"C1_one_combo_per_stage_r{i}_s{k}"
                )

    def _add_constraint_c2(self):
        """C2: Combo appears at most once at any stage position."""
        if not self.constraints.c2_enabled:
            return

        for j in range(self.n_combos):
            for k in range(self.num_stages):
                self.problem += (
                    pulp.lpSum(self.x[i][j][k] for i in range(self.num_runs)) <= 1,
                    f"C2_unique_at_stage_c{j}_s{k}"
                )

    def _add_constraint_c3(self):
        """C3: Combo used at most N times per run."""
        if not self.constraints.c3_enabled:
            return

        max_per_run = self.constraints.c3_max_per_run
        for i in range(self.num_runs):
            for j in range(self.n_combos):
                self.problem += (
                    pulp.lpSum(self.x[i][j][k] for k in range(self.num_stages)) <= max_per_run,
                    f"C3_max_per_run_r{i}_c{j}"
                )

    def _add_constraint_c4(self):
        """C4: Combo used at most M times globally."""
        if not self.constraints.c4_enabled:
            return

        max_global = self.constraints.c4_max_global
        for j in range(self.n_combos):
            self.problem += (
                pulp.lpSum(
                    self.x[i][j][k]
                    for i in range(self.num_runs)
                    for k in range(self.num_stages)
                ) <= max_global,
                f"C4_max_global_c{j}"
            )

    def _add_constraint_c5(self):
        """C5: Every combo used at least once."""
        if not self.constraints.c5_enabled:
            return

        for j in range(self.n_combos):
            self.problem += (
                pulp.lpSum(
                    self.x[i][j][k]
                    for i in range(self.num_runs)
                    for k in range(self.num_stages)
                ) >= 1,
                f"C5_cover_all_c{j}"
            )

    def _add_constraint_c6(self):
        """C6: Weighted stage repetition."""
        if not self.constraints.c6_enabled:
            return

        # Default equal weights if not specified
        if self.constraints.c6_stage_weights is None:
            stage_weights = {k: 1.0 for k in range(self.num_stages)}
        else:
            stage_weights = self.constraints.c6_stage_weights

        target = self.constraints.c6_target_stages

        for j in range(self.n_combos):
            self.problem += (
                pulp.lpSum(
                    stage_weights.get(k, 1.0) * self.x[i][j][k]
                    for i in range(self.num_runs)
                    for k in range(self.num_stages)
                ) >= target,
                f"C6_weighted_rep_c{j}"
            )

    def _add_constraint_c7(self):
        """C7: Limit step changes between consecutive stages."""
        if not self.constraints.c7_enabled or self.constraints.c7_max_changes is None:
            return

        for i in range(self.num_runs):
            for k in range(self.num_stages - 1):
                for p_idx, param_name in enumerate(self.parameter_names):
                    if param_name not in self.constraints.c7_max_changes:
                        continue

                    max_change = self.constraints.c7_max_changes[param_name]

                    # Difference in parameter p between stage k and k+1
                    diff = (
                        pulp.lpSum(
                            self.combinations[j, p_idx] * self.x[i][j][k]
                            for j in range(self.n_combos)
                        ) - pulp.lpSum(
                            self.combinations[j, p_idx] * self.x[i][j][k + 1]
                            for j in range(self.n_combos)
                        )
                    )

                    self.problem += (
                        diff <= max_change,
                        f"C7_max_step_r{i}_s{k}_p{p_idx}_pos"
                    )
                    self.problem += (
                        diff >= -max_change,
                        f"C7_max_step_r{i}_s{k}_p{p_idx}_neg"
                    )

    def _add_constraint_c8(self):
        """C8: Minimum total change per run using Big-M."""
        if not self.constraints.c8_enabled or self.constraints.c8_min_changes is None:
            return

        BIG_M = 1000
        BIG_L = 500

        for i in range(self.num_runs):
            for p_idx, param_name in enumerate(self.parameter_names):
                if param_name not in self.constraints.c8_min_changes:
                    continue

                min_change = self.constraints.c8_min_changes[param_name]

                # Compute differences for each stage transition
                for k in range(self.num_stages - 1):
                    diff = (
                        pulp.lpSum(
                            self.combinations[j, p_idx] * self.x[i][j][k]
                            for j in range(self.n_combos)
                        ) - pulp.lpSum(
                            self.combinations[j, p_idx] * self.x[i][j][k + 1]
                            for j in range(self.n_combos)
                        )
                    )

                    # Big-M constraints
                    self.problem += (
                        diff + BIG_M * self.z[i][p_idx] +
                        BIG_L * sum(self.q[kt][i][p_idx] for kt in range(self.num_stages - 1))
                        >= min_change,
                        f"C8_min_var_r{i}_s{k}_p{p_idx}_1"
                    )

                    self.problem += (
                        diff - BIG_M * self.z[i][p_idx] +
                        BIG_L * sum(self.q[kt][i][p_idx] for kt in range(self.num_stages - 1))
                        >= min_change - BIG_M,
                        f"C8_min_var_r{i}_s{k}_p{p_idx}_2"
                    )

    def _build_problem(self):
        """Build the complete MILP problem."""
        self.problem = pulp.LpProblem("iDoE_Plan", pulp.LpMinimize)
        self._create_decision_variables()
        self._add_objective()
        self._add_constraint_c1()
        self._add_constraint_c2()
        self._add_constraint_c3()
        self._add_constraint_c4()
        self._add_constraint_c5()
        self._add_constraint_c6()
        self._add_constraint_c7()
        self._add_constraint_c8()

    def _extract_assignments(self) -> Dict[int, List[int]]:
        """Extract combo assignments from solution."""
        assignments = {}

        for i in range(self.num_runs):
            run_assignments = []
            for k in range(self.num_stages):
                for j in range(self.n_combos):
                    if pulp.value(self.x[i][j][k]) == 1:
                        run_assignments.append(j)
                        break

            if run_assignments:  # Only include non-empty runs
                assignments[i] = run_assignments

        return assignments

    def _generate_infeasibility_hints(self) -> List[str]:
        """Generate user-friendly hints for infeasible problems."""
        hints = []

        if self.constraints.c5_enabled and self.n_combos > self.num_runs * self.num_stages:
            hints.append(f"⚠️ You have {self.n_combos} combinations but only {self.num_runs * self.num_stages} total stage slots. Try increasing number of runs.")

        if self.constraints.c2_enabled and self.n_combos > self.num_runs:
            hints.append("⚠️ C2 (unique combo per stage position) may be too restrictive. Try disabling C2.")

        if self.constraints.c7_enabled and self.constraints.c7_max_changes:
            hints.append("⚠️ C7 (max step changes) may be too restrictive. Try increasing the allowed step sizes.")

        if self.constraints.c8_enabled and self.constraints.c8_min_changes:
            hints.append("⚠️ C8 (min total changes) may be too demanding. Try reducing the minimum required changes.")

        if self.constraints.c6_enabled and self.constraints.c6_target_stages > 1:
            hints.append(f"⚠️ C6 requires each combo in {self.constraints.c6_target_stages} different stages, which may be infeasible. Try reducing target stages.")

        if self.constraints.c4_enabled and self.constraints.c4_max_global < 2:
            hints.append("⚠️ C4 (max global repeats) = 1 combined with C5 and C6 may be impossible. Try allowing 2 repeats.")

        hints.append("💡 Try increasing the number of runs")
        hints.append("💡 Try increasing stages per run")

        return hints

    def optimize(self, time_limit: int = 30) -> OptimizationResult:
        """
        Run the optimization.

        Args:
            time_limit: Solver time limit in seconds

        Returns:
            OptimizationResult with status and assignments
        """
        self._build_problem()

        # Solve with time limit
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit)
        self.problem.solve(solver)

        status = pulp.LpStatus[self.problem.status]
        feasible = status in ["Optimal", "Feasible"]

        if feasible:
            assignments = self._extract_assignments()
            runs_used = len(assignments)
            total_stages = sum(len(stages) for stages in assignments.values())
            obj_value = pulp.value(self.problem.objective)
            hints = []
        else:
            assignments = {}
            runs_used = 0
            total_stages = 0
            obj_value = 0.0
            hints = self._generate_infeasibility_hints()

        return OptimizationResult(
            status=status,
            feasible=feasible,
            runs_used=runs_used,
            total_stages=total_stages,
            objective_value=obj_value,
            assignments=assignments,
            infeasibility_hints=hints
        )
