"""Data models for the iDoE planner."""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class StageAssignment:
    """Represents a DOE combination assignment to a stage."""

    stage: int
    combination: int
    mu_set: float
    temperature: float

    def __str__(self) -> str:
        """Format the stage assignment as a readable string."""
        return f"Stage {self.stage}: Combo {self.combination} (μ_set={self.mu_set}, Temp={self.temperature}°C)"


@dataclass
class Experiment:
    """Represents an intensified experiment with multiple stages."""

    experiment_id: int
    stages: List[StageAssignment]

    def __str__(self) -> str:
        """Format the experiment as a readable string."""
        stage_descriptions = ", ".join(str(stage) for stage in self.stages)
        return f"Experiment {self.experiment_id}: {stage_descriptions}"

    def is_empty(self) -> bool:
        """Check if the experiment has any stages assigned."""
        return len(self.stages) == 0


@dataclass
class OptimizationResult:
    """Results from the MILP optimization."""

    status: str
    experiments: List[Experiment]
    objective_value: float
    num_experiments_used: int
    num_stages_used: int

    def to_dict(self) -> dict:
        """Convert result to dictionary format."""
        return {
            "status": self.status,
            "objective_value": self.objective_value,
            "num_experiments_used": self.num_experiments_used,
            "num_stages_used": self.num_stages_used,
            "experiments": [
                {
                    "experiment_id": exp.experiment_id,
                    "stages": [
                        {
                            "stage": stage.stage,
                            "combination": stage.combination,
                            "mu_set": stage.mu_set,
                            "temperature": stage.temperature
                        }
                        for stage in exp.stages
                    ]
                }
                for exp in self.experiments
            ]
        }

    def __str__(self) -> str:
        """Format the optimization result as a readable string."""
        lines = [
            f"Optimization Status: {self.status}",
            f"Objective Value: {self.objective_value:.6f}",
            f"Number of Experiments Used: {self.num_experiments_used}",
            f"Total Stages Used: {self.num_stages_used}",
            "",
            "Experiment Assignments:"
        ]
        for exp in self.experiments:
            if not exp.is_empty():
                lines.append(str(exp))
        return "\n".join(lines)
