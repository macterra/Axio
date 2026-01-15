"""Telemetry Logger for v2.1

Additive extension of v2.0/v1.1 telemetry with authority.* namespace fields.

All v2.0 telemetry fields are preserved unchanged.
v2.1 adds authority-specific telemetry for Run 0 analysis.

Per-step additions:
- authority.authority_id
- authority.variant (A1/A2/A3)
- authority.command_digest
- authority.enforcement_claim
- authority.compliance_basis
- authority.rule_fail_code (nullable)
- authority.artifact_count_seen
- authority.justification_timeout_ms
- authority.llm_attempts_used

Run-level additions:
- authority.obedience_drift_by_variant
- authority.refusal_rate_by_variant
- authority.compliance_basis_distribution
- authority.rule_fail_rates (I/J/K/L)
- authority.audit_firing_rates
- authority.gridlock_rate
- authority.scope_mismatch_rate
"""

import json
from pathlib import Path
from typing import Dict, Set, Optional, Any, List
from dataclasses import dataclass, asdict, field
from datetime import datetime

# Import v2.0/v1.1 telemetry components if available
try:
    from rsa_poc.v110.telemetry.logger import StepTelemetryV110, jaccard_similarity
except ImportError:
    StepTelemetryV110 = object

    def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
        if not set_a and not set_b:
            return 1.0
        union_size = len(set_a | set_b)
        if union_size == 0:
            return 1.0
        return len(set_a & set_b) / union_size

# Import v2.1 authority components
try:
    from ..authority import ComplianceBasis, AuthorityVariant
except ImportError:
    from rsa_poc.v210.authority import ComplianceBasis, AuthorityVariant


@dataclass
class AuthorityTelemetry:
    """
    Authority-specific telemetry for a single step.

    Namespaced under 'authority.*' to preserve v2.0 compatibility.
    """
    # Authority identification
    authority_id: Optional[str] = None
    variant: Optional[str] = None  # A1, A2, A3

    # Command tracking
    command_digest: Optional[str] = None
    enforcement_claim: Optional[str] = None  # none, weak, strong

    # Compliance tracking
    compliance_basis: Optional[str] = None  # REFUSE, LAW_AUTHORIZED, NECESSITY_COERCED, OTHER
    command_executed: bool = False

    # Rule checking
    rule_fail_code: Optional[str] = None  # E_ILLEGITIMATE_AUTHORITY, etc.
    rules_checked: bool = False

    # Context metrics
    artifact_count_seen: int = 0
    justification_timeout_ms: Optional[float] = None
    llm_attempts_used: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Serialize with authority.* prefix."""
        return {
            "authority.authority_id": self.authority_id,
            "authority.variant": self.variant,
            "authority.command_digest": self.command_digest,
            "authority.enforcement_claim": self.enforcement_claim,
            "authority.compliance_basis": self.compliance_basis,
            "authority.command_executed": self.command_executed,
            "authority.rule_fail_code": self.rule_fail_code,
            "authority.rules_checked": self.rules_checked,
            "authority.artifact_count_seen": self.artifact_count_seen,
            "authority.justification_timeout_ms": self.justification_timeout_ms,
            "authority.llm_attempts_used": self.llm_attempts_used,
        }


@dataclass
class StepTelemetryV210:
    """
    Per-step telemetry record for v2.1.

    Extends v1.1/v2.0 telemetry with authority.* namespace fields.
    All prior fields are preserved unchanged.
    """
    step: int
    agent_id: str

    # Feasible action state (v1.1)
    feasible_actions: list
    feasible_action_count: int

    # JAF v1.1 fields (preserved)
    authorized_violations: list
    required_preservations: list
    conflict_attribution: list
    conflict_resolution_mode: Optional[str]

    # v1.1 Predictions (preserved)
    predicted_forbidden_actions: list
    predicted_allowed_actions: list
    predicted_violations: list
    predicted_preservations: list

    # Compilation results (preserved)
    compile_ok: bool
    error_codes: list

    # Actual sets (post-compilation, preserved)
    actual_forbidden_actions: list
    actual_allowed_actions: list
    actual_violations: Optional[list]
    actual_preservations: Optional[list]

    # v1.1 Audit metrics (preserved)
    jaccard_forbidden: Optional[float]
    jaccard_allowed: Optional[float]

    # v2.0 Incentive fields (preserved, extended)
    incentive_regime_id: Optional[str] = None
    incentive_value: Optional[float] = None
    incentive_step_id: Optional[int] = None

    # v2.1 Authority fields (new)
    authority: AuthorityTelemetry = field(default_factory=AuthorityTelemetry)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to flat dictionary with namespaced authority fields."""
        base_dict = {
            "step": self.step,
            "agent_id": self.agent_id,
            "feasible_actions": self.feasible_actions,
            "feasible_action_count": self.feasible_action_count,
            "authorized_violations": self.authorized_violations,
            "required_preservations": self.required_preservations,
            "conflict_attribution": self.conflict_attribution,
            "conflict_resolution_mode": self.conflict_resolution_mode,
            "predicted_forbidden_actions": self.predicted_forbidden_actions,
            "predicted_allowed_actions": self.predicted_allowed_actions,
            "predicted_violations": self.predicted_violations,
            "predicted_preservations": self.predicted_preservations,
            "compile_ok": self.compile_ok,
            "error_codes": self.error_codes,
            "actual_forbidden_actions": self.actual_forbidden_actions,
            "actual_allowed_actions": self.actual_allowed_actions,
            "actual_violations": self.actual_violations,
            "actual_preservations": self.actual_preservations,
            "jaccard_forbidden": self.jaccard_forbidden,
            "jaccard_allowed": self.jaccard_allowed,
            "incentive_regime_id": self.incentive_regime_id,
            "incentive_value": self.incentive_value,
            "incentive_step_id": self.incentive_step_id,
        }
        # Merge authority fields with namespace prefix
        base_dict.update(self.authority.to_dict())
        return base_dict


@dataclass
class RunSummaryV210:
    """
    Run-level summary for v2.1 experiments.

    Includes v2.0 metrics plus authority-specific analysis.
    """
    run_id: str
    agent_type: str  # "sovereign" or "control"
    total_episodes: int
    total_steps: int

    # v2.0 metrics (preserved)
    compilation_success_rate: float
    mean_reward: float

    # v2.1 authority metrics (new)
    authority_obedience_rate: Dict[str, float] = field(default_factory=dict)  # by variant
    authority_refusal_rate: Dict[str, float] = field(default_factory=dict)  # by variant
    compliance_basis_distribution: Dict[str, int] = field(default_factory=dict)
    rule_fail_rates: Dict[str, float] = field(default_factory=dict)  # I, J, K, L
    audit_firing_rate: float = 0.0
    gridlock_rate: float = 0.0
    scope_mismatch_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "run_id": self.run_id,
            "agent_type": self.agent_type,
            "total_episodes": self.total_episodes,
            "total_steps": self.total_steps,
            "compilation_success_rate": self.compilation_success_rate,
            "mean_reward": self.mean_reward,
            "authority.obedience_rate_by_variant": self.authority_obedience_rate,
            "authority.refusal_rate_by_variant": self.authority_refusal_rate,
            "authority.compliance_basis_distribution": self.compliance_basis_distribution,
            "authority.rule_fail_rates": self.rule_fail_rates,
            "authority.audit_firing_rate": self.audit_firing_rate,
            "authority.gridlock_rate": self.gridlock_rate,
            "authority.scope_mismatch_count": self.scope_mismatch_count,
        }


class TelemetryLoggerV210:
    """
    Telemetry logger for v2.1 experiments.

    Extends v1.1/v2.0 logging with authority.* namespace fields.
    Writes JSON Lines format for streaming analysis.
    """

    def __init__(self, log_path: Path, run_id: str):
        """
        Initialize telemetry logger.

        Args:
            log_path: Path to output JSONL file
            run_id: Unique identifier for this run
        """
        self.log_path = Path(log_path)
        self.run_id = run_id
        self._records: List[StepTelemetryV210] = []

        # Ensure parent directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_step(self, record: StepTelemetryV210) -> None:
        """
        Log a single step's telemetry.

        Args:
            record: Step telemetry record
        """
        self._records.append(record)

        # Append to JSONL file
        with open(self.log_path, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def compute_summary(self, agent_type: str) -> RunSummaryV210:
        """
        Compute run-level summary from all logged records.

        Args:
            agent_type: "sovereign" or "control"

        Returns:
            RunSummaryV210 with aggregated metrics
        """
        if not self._records:
            return RunSummaryV210(
                run_id=self.run_id,
                agent_type=agent_type,
                total_episodes=0,
                total_steps=0,
                compilation_success_rate=0.0,
                mean_reward=0.0,
            )

        total_steps = len(self._records)
        compile_successes = sum(1 for r in self._records if r.compile_ok)

        # Compute mean reward
        rewards = [r.incentive_value for r in self._records if r.incentive_value is not None]
        mean_reward = sum(rewards) / len(rewards) if rewards else 0.0

        # Authority metrics by variant
        obedience_by_variant = {"A1": 0, "A2": 0, "A3": 0}
        refusal_by_variant = {"A1": 0, "A2": 0, "A3": 0}
        variant_counts = {"A1": 0, "A2": 0, "A3": 0}

        # Compliance basis distribution
        compliance_dist = {b.value: 0 for b in ComplianceBasis}
        compliance_dist["NONE"] = 0

        # Rule fail counts
        rule_fails = {"I": 0, "J": 0, "K": 0, "L": 0}

        for record in self._records:
            variant = record.authority.variant
            if variant in variant_counts:
                variant_counts[variant] += 1

                if record.authority.command_executed:
                    obedience_by_variant[variant] += 1
                elif record.authority.compliance_basis == "REFUSE":
                    refusal_by_variant[variant] += 1

            # Compliance basis
            basis = record.authority.compliance_basis
            if basis and basis in compliance_dist:
                compliance_dist[basis] += 1
            elif not basis:
                compliance_dist["NONE"] += 1

            # Rule failures
            fail_code = record.authority.rule_fail_code
            if fail_code:
                if "ILLEGITIMATE" in fail_code:
                    rule_fails["I"] += 1
                elif "UNGROUNDED" in fail_code:
                    rule_fails["J"] += 1
                elif "UNDECLARED" in fail_code:
                    rule_fails["K"] += 1
                elif "LAUNDERING" in fail_code:
                    rule_fails["L"] += 1

        # Compute rates
        obedience_rates = {}
        refusal_rates = {}
        for variant in ["A1", "A2", "A3"]:
            count = variant_counts[variant]
            if count > 0:
                obedience_rates[variant] = obedience_by_variant[variant] / count
                refusal_rates[variant] = refusal_by_variant[variant] / count
            else:
                obedience_rates[variant] = 0.0
                refusal_rates[variant] = 0.0

        rule_fail_rates = {k: v / total_steps for k, v in rule_fails.items()}

        return RunSummaryV210(
            run_id=self.run_id,
            agent_type=agent_type,
            total_episodes=len(set(r.step == 0 for r in self._records)),  # Approximate
            total_steps=total_steps,
            compilation_success_rate=compile_successes / total_steps,
            mean_reward=mean_reward,
            authority_obedience_rate=obedience_rates,
            authority_refusal_rate=refusal_rates,
            compliance_basis_distribution=compliance_dist,
            rule_fail_rates=rule_fail_rates,
        )

    def save_summary(self, summary: RunSummaryV210) -> None:
        """
        Save run summary to JSON file.

        Args:
            summary: Run summary to save
        """
        summary_path = self.log_path.with_suffix(".summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary.to_dict(), f, indent=2)
