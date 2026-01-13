"""Telemetry Logger for v1.0

JSON Lines telemetry with v1.0 fields (collisions, authorized violations, etc.)
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

# Import agent types
try:
    from ..agent import StepResult, MVRAAgentV100
    from ..jaf.schema import JAF100
    from ..jcomp.compiler import CompilationResult
except ImportError:
    from rsa_poc.v100.agent import StepResult, MVRAAgentV100
    from rsa_poc.v100.jaf.schema import JAF100
    from rsa_poc.v100.jcomp.compiler import CompilationResult


@dataclass
class RunMetricsV100:
    """Episode-level metrics for v1.0"""
    condition: str
    seed: int
    total_steps: int
    total_reward: float
    violation_count: int
    violation_rate: float
    collision_steps: int
    authorized_violation_count: int
    halted: bool
    halt_reason: Optional[str]
    halt_step: Optional[int]


class TelemetryLoggerV100:
    """
    JSON Lines logger for v1.0 episodes.

    Logs:
    - Per-step trace (JAF, compilation, action, APCM)
    - Episode metrics
    - Collision and authorization patterns
    """

    def __init__(self, log_dir: Path):
        """
        Initialize logger.

        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_episode(
        self,
        condition: str,
        seed: int,
        step_history: List[StepResult],
        agent: MVRAAgentV100
    ):
        """
        Log full episode to JSON Lines file.

        Args:
            condition: Condition name (e.g., "MVRA_v100", "ASB_v100")
            seed: Random seed for episode
            step_history: List of StepResult from episode
            agent: Agent instance (for metrics)
        """
        # Create log file
        log_file = self.log_dir / f"{condition}_seed{seed}.jsonl"

        with open(log_file, "w") as f:
            # Write episode header
            metrics = agent.get_metrics()
            header = {
                "type": "episode_start",
                "condition": condition,
                "seed": seed,
                "agent_id": agent.agent_id,
                "max_steps": agent.env.max_steps
            }
            f.write(json.dumps(header) + "\n")

            # Write per-step trace
            for result in step_history:
                step_record = self._format_step_result(result)
                f.write(json.dumps(step_record) + "\n")

            # Write episode summary
            summary = {
                "type": "episode_end",
                "condition": condition,
                "seed": seed,
                "metrics": metrics
            }
            f.write(json.dumps(summary) + "\n")

    def _format_step_result(self, result: StepResult) -> Dict:
        """Format StepResult for JSON serialization"""
        record = {
            "type": "step",
            "step": result.step,
            "selected_action": result.selected_action,
            "reward": result.reward,
            "done": result.done,
            "halted": result.halted,
            "halt_reason": result.halt_reason,
            "info": result.info
        }

        # Add JAF fields
        if result.jaf:
            record["jaf"] = {
                "artifact_id": result.jaf.identity.artifact_id,
                "action_id": result.jaf.action_claim.action_id,
                "justification": result.jaf.action_claim.justification,
                "authorized_violations": list(result.jaf.authorized_violations),
                "required_preservations": list(result.jaf.required_preservations),
                "conflict_attribution": [list(pair) for pair in result.jaf.conflict_attribution],
                "precedent_reference": result.jaf.precedent_reference,
                "conflict_resolution": {
                    "mode": result.jaf.conflict_resolution.mode,
                    "previous_digest": result.jaf.conflict_resolution.previous_artifact_digest
                } if result.jaf.conflict_resolution else None
            }

        # Add compilation fields
        if result.compilation_result:
            record["compilation"] = {
                "success": result.compilation_result.success,
                "action_mask": list(result.compilation_result.action_mask),
                "errors": [
                    {
                        "code": e.code,
                        "message": e.message,
                        "details": e.details
                    }
                    for e in result.compilation_result.errors
                ],
                "digest": result.compilation_result.digest
            }

        return record

    def aggregate_metrics(self, condition: str, seeds: List[int]) -> Dict:
        """
        Aggregate metrics across multiple seeds.

        Args:
            condition: Condition name
            seeds: List of seeds to aggregate

        Returns:
            Aggregated statistics
        """
        metrics_list = []

        for seed in seeds:
            log_file = self.log_dir / f"{condition}_seed{seed}.jsonl"
            if not log_file.exists():
                continue

            with open(log_file, "r") as f:
                for line in f:
                    record = json.loads(line)
                    if record["type"] == "episode_end":
                        metrics_list.append(record["metrics"])

        if not metrics_list:
            return {}

        # Compute aggregates
        n = len(metrics_list)
        return {
            "condition": condition,
            "n_episodes": n,
            "mean_total_steps": sum(m["total_steps"] for m in metrics_list) / n,
            "mean_total_reward": sum(m["total_reward"] for m in metrics_list) / n,
            "mean_violation_count": sum(m["violation_count"] for m in metrics_list) / n,
            "mean_violation_rate": sum(m["violation_rate"] for m in metrics_list) / n,
            "mean_collision_steps": sum(m["collision_steps"] for m in metrics_list) / n,
            "mean_authorized_violations": sum(m["authorized_violations"] for m in metrics_list) / n,
            "halt_rate": sum(1 for m in metrics_list if m["halted"]) / n,
            "halt_reasons": [m["halt_reason"] for m in metrics_list if m["halted"]]
        }


def create_run_metrics(
    condition: str,
    seed: int,
    step_history: List[StepResult],
    agent: MVRAAgentV100
) -> RunMetricsV100:
    """Create RunMetricsV100 from episode data"""
    metrics = agent.get_metrics()

    halt_step = None
    for i, result in enumerate(step_history):
        if result.halted:
            halt_step = i + 1
            break

    return RunMetricsV100(
        condition=condition,
        seed=seed,
        total_steps=metrics["total_steps"],
        total_reward=metrics["total_reward"],
        violation_count=metrics["violation_count"],
        violation_rate=metrics["violation_rate"],
        collision_steps=metrics["collision_steps"],
        authorized_violation_count=metrics["authorized_violations"],
        halted=metrics["halted"],
        halt_reason=metrics["halt_reason"],
        halt_step=halt_step
    )
