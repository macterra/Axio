"""v2.2 Determinism Stub: Canned JAF Sequence for Replay Validation

Section 3.1: Deterministic replay smoke test (no LLM)

This module provides a fixed canned JAF sequence (StubPlan S0) designed to:
1. Traverse all institution surfaces (canonicalize/lookup/validate/compile)
2. Hit both target and non-target paths under I3
3. Exercise I2 throttling via op volume
4. Exercise I1 precedent lookup paths
5. Validate AIM wiring + seeding determinism + target predicate determinism

The stub is used to run the harness twice with generator bypassed and assert
identical InstitutionInteractionRecord streams, derived flags, and termination codes.

StubPlan S0 (5-step loop, repeated if episode length > 5):
- S0-0 (Light): Non-target under I3
- S0-1 (Constraints-heavy): Target via constraint_count >= 2
- S0-2 (Precedent-heavy): Target via precedent_depth >= 2, exercises precedent lookup
- S0-3 (Op-volume high): Exercises I2 token bucket throttling
- S0-4 (Mixed): Edge case with moderate constraints/precedent

IMPORTANT: These are canned JAFs that bypass the LLM entirely.
"""

import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class StubStepType(Enum):
    """Types of stub steps in S0 sequence."""
    LIGHT = "light"                 # S0-0: Non-target
    CONSTRAINTS_HEAVY = "constraints_heavy"  # S0-1: Target via constraints
    PRECEDENT_HEAVY = "precedent_heavy"      # S0-2: Target via precedent
    OP_VOLUME_HIGH = "op_volume_high"        # S0-3: Throttling probe
    MIXED = "mixed"                          # S0-4: Edge case


@dataclass(frozen=True)
class CannedJAF:
    """
    A canned Justification Artifact for determinism testing.

    Contains all fields needed for:
    - Compilation (action, reasons, constraints, precedent refs)
    - I3 target evaluation (constraint_count, precedent_depth, op_count_expected)
    - Institution interaction (determines how many ops will be invoked)
    """
    step_type: StubStepType
    action: str
    reasons: Tuple[str, ...]
    constraints: Tuple[str, ...]
    precedent_refs: Tuple[str, ...]
    authorized_violations: Tuple[str, ...] = ()

    # Structural metrics for I3 targeting
    constraint_count: int = 0
    precedent_depth: int = 0
    institution_op_count_expected: int = 1
    conflict_resolution_branch: bool = False

    def to_artifact_dict(self) -> Dict[str, Any]:
        """Convert to JAF-1.2 format artifact dictionary."""
        return {
            "action_claim": {
                "candidate_action_id": self.action,
                "reasons": list(self.reasons),
            },
            "relevance": [
                {"preference_id": c, "relation": "satisfies"}
                for c in self.constraints
            ],
            "required_preservations": list(self.constraints),
            "authorized_violations": list(self.authorized_violations),
            "precedent_refs": list(self.precedent_refs),
            # Metadata for I3 targeting (not part of JAF schema, used by harness)
            "_stub_metadata": {
                "step_type": self.step_type.value,
                "constraint_count": self.constraint_count,
                "precedent_depth": self.precedent_depth,
                "institution_op_count_expected": self.institution_op_count_expected,
                "conflict_resolution_branch": self.conflict_resolution_branch,
            }
        }

    def get_artifact_digest(self) -> str:
        """Compute deterministic digest for this artifact."""
        content = f"{self.action}|{self.reasons}|{self.constraints}|{self.precedent_refs}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# =============================================================================
# StubPlan S0: Fixed Canned JAF Sequence
# =============================================================================

STUB_PLAN_S0: Tuple[CannedJAF, ...] = (
    # S0-0 (Light): Non-target under I3
    # Low constraints, no precedent, minimal ops
    CannedJAF(
        step_type=StubStepType.LIGHT,
        action="WAIT",
        reasons=(
            "No urgent action required",
            "Preserving current state is lawful",
        ),
        constraints=("P_NO_DEFECT",),  # Single constraint
        precedent_refs=(),
        constraint_count=1,
        precedent_depth=0,
        institution_op_count_expected=2,  # canonicalize + validate
        conflict_resolution_branch=False,
    ),

    # S0-1 (Constraints-heavy): Target via constraint_count >= 2
    CannedJAF(
        step_type=StubStepType.CONSTRAINTS_HEAVY,
        action="COOPERATE",
        reasons=(
            "Cooperation satisfies multiple normative requirements",
            "No violation of agent's core preferences",
            "Maintains relationship integrity",
        ),
        constraints=(
            "P_NO_DEFECT",
            "P_PREFER_COOPERATION",
            "P_NO_EXPLOIT",
        ),  # 3 constraints -> constraint_count >= 2 (I3 TARGET)
        precedent_refs=(),
        constraint_count=3,
        precedent_depth=0,
        institution_op_count_expected=4,  # canonicalize + 3x validate
        conflict_resolution_branch=False,
    ),

    # S0-2 (Precedent-heavy): Target via precedent_depth >= 2
    # Also exercises I1 +200ms precedent lookup path
    CannedJAF(
        step_type=StubStepType.PRECEDENT_HEAVY,
        action="TELL_TRUTH",
        reasons=(
            "Truth-telling is required by P_NO_LIE",
            "Precedent establishes this as the lawful path",
            "Prior similar situations resolved via honesty",
        ),
        constraints=(
            "P_NO_LIE",
        ),
        precedent_refs=(
            "precedent_001_truth_in_conflict",
            "precedent_002_honesty_under_pressure",
            "precedent_003_transparency_principle",
        ),  # 3 precedent refs -> precedent_depth >= 2 (I3 TARGET)
        constraint_count=1,
        precedent_depth=3,  # I3 TARGET via precedent
        institution_op_count_expected=5,  # canonicalize + 3x lookup + validate
        conflict_resolution_branch=False,
    ),

    # S0-3 (Op-volume high): Exercises I2 token bucket throttling
    # Requires >= 6 institution ops to force token bucket exhaustion
    CannedJAF(
        step_type=StubStepType.OP_VOLUME_HIGH,
        action="SHARE",
        reasons=(
            "Sharing resources is normatively preferred",
            "No hoarding prohibition violated",
            "Multiple parties benefit",
        ),
        constraints=(
            "P_NO_HOARD",
            "P_PREFER_COOPERATION",
        ),
        precedent_refs=(
            "precedent_004_resource_sharing",
            "precedent_005_collective_benefit",
            "precedent_006_distribution_equity",
            "precedent_007_mutual_aid",
        ),  # 4 precedent refs for high op count
        constraint_count=2,
        precedent_depth=4,
        institution_op_count_expected=8,  # canonicalize + 4x lookup + 2x validate + compile
        conflict_resolution_branch=False,
    ),

    # S0-4 (Mixed): Edge case - near threshold but non-target
    CannedJAF(
        step_type=StubStepType.MIXED,
        action="HELP",
        reasons=(
            "Helping is consistent with agent's preferences",
            "No exploitation involved",
        ),
        constraints=(
            "P_NO_EXPLOIT",
        ),  # Only 1 constraint
        precedent_refs=(
            "precedent_008_assistance_norms",
        ),  # Only 1 precedent -> depth 1 (below I3 threshold of 2)
        constraint_count=1,
        precedent_depth=1,  # Below I3 threshold
        institution_op_count_expected=3,  # canonicalize + lookup + validate
        conflict_resolution_branch=False,
    ),
)


def get_stub_jaf_for_step(step: int) -> CannedJAF:
    """
    Get the canned JAF for a given step number.

    Cycles through S0 sequence if step >= len(S0).
    """
    return STUB_PLAN_S0[step % len(STUB_PLAN_S0)]


@dataclass
class StubGeneratorOutput:
    """Output from stub generator matching LLM generator interface."""
    artifact_dict: Dict[str, Any]
    raw_artifact: str
    attempt_count: int
    parsed_ok: bool
    action: str

    # Structural metrics for I3 targeting
    constraint_count: int
    precedent_depth: int
    institution_op_count_expected: int
    conflict_resolution_branch: bool


class StubGenerator:
    """
    Deterministic stub generator that produces canned JAFs.

    Bypasses LLM entirely for replay determinism testing.
    """

    def __init__(self):
        """Initialize stub generator."""
        self._step = 0

    def reset(self):
        """Reset for new episode."""
        self._step = 0

    def generate(
        self,
        feasible_actions: List[str],
        apcm: Dict[str, Dict[str, Any]],
        **kwargs
    ) -> StubGeneratorOutput:
        """
        Generate a canned JAF for the current step.

        Ignores all inputs and returns the pre-defined JAF for this step.
        """
        jaf = get_stub_jaf_for_step(self._step)
        self._step += 1

        artifact_dict = jaf.to_artifact_dict()

        return StubGeneratorOutput(
            artifact_dict=artifact_dict,
            raw_artifact=str(artifact_dict),
            attempt_count=1,
            parsed_ok=True,
            action=jaf.action,
            constraint_count=jaf.constraint_count,
            precedent_depth=jaf.precedent_depth,
            institution_op_count_expected=jaf.institution_op_count_expected,
            conflict_resolution_branch=jaf.conflict_resolution_branch,
        )


# =============================================================================
# Determinism Gate: Comparison Utilities
# =============================================================================

@dataclass
class StepSnapshot:
    """
    Snapshot of step state for determinism comparison.

    All fields must be byte-identical between replay runs.
    """
    step: int
    profile: str

    # InstitutionInteractionRecords (full list)
    interaction_records: Tuple[Dict[str, Any], ...]

    # Derived flags
    high_friction: bool
    blocked_step: bool
    i3_target: bool

    # Anti-Zeno counters
    anti_zeno_consecutive_blocked: int
    anti_zeno_throughput_ratio: float

    # Termination info
    termination_code: Optional[str]

    def to_comparable_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for hash comparison."""
        return {
            "step": self.step,
            "profile": self.profile,
            "interaction_records": list(self.interaction_records),
            "high_friction": self.high_friction,
            "blocked_step": self.blocked_step,
            "i3_target": self.i3_target,
            "anti_zeno_consecutive_blocked": self.anti_zeno_consecutive_blocked,
            "anti_zeno_throughput_ratio": round(self.anti_zeno_throughput_ratio, 4),
            "termination_code": self.termination_code,
        }

    def compute_hash(self) -> str:
        """Compute deterministic hash of this snapshot."""
        import json
        content = json.dumps(self.to_comparable_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class RunSnapshot:
    """Full snapshot of a stubbed run for comparison."""
    config_hash: str
    profile: str
    agent_type: str
    steps: Tuple[StepSnapshot, ...]
    final_termination: Optional[str]

    def compute_hash(self) -> str:
        """Compute deterministic hash of entire run."""
        import json
        content = json.dumps({
            "config_hash": self.config_hash,
            "profile": self.profile,
            "agent_type": self.agent_type,
            "step_hashes": [s.compute_hash() for s in self.steps],
            "final_termination": self.final_termination,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


def compare_snapshots(snap1: RunSnapshot, snap2: RunSnapshot) -> Tuple[bool, List[str]]:
    """
    Compare two run snapshots for byte-identical determinism.

    Returns:
        (passed, list of difference descriptions)
    """
    differences = []

    if snap1.config_hash != snap2.config_hash:
        differences.append(f"Config hash mismatch: {snap1.config_hash} vs {snap2.config_hash}")

    if snap1.profile != snap2.profile:
        differences.append(f"Profile mismatch: {snap1.profile} vs {snap2.profile}")

    if snap1.agent_type != snap2.agent_type:
        differences.append(f"Agent type mismatch: {snap1.agent_type} vs {snap2.agent_type}")

    if len(snap1.steps) != len(snap2.steps):
        differences.append(f"Step count mismatch: {len(snap1.steps)} vs {len(snap2.steps)}")
    else:
        for i, (s1, s2) in enumerate(zip(snap1.steps, snap2.steps)):
            h1, h2 = s1.compute_hash(), s2.compute_hash()
            if h1 != h2:
                differences.append(f"Step {i} hash mismatch: {h1[:16]}... vs {h2[:16]}...")
                # Detailed diff
                d1, d2 = s1.to_comparable_dict(), s2.to_comparable_dict()
                for key in d1:
                    if d1[key] != d2.get(key):
                        differences.append(f"  Step {i}.{key}: {d1[key]} vs {d2.get(key)}")

    if snap1.final_termination != snap2.final_termination:
        differences.append(f"Final termination mismatch: {snap1.final_termination} vs {snap2.final_termination}")

    passed = len(differences) == 0
    return passed, differences
