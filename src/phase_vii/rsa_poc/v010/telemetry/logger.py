"""Telemetry and Logging for RSA-PoC v0.1

JSON Lines logging per spec.
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class TelemetryLogger:
    """
    JSON Lines logger for RSA-PoC v0.1.

    Logs step-level and run-level telemetry.
    """

    def __init__(self, log_path: str):
        """
        Initialize logger.

        Args:
            log_path: Path to .jsonl log file
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Clear existing log
        with open(self.log_path, 'w') as f:
            pass

    def log_step(self, step_data: Dict[str, Any]):
        """
        Log step-level telemetry.

        Required fields per spec:
        - step
        - feasible_actions_pre_mask
        - jaf_schema_valid
        - compile_ok
        - compile_error_code (if not compile_ok)
        - forbidden_actions
        - nontrivial_forbidden (count)
        - decorative_constraint
        - feasible_actions_post_mask (count)
        - gridlock
        - selected_action (if any)
        - selector_scope_violation
        """
        record = {
            "type": "step",
            "timestamp": datetime.utcnow().isoformat(),
            **step_data
        }

        with open(self.log_path, 'a') as f:
            f.write(json.dumps(record, sort_keys=True) + '\n')

    def log_run_summary(self, run_data: Dict[str, Any]):
        """
        Log run-level summary.

        Required fields per spec:
        - total_steps
        - compile_failure_rate
        - decorative_constraint_rate
        - non_trivial_constraint_rate
        - gridlock_rate
        - first_gridlock_step (if any)
        """
        record = {
            "type": "run_summary",
            "timestamp": datetime.utcnow().isoformat(),
            **run_data
        }

        with open(self.log_path, 'a') as f:
            f.write(json.dumps(record, sort_keys=True) + '\n')

    def log_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log arbitrary event"""
        record = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **event_data
        }

        with open(self.log_path, 'a') as f:
            f.write(json.dumps(record, sort_keys=True) + '\n')


class RunMetrics:
    """
    Accumulate metrics across a run.
    """

    def __init__(self):
        self.total_steps = 0
        self.compile_failures = 0
        self.decorative_constraints = 0
        self.non_trivial_constraints = 0
        self.gridlock_steps = 0
        self.first_gridlock_step: Optional[int] = None
        self.halt_steps = 0
        self.first_halt_step: Optional[int] = None

        self.total_violations = 0  # Actions taken that violate preferences
        self.total_reward = 0.0

    def update_step(
        self,
        compile_ok: bool,
        is_decorative: bool,
        is_nontrivial: bool,
        is_gridlock: bool,
        is_halt: bool,
        reward: float = 0.0,
        is_violation: bool = False
    ):
        """Update metrics for a step"""
        self.total_steps += 1

        if not compile_ok:
            self.compile_failures += 1

        if is_decorative:
            self.decorative_constraints += 1

        if is_nontrivial:
            self.non_trivial_constraints += 1

        if is_gridlock:
            self.gridlock_steps += 1
            if self.first_gridlock_step is None:
                self.first_gridlock_step = self.total_steps

        if is_halt:
            self.halt_steps += 1
            if self.first_halt_step is None:
                self.first_halt_step = self.total_steps

        self.total_reward += reward

        if is_violation:
            self.total_violations += 1

    def compute_rates(self) -> Dict[str, float]:
        """Compute rates for run summary"""
        if self.total_steps == 0:
            return {
                "compile_failure_rate": 0.0,
                "decorative_constraint_rate": 0.0,
                "non_trivial_constraint_rate": 0.0,
                "gridlock_rate": 0.0,
                "halt_rate": 0.0,
                "violation_rate": 0.0,
            }

        return {
            "compile_failure_rate": self.compile_failures / self.total_steps,
            "decorative_constraint_rate": self.decorative_constraints / self.total_steps,
            "non_trivial_constraint_rate": self.non_trivial_constraints / self.total_steps,
            "gridlock_rate": self.gridlock_steps / self.total_steps,
            "halt_rate": self.halt_steps / self.total_steps,
            "violation_rate": self.total_violations / self.total_steps,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Export full metrics"""
        return {
            "total_steps": self.total_steps,
            "compile_failures": self.compile_failures,
            "decorative_constraints": self.decorative_constraints,
            "non_trivial_constraints": self.non_trivial_constraints,
            "gridlock_steps": self.gridlock_steps,
            "first_gridlock_step": self.first_gridlock_step,
            "halt_steps": self.halt_steps,
            "first_halt_step": self.first_halt_step,
            "total_violations": self.total_violations,
            "total_reward": self.total_reward,
            **self.compute_rates()
        }
