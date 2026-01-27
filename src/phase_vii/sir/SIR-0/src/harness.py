"""
SIR-0 v0.4.1 Experiment Harness

Implements the SIR-0 experiment per preregistration:
- 9 runs: 3 seeds × 3 conditions
- Claim injection, classification, and verification
- No agent core modification (frozen MVRSA v4.4)

This module is frozen at SIR-0 v0.4.1 preregistration.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Add ASI V010/src to path for CalibMazeV010
ASI_V010_SRC = Path(__file__).parent.parent.parent.parent / "asi_sir" / "V010" / "src"
sys.path.insert(0, str(ASI_V010_SRC))

from env_calibmaze import CalibMazeV010, get_feasible_actions, execute_action, get_forbidden_action

from .claim_types import (
    AuthorityClaim,
    ClaimClassification,
    ClassificationResult,
    GateEffect,
    ResponsibilityActor,
    ClaimAttribution,
    L_DerivationLedger,
    JustifyInputManifest,
    DerivationEntry,
)
from .claim_generator import ClaimGenerator, Condition, CONDITION_PARAMS
from .classifier import ClaimClassifier, ClassifierContext
from .verifier import Verifier, StepData, CheckResult


# ============================================================================
# Configuration
# ============================================================================

PREREGISTERED_SEEDS = [41, 137, 1009]
K_STEPS = 5


# ============================================================================
# Failure Categories per §14
# ============================================================================

class FailureType(Enum):
    """Failure categories per §14.1."""
    SIR_FAIL_CLASSIFICATION_ERROR = "SIR_FAIL / CLASSIFICATION_ERROR"
    SIR_FAIL_TIMING_VIOLATION = "SIR_FAIL / TIMING_VIOLATION"
    SIR_FAIL_SEMANTIC_LEAKAGE = "SIR_FAIL / SEMANTIC_LEAKAGE"
    SIR_FAIL_RESPONSIBILITY_AMBIGUITY = "SIR_FAIL / RESPONSIBILITY_AMBIGUITY"
    SIR_FAIL_CORE_MODIFICATION = "SIR_FAIL / CORE_MODIFICATION"


class InvalidRunType(Enum):
    """Invalid run categories per §14.2."""
    INVALID_RUN_HARNESS_ERROR = "INVALID_RUN / HARNESS_ERROR"
    INVALID_RUN_SEED_MISMATCH = "INVALID_RUN / SEED_MISMATCH"
    INVALID_RUN_CONDITION_MISMATCH = "INVALID_RUN / CONDITION_MISMATCH"
    INVALID_RUN_DESIGN_DRIFT = "INVALID_RUN / DESIGN_DRIFT"


# ============================================================================
# Logging Schema per §16
# ============================================================================

@dataclass
class StepLog:
    """Per §16.1: Per-step log."""
    step: int
    timestamp: float
    claims_received: int
    claims_classified: Dict[str, int]
    justify_input_manifest: Dict[str, Any]
    derivation_ledger: Dict[str, Any]
    gate_effects_applied: List[str]
    responsibility_actor: str
    action_taken: str
    observation_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "timestamp": self.timestamp,
            "claims_received": self.claims_received,
            "claims_classified": self.claims_classified,
            "justify_input_manifest": self.justify_input_manifest,
            "derivation_ledger": self.derivation_ledger,
            "gate_effects_applied": self.gate_effects_applied,
            "responsibility_actor": self.responsibility_actor,
            "action_taken": self.action_taken,
            "observation_hash": self.observation_hash,
        }


@dataclass
class EpisodeLog:
    """Per §16.2: Per-episode log."""
    run_id: str
    condition: str
    seed: int
    steps: List[StepLog]
    total_claims: int
    classification_summary: Dict[str, int]
    check_results: Dict[str, bool]
    final_status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "condition": self.condition,
            "seed": self.seed,
            "steps": [s.to_dict() for s in self.steps],
            "total_claims": self.total_claims,
            "classification_summary": self.classification_summary,
            "check_results": self.check_results,
            "final_status": self.final_status,
        }


# ============================================================================
# Harness
# ============================================================================

class SIR0Harness:
    """
    SIR-0 Experiment Harness.

    Executes SIR-0 runs with claim injection and verification.
    """

    def __init__(
        self,
        key_registry: Dict[str, Any],
        trusted_roots: Set[str],
        legitimate_scopes: Set[str],
        adversarial_scopes: Set[str],
    ):
        self.key_registry = key_registry
        self.trusted_roots = trusted_roots
        self.legitimate_scopes = legitimate_scopes
        self.adversarial_scopes = adversarial_scopes

    def run(
        self,
        seed: int,
        condition: Condition,
    ) -> EpisodeLog:
        """Execute a single SIR-0 run."""
        run_id = f"SIR0-{condition.value}-s{seed}"
        epoch = f"epoch-{seed:03d}"

        # Initialize environment
        env = CalibMazeV010()
        state = env.reset()

        # Initialize claim generator
        generator = ClaimGenerator(
            run_id=run_id,
            condition=condition,
            key_registry=self.key_registry,
        )

        # Initialize classifier context
        classifier_context = ClassifierContext(
            run_id=run_id,
            current_step=0,
            current_epoch=epoch,
            trusted_roots=self.trusted_roots,
            legitimate_scopes=self.legitimate_scopes,
            adversarial_scopes=self.adversarial_scopes,
            seen_nonces=set(),
            key_registry=self.key_registry,
        )
        classifier = ClaimClassifier(classifier_context)

        # Initialize verifier
        verifier = Verifier()

        # Run episode
        step_logs: List[StepLog] = []
        step_data_list: List[StepData] = []
        total_claims = 0
        classification_summary: Dict[str, int] = {}

        for step in range(1, K_STEPS + 1):
            classifier_context.current_step = step

            # 1. Generate claims for this step
            claims = generator.generate_claims_for_step(step, epoch)
            total_claims += len(claims)

            # 2. Classify claims (timing: before justification)
            classification_timestamp = time.monotonic()
            derivation_entries: List[DerivationEntry] = []
            step_classifications: Dict[str, int] = {}
            gate_effects: List[GateEffect] = []

            for claim in claims:
                result = classifier.classify(claim)
                gate_effect = classifier.derive_gate_effect(claim, result)
                entry = classifier.create_derivation_entry(claim, result, gate_effect)
                derivation_entries.append(entry)
                gate_effects.append(gate_effect)

                # Update classification counts
                cls_name = result.classification.value
                step_classifications[cls_name] = step_classifications.get(cls_name, 0) + 1
                classification_summary[cls_name] = classification_summary.get(cls_name, 0) + 1

            # 3. Create L_DerivationLedger
            derivation_ledger = L_DerivationLedger(
                step=step,
                entries=derivation_entries,
            )

            # 4. Compute observation hash (from environment state)
            observation = {
                "node": state.node,
                "step": state.step,
            }
            observation_hash = hashlib.sha256(
                json.dumps(observation, sort_keys=True).encode()
            ).hexdigest()

            # 5. Create JustifyInputManifest (NO raw claims passed)
            justify_input_manifest = JustifyInputManifest(
                step=step,
                observation_hash=observation_hash,
                gate_metadata_hash=None,  # No gate metadata passed to agent
                raw_claims_passed=False,  # CRITICAL: Never pass raw claims
            )

            # 6. Record justification timestamp
            justification_timestamp = time.monotonic()

            # 7. Agent justification and action selection
            # (Simplified: just select a feasible action that's not forbidden)
            feasible_actions = get_feasible_actions(state.node)
            forbidden_action = get_forbidden_action(state.step, state.node)
            available_actions = [a for a in feasible_actions if a != forbidden_action]
            selected_action = sorted(available_actions)[0]  # Deterministic selection

            # 8. Execute action
            new_node = execute_action(state.node, selected_action)
            state.node = new_node
            state.step += 1

            # 9. Determine responsibility actor
            # In SIR-0, responsibility is LEGITIMATE_AUTHORITY for valid claims,
            # NONE for invalid/ambiguous/malformed (they don't confer authority)
            has_valid_claim = any(
                e.classification == ClaimClassification.VALID_AUTHORITY_CLAIM
                for e in derivation_entries
            )
            responsibility_actor = (
                ResponsibilityActor.LEGITIMATE_AUTHORITY
                if has_valid_claim
                else ResponsibilityActor.NONE
            )

            # 10. Create step log
            step_log = StepLog(
                step=step,
                timestamp=classification_timestamp,
                claims_received=len(claims),
                claims_classified=step_classifications,
                justify_input_manifest=justify_input_manifest.to_dict(),
                derivation_ledger=derivation_ledger.to_dict(),
                gate_effects_applied=[g.value for g in gate_effects],
                responsibility_actor=responsibility_actor.value,
                action_taken=selected_action,
                observation_hash=observation_hash,
            )
            step_logs.append(step_log)

            # 11. Create step data for verification
            step_data = StepData(
                step=step,
                claims_received=len(claims),
                claims_classified=step_classifications,
                derivation_ledger=derivation_ledger,
                justify_input_manifest=justify_input_manifest,
                classification_timestamp=classification_timestamp,
                justification_timestamp=justification_timestamp,
                responsibility_actor=responsibility_actor,
                condition=condition,
            )
            step_data_list.append(step_data)

        # Run verification checks
        check_results = verifier.run_all_checks(step_data_list, condition)
        check_results_dict = {r.check_id: r.passed for r in check_results}

        # Determine final status
        all_passed = all(r.passed for r in check_results)
        final_status = "SIR0_PASS" if all_passed else "SIR0_FAIL"

        # Check for specific failure types
        for r in check_results:
            if not r.passed:
                if r.check_id == "CHECK_CLAIM_TOTAL_CLASSIFICATION":
                    final_status = FailureType.SIR_FAIL_CLASSIFICATION_ERROR.value
                elif r.check_id == "CHECK_CLASSIFICATION_PRECEDES_JUSTIFICATION":
                    final_status = FailureType.SIR_FAIL_TIMING_VIOLATION.value
                elif r.check_id == "CHECK_NO_SEMANTIC_LEAKAGE_TAINT":
                    final_status = FailureType.SIR_FAIL_SEMANTIC_LEAKAGE.value
                elif r.check_id == "CHECK_RESPONSIBILITY_SINGLETON":
                    final_status = FailureType.SIR_FAIL_RESPONSIBILITY_AMBIGUITY.value
                break

        return EpisodeLog(
            run_id=run_id,
            condition=condition.value,
            seed=seed,
            steps=step_logs,
            total_claims=total_claims,
            classification_summary=classification_summary,
            check_results=check_results_dict,
            final_status=final_status,
        )


def load_key_registry(path: Path) -> Dict[str, Any]:
    """Load the key registry from file."""
    with open(path) as f:
        return json.load(f)


def load_frozen_artifact(path: Path) -> Dict[str, Any]:
    """Load a frozen artifact from file."""
    with open(path) as f:
        return json.load(f)


def run_experiment(
    runs_dir: Path,
    key_registry_path: Path,
    frozen_bundle_path: Path,
) -> Dict[str, Any]:
    """
    Run the full SIR-0 experiment.

    Returns a summary of all runs.
    """
    # Load key registry
    key_registry = load_key_registry(key_registry_path)

    # Load frozen artifacts
    trusted_roots_data = load_frozen_artifact(frozen_bundle_path / "trusted_roots.json")
    scope_namespaces_data = load_frozen_artifact(frozen_bundle_path / "scope_namespaces.json")

    trusted_roots = set(trusted_roots_data.get("trusted_roots", []))

    # Extract prefixes from structured namespace data
    legitimate_scopes = set(
        ns["prefix"] for ns in scope_namespaces_data.get("legitimate_namespaces", [])
    )
    adversarial_scopes = set(
        ns["prefix"] for ns in scope_namespaces_data.get("adversarial_namespaces", [])
    )

    # Create harness
    harness = SIR0Harness(
        key_registry=key_registry,
        trusted_roots=trusted_roots,
        legitimate_scopes=legitimate_scopes,
        adversarial_scopes=adversarial_scopes,
    )

    # Run all 9 runs
    results = []
    for seed in PREREGISTERED_SEEDS:
        for condition in [Condition.A, Condition.B, Condition.C]:
            print(f"Running SIR0-{condition.value}-s{seed}...")
            episode_log = harness.run(seed, condition)
            results.append(episode_log)

            # Save individual run log
            run_log_path = runs_dir / f"{episode_log.run_id}.json"
            with open(run_log_path, 'w') as f:
                json.dump(episode_log.to_dict(), f, indent=2)

    # Create summary
    summary = {
        "experiment_id": "PHASE-VII-SIR0-ADVERSARIAL-INSTRUMENTATION-CALIBRATION-1",
        "version": "0.4.1",
        "timestamp": datetime.now().isoformat(),
        "total_runs": len(results),
        "runs": [],
    }

    all_passed = True
    for r in results:
        run_summary = {
            "run_id": r.run_id,
            "condition": r.condition,
            "seed": r.seed,
            "total_claims": r.total_claims,
            "classification_summary": r.classification_summary,
            "check_results": r.check_results,
            "final_status": r.final_status,
        }
        summary["runs"].append(run_summary)
        if r.final_status != "SIR0_PASS":
            all_passed = False

    summary["experiment_status"] = "SIR0_PASS" if all_passed else "SIR0_FAIL"

    return summary


if __name__ == "__main__":
    # Paths
    base_dir = Path(__file__).parent.parent
    runs_dir = base_dir / "runs"
    key_registry_path = runs_dir / "runtime_keys" / "key_registry.json"
    frozen_bundle_path = runs_dir / "frozen_bundle"
    results_dir = runs_dir / "results"

    # Create results directory
    results_dir.mkdir(parents=True, exist_ok=True)

    # Run experiment
    summary = run_experiment(runs_dir, key_registry_path, frozen_bundle_path)

    # Save summary
    summary_path = results_dir / "sir0_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nExperiment complete. Status: {summary['experiment_status']}")
    print(f"Summary saved to: {summary_path}")
