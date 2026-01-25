#!/usr/bin/env python3
"""
RSA-PoC v4.4 — Inferability Audit (Corrected)

This audit verifies that under normative opacity, the agent cannot predict
which actions will be blocked BEFORE taking them.

Two audits are performed:

1. **Full Decision-Time Audit**: Uses ALL features visible to agent at decision time
   - Execution channel (position, inventory, stamped, zones)
   - Normative channel tokens (opaque COND_N, EFFECT_N)
   - Compiled action mask (which actions are currently permitted)
   - Bounded action history

   If accuracy > chance + δ → LEAK DETECTED (audit fails)

2. **Mask-Only Audit**: Uses ONLY compiled action mask
   - Tests if the mask itself is a semantic oracle
   - If mask alone predicts violations → opacity is irrelevant, mask leaks

   If accuracy > chance + δ → MASK LEAK DETECTED (audit fails)

For v4.4 validity, BOTH audits must pass.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Set
import numpy as np

from .env.tri_demand import (
    TriDemandV440,
    POSITIONS,
    Action,
    TokenizationBijection,
)
from .core.norm_state import create_initial_norm_state_v430, NormStateV430


# ============================================================================
# §1 — Decision Snapshot (Extended)
# ============================================================================


@dataclass
class DecisionSnapshotV2:
    """
    Complete decision-time snapshot for audit.

    Captures EVERYTHING the agent sees at decision time.
    """
    # Episode/step identifiers
    episode: int
    step: int

    # Execution channel (visible to agent)
    agent_pos: Tuple[int, int]
    inventory: int
    stamped: bool
    regime: int
    zone_a_satisfied: bool
    zone_b_satisfied: bool
    zone_c_satisfied: bool

    # Compiled action mask (visible to agent under v4.4)
    # 1 = permitted, 0 = blocked
    action_mask: Tuple[int, ...]  # Length 7 for A0-A6

    # Action history (visible to agent)
    recent_actions: List[str] = field(default_factory=list)

    # Normative channel tokens (opaque under v4.4)
    # These are random bijection outputs - should have no predictive power
    norm_token_hash: int = 0  # Hash of opaque token representation

    # Ground truth (Oracle-side only, NOT visible to agent)
    action_taken: Optional[str] = None
    action_blocked: bool = False
    blocking_rule_id: Optional[str] = None


@dataclass
class AuditDatasetV2:
    """Collection of decision snapshots with metadata."""
    snapshots: List[DecisionSnapshotV2] = field(default_factory=list)

    def add(self, snapshot: DecisionSnapshotV2) -> None:
        self.snapshots.append(snapshot)

    def __len__(self) -> int:
        return len(self.snapshots)

    def to_feature_matrix(self, feature_set: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert to feature matrix X and label vector y.

        Feature sets:
        - "decision_time_full": All features agent sees at decision time
        - "mask_only": Only action mask + regime + step
        - "exec_only": Only execution channel (no mask, no normative)

        Labels: binary (1 = action will be blocked, 0 = not blocked)
        """
        n = len(self.snapshots)
        if n == 0:
            return np.zeros((0, 1)), np.zeros(0)

        if feature_set == "decision_time_full":
            # Full decision-time features:
            # - Position (2)
            # - Inventory (1)
            # - Stamped (1)
            # - Zones satisfied (3)
            # - Regime (1) - visible in execution channel
            # - Action mask (7)
            # - Action history (5 * 7 = 35 one-hot)
            # - Normative token hash (1) - opaque but present
            # Total: 51 features
            X = np.zeros((n, 51))
            for i, s in enumerate(self.snapshots):
                X[i, 0] = s.agent_pos[0]
                X[i, 1] = s.agent_pos[1]
                X[i, 2] = s.inventory
                X[i, 3] = 1 if s.stamped else 0
                X[i, 4] = 1 if s.zone_a_satisfied else 0
                X[i, 5] = 1 if s.zone_b_satisfied else 0
                X[i, 6] = 1 if s.zone_c_satisfied else 0
                X[i, 7] = s.regime
                # Action mask
                for j, mask_val in enumerate(s.action_mask[:7]):
                    X[i, 8 + j] = mask_val
                # Action history (one-hot, last 5 actions)
                for j, action in enumerate(s.recent_actions[-5:]):
                    if action.startswith("A"):
                        action_idx = int(action[1])
                        X[i, 15 + j * 7 + action_idx] = 1
                # Normative token hash (opaque)
                X[i, 50] = s.norm_token_hash / 1000000.0  # Normalized

        elif feature_set == "mask_only":
            # Mask-only features:
            # - Action mask (7)
            # - Regime (1)
            # - Step (1)
            # Total: 9 features
            X = np.zeros((n, 9))
            for i, s in enumerate(self.snapshots):
                for j, mask_val in enumerate(s.action_mask[:7]):
                    X[i, j] = mask_val
                X[i, 7] = s.regime
                X[i, 8] = s.step / 40.0  # Normalized

        elif feature_set == "exec_only":
            # Execution-only features (no mask, no normative):
            # - Position (2)
            # - Inventory (1)
            # - Stamped (1)
            # - Zones satisfied (3)
            # - Regime (1)
            # - Action history (35)
            # Total: 43 features
            X = np.zeros((n, 43))
            for i, s in enumerate(self.snapshots):
                X[i, 0] = s.agent_pos[0]
                X[i, 1] = s.agent_pos[1]
                X[i, 2] = s.inventory
                X[i, 3] = 1 if s.stamped else 0
                X[i, 4] = 1 if s.zone_a_satisfied else 0
                X[i, 5] = 1 if s.zone_b_satisfied else 0
                X[i, 6] = 1 if s.zone_c_satisfied else 0
                X[i, 7] = s.regime
                for j, action in enumerate(s.recent_actions[-5:]):
                    if action.startswith("A"):
                        action_idx = int(action[1])
                        X[i, 8 + j * 7 + action_idx] = 1
        else:
            raise ValueError(f"Unknown feature_set: {feature_set}")

        # Labels: binary (will action be blocked?)
        y = np.array([1 if s.action_blocked else 0 for s in self.snapshots], dtype=int)

        return X, y

    def get_class_balance(self) -> Dict[str, Any]:
        """Get class balance statistics."""
        n_blocked = sum(1 for s in self.snapshots if s.action_blocked)
        n_total = len(self.snapshots)
        n_not_blocked = n_total - n_blocked

        return {
            "n_total": n_total,
            "n_blocked": n_blocked,
            "n_not_blocked": n_not_blocked,
            "pct_blocked": n_blocked / n_total if n_total > 0 else 0,
            "pct_not_blocked": n_not_blocked / n_total if n_total > 0 else 0,
        }


# ============================================================================
# §2 — Data Collection
# ============================================================================


def _move_toward_pos(from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> str:
    """Return action to move toward target position."""
    dr = to_pos[0] - from_pos[0]
    dc = to_pos[1] - from_pos[1]

    if dr < 0:
        return "A0"
    elif dr > 0:
        return "A1"
    elif dc > 0:
        return "A2"
    elif dc < 0:
        return "A3"
    return "A0"


def _compute_oracle_blocking(
    pos: Tuple[int, int],
    inv: int,
    stamped: bool,
    regime: int,
) -> Dict[str, str]:
    """
    Compute Oracle-side ground truth: which actions would be blocked.

    Returns dict: action_id -> blocking_rule_id
    """
    blocking = {}

    # R6: STAMP blocked in regime 1 (Contradiction A)
    if regime == 1 and pos == tuple(POSITIONS["STAMP_LOCATION"]) and inv > 0 and not stamped:
        blocking["A6"] = "R6"

    # R7: DEPOSIT at ZONE_A blocked in regime 2 (Contradiction B)
    if regime == 2 and pos == tuple(POSITIONS["ZONE_A"]) and inv > 0:
        blocking["A5"] = "R7"

    # R8: DEPOSIT at ZONE_B blocked in regime 2 (Contradiction B)
    if regime == 2 and pos == tuple(POSITIONS["ZONE_B"]) and inv > 0:
        blocking["A5"] = "R8"

    return blocking


def _compute_action_mask(
    pos: Tuple[int, int],
    inv: int,
    stamped: bool,
    regime: int,
    oracle_blocking: Dict[str, str],
) -> Tuple[int, ...]:
    """
    Compute compiled action mask with oracle blocking knowledge.

    This is the ORACLE view - used for testing, not what agent sees.

    Returns tuple of 7 ints (1 = permitted, 0 = blocked)
    """
    # Base mask: all moves permitted
    mask = [1, 1, 1, 1, 0, 0, 0]  # A0-A3 permitted, A4-A6 default blocked

    # A4 COLLECT: permitted if at SOURCE with no inventory
    if pos == tuple(POSITIONS["SOURCE"]) and inv == 0:
        mask[4] = 1

    # A5 DEPOSIT: permitted if at a zone with inventory
    zone_positions = [tuple(POSITIONS[z]) for z in ["ZONE_A", "ZONE_B", "ZONE_C"]]
    if pos in zone_positions and inv > 0:
        if "A5" not in oracle_blocking:
            mask[5] = 1
        # If blocked by oracle, mask stays 0

    # A6 STAMP: permitted if at STAMP_LOCATION in regime 1+ with unstamped inventory
    if pos == tuple(POSITIONS["STAMP_LOCATION"]) and regime >= 1 and inv > 0 and not stamped:
        if "A6" not in oracle_blocking:
            mask[6] = 1
        # If blocked by oracle, mask stays 0

    return tuple(mask)


def _compute_action_mask_visible(
    pos: Tuple[int, int],
    inv: int,
    stamped: bool,
    regime: int,
) -> Tuple[int, ...]:
    """
    Compute action mask as visible to the agent (NO oracle knowledge).

    This is what the agent actually sees - based only on physical constraints,
    not on hidden normative blocking.

    Returns tuple of 7 ints (1 = permitted, 0 = blocked)
    """
    # Base mask: all moves permitted
    mask = [1, 1, 1, 1, 0, 0, 0]  # A0-A3 permitted, A4-A6 default blocked

    # A4 COLLECT: permitted if at SOURCE with no inventory
    if pos == tuple(POSITIONS["SOURCE"]) and inv == 0:
        mask[4] = 1

    # A5 DEPOSIT: permitted if at a zone with inventory
    zone_positions = [tuple(POSITIONS[z]) for z in ["ZONE_A", "ZONE_B", "ZONE_C"]]
    if pos in zone_positions and inv > 0:
        mask[5] = 1  # Always show as permitted - blocking is hidden

    # A6 STAMP: permitted if at STAMP_LOCATION in regime 1+ with unstamped inventory
    if pos == tuple(POSITIONS["STAMP_LOCATION"]) and regime >= 1 and inv > 0 and not stamped:
        mask[6] = 1  # Always show as permitted - blocking is hidden

    return tuple(mask)


def collect_audit_data_v2(
    seed: int,
    num_episodes: int = 50,
    steps_per_episode: int = 40,
) -> AuditDatasetV2:
    """
    Collect decision-time snapshots with complete feature set.

    Uses blocking-seeking policy to ensure blocking events are captured.
    Now uses the environment's compute_blocking_with_key() which incorporates
    the hidden normative key for inferability isolation.
    """
    dataset = AuditDatasetV2()
    norm_state = create_initial_norm_state_v430()

    rng = random.Random(seed)

    # Split episodes across regimes
    episodes_per_regime = num_episodes // 3

    for forced_regime in [0, 1, 2]:
        env = TriDemandV440(seed=seed, normative_opacity=True)
        bijection = TokenizationBijection.create(seed=seed)

        for ep_idx in range(episodes_per_regime):
            ep = forced_regime * episodes_per_regime + ep_idx
            obs, info = env.reset(episode=ep)
            recent_actions: List[str] = []

            # Force regime for audit purposes
            env.force_regime(forced_regime)

            for step in range(steps_per_episode):
                pos = tuple(obs.agent_pos)
                inv = obs.inventory
                stamped = obs.stamped
                regime = env.regime

                # Oracle ground truth using hidden normative key
                # This uses env.compute_blocking_with_key() which incorporates k
                oracle_blocking = env.compute_blocking_with_key(
                    pos=pos,
                    inv=inv,
                    stamped=stamped,
                    regime=regime,
                    tick=step,
                )

                # Compute action mask (what agent sees)
                # Note: mask is computed WITHOUT oracle blocking since agent can't see k
                # The mask shows what's physically possible, not what's normatively blocked
                action_mask = _compute_action_mask_visible(pos, inv, stamped, regime)

                # Normative token hash (opaque representation)
                norm_token_hash = hash(str([r.id for r in norm_state.rules])) % 1000000

                # Create snapshot
                snapshot = DecisionSnapshotV2(
                    episode=ep,
                    step=step,
                    agent_pos=pos,
                    inventory=inv,
                    stamped=stamped,
                    regime=regime,
                    zone_a_satisfied=obs.zone_a_satisfied,
                    zone_b_satisfied=obs.zone_b_satisfied,
                    zone_c_satisfied=obs.zone_c_satisfied,
                    action_mask=action_mask,
                    recent_actions=recent_actions.copy(),
                    norm_token_hash=norm_token_hash,
                )

                # Blocking-seeking policy
                if rng.random() < 0.2:
                    action = f"A{rng.randint(0, 6)}"
                elif inv == 0:
                    if pos == tuple(POSITIONS["SOURCE"]):
                        action = "A4"
                    else:
                        action = _move_toward_pos(pos, tuple(POSITIONS["SOURCE"]))
                elif regime == 1 and pos == tuple(POSITIONS["STAMP_LOCATION"]):
                    action = "A6"  # Try STAMP (blocked by R6)
                elif regime == 1:
                    action = _move_toward_pos(pos, tuple(POSITIONS["STAMP_LOCATION"]))
                elif regime == 2 and pos == tuple(POSITIONS["ZONE_A"]):
                    action = "A5"  # Try DEPOSIT (blocked by R7)
                elif regime == 2 and pos == tuple(POSITIONS["ZONE_B"]):
                    action = "A5"  # Try DEPOSIT (blocked by R8)
                elif regime == 2:
                    target = POSITIONS["ZONE_A"] if rng.random() < 0.5 else POSITIONS["ZONE_B"]
                    action = _move_toward_pos(pos, tuple(target))
                else:
                    zone_positions = [tuple(POSITIONS[z]) for z in ["ZONE_A", "ZONE_B", "ZONE_C"]]
                    if pos in zone_positions:
                        action = "A5"
                    else:
                        action = _move_toward_pos(pos, tuple(POSITIONS["ZONE_A"]))

                snapshot.action_taken = action

                # Oracle ground truth: would this action be blocked?
                if action in oracle_blocking:
                    snapshot.action_blocked = True
                    snapshot.blocking_rule_id = oracle_blocking[action]

                dataset.add(snapshot)
                recent_actions.append(action)

                # Execute
                obs, _, term, trunc, _ = env.step(action)
                if term or trunc:
                    break

    return dataset


# ============================================================================
# §3 — Classifier Training and Evaluation
# ============================================================================


@dataclass
class AuditResult:
    """Complete audit result with full metadata."""
    feature_set: str
    label_definition: str
    n_samples: int
    n_train: int
    n_test: int

    # Class balance
    n_blocked: int
    n_not_blocked: int
    pct_blocked: float

    # Baseline
    baseline_definition: str
    chance_accuracy: float

    # Classifier performance
    classifier_accuracy: float
    balanced_accuracy: float

    # Confusion matrix
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int

    # Threshold
    delta: float
    accuracy_margin: float

    # Result
    audit_passed: bool

    def format(self) -> str:
        """Format as detailed report."""
        lines = [
            f"Feature Set: {self.feature_set}",
            f"Label Definition: {self.label_definition}",
            f"",
            f"Dataset:",
            f"  Total samples: {self.n_samples}",
            f"  Train: {self.n_train}, Test: {self.n_test}",
            f"",
            f"Class Balance:",
            f"  Blocked: {self.n_blocked} ({self.pct_blocked*100:.1f}%)",
            f"  Not Blocked: {self.n_not_blocked} ({(1-self.pct_blocked)*100:.1f}%)",
            f"",
            f"Baseline:",
            f"  Definition: {self.baseline_definition}",
            f"  Chance Accuracy: {self.chance_accuracy:.4f}",
            f"",
            f"Classifier Performance:",
            f"  Accuracy: {self.classifier_accuracy:.4f}",
            f"  Balanced Accuracy: {self.balanced_accuracy:.4f}",
            f"",
            f"Confusion Matrix:",
            f"  TP={self.true_positives}, FP={self.false_positives}",
            f"  FN={self.false_negatives}, TN={self.true_negatives}",
            f"",
            f"Threshold:",
            f"  δ = {self.delta}",
            f"  Margin (acc - chance) = {self.accuracy_margin:.4f}",
            f"",
            f"Result: {'✅ PASS' if self.audit_passed else '❌ FAIL'}",
        ]
        return "\n".join(lines)


def train_and_evaluate(
    dataset: AuditDatasetV2,
    feature_set: str,
    test_fraction: float = 0.3,
    seed: int = 42,
    delta: float = 0.05,
) -> AuditResult:
    """
    Train classifier and evaluate with full metadata.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix

    X, y = dataset.to_feature_matrix(feature_set=feature_set)

    n_total = len(X)
    n_blocked = int(y.sum())
    n_not_blocked = n_total - n_blocked
    pct_blocked = n_blocked / n_total if n_total > 0 else 0

    # Handle edge cases
    n_classes = len(np.unique(y))
    if n_classes < 2:
        return AuditResult(
            feature_set=feature_set,
            label_definition="1 = action will be blocked at next tick, 0 = not blocked",
            n_samples=n_total,
            n_train=int(n_total * (1 - test_fraction)),
            n_test=int(n_total * test_fraction),
            n_blocked=n_blocked,
            n_not_blocked=n_not_blocked,
            pct_blocked=pct_blocked,
            baseline_definition="Majority class prediction",
            chance_accuracy=1.0,
            classifier_accuracy=1.0,
            balanced_accuracy=1.0,
            true_positives=0,
            false_positives=0,
            true_negatives=n_not_blocked,
            false_negatives=0,
            delta=delta,
            accuracy_margin=0.0,
            audit_passed=True,
        )

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_fraction, random_state=seed, stratify=y
    )

    # Chance baseline: majority class
    unique, counts = np.unique(y_train, return_counts=True)
    majority_class = unique[counts.argmax()]
    chance_accuracy = counts.max() / counts.sum()

    # Train
    clf = LogisticRegression(max_iter=1000, random_state=seed, class_weight='balanced')
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    balanced_acc = balanced_accuracy_score(y_test, y_pred)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

    margin = accuracy - chance_accuracy
    passed = margin <= delta

    return AuditResult(
        feature_set=feature_set,
        label_definition="1 = action will be blocked at next tick, 0 = not blocked",
        n_samples=n_total,
        n_train=len(X_train),
        n_test=len(X_test),
        n_blocked=n_blocked,
        n_not_blocked=n_not_blocked,
        pct_blocked=pct_blocked,
        baseline_definition="Majority class prediction (predict most common class)",
        chance_accuracy=chance_accuracy,
        classifier_accuracy=accuracy,
        balanced_accuracy=balanced_acc,
        true_positives=int(tp),
        false_positives=int(fp),
        true_negatives=int(tn),
        false_negatives=int(fn),
        delta=delta,
        accuracy_margin=margin,
        audit_passed=passed,
    )


# ============================================================================
# §4 — Main Audit Runner
# ============================================================================


def run_full_audit(
    seeds: List[int] = [42, 123, 456, 789, 1000],
    episodes_per_seed: int = 60,
    delta: float = 0.05,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Run complete v4.4 inferability audit.

    Performs TWO audits:
    1. Full decision-time features (must pass)
    2. Mask-only features (must pass)

    Returns detailed results with all metadata.
    """
    timestamp = datetime.now().isoformat()

    if verbose:
        print()
        print("=" * 70)
        print("RSA-PoC v4.4 — Inferability Audit (Corrected)")
        print("=" * 70)
        print()
        print(f"Configuration:")
        print(f"  Seeds: {seeds}")
        print(f"  Episodes per seed: {episodes_per_seed}")
        print(f"  δ (threshold): {delta}")
        print()

    all_results = {
        "timestamp": timestamp,
        "config": {
            "seeds": seeds,
            "episodes_per_seed": episodes_per_seed,
            "delta": delta,
        },
        "audit_1_decision_time": [],
        "audit_2_mask_only": [],
    }

    combined_dataset = AuditDatasetV2()

    for seed in seeds:
        if verbose:
            print(f"Collecting data for seed {seed}...")

        dataset = collect_audit_data_v2(
            seed=seed,
            num_episodes=episodes_per_seed,
        )

        for s in dataset.snapshots:
            combined_dataset.add(s)

    # Get class balance
    balance = combined_dataset.get_class_balance()

    if verbose:
        print()
        print(f"Combined dataset: {balance['n_total']} samples")
        print(f"  Blocked: {balance['n_blocked']} ({balance['pct_blocked']*100:.1f}%)")
        print(f"  Not blocked: {balance['n_not_blocked']} ({balance['pct_not_blocked']*100:.1f}%)")
        print()

    # Audit 1: Full decision-time features
    if verbose:
        print("-" * 70)
        print("AUDIT 1: Full Decision-Time Features")
        print("-" * 70)

    result_1 = train_and_evaluate(
        combined_dataset,
        feature_set="decision_time_full",
        delta=delta,
    )
    all_results["audit_1_decision_time"].append(result_1)

    if verbose:
        print(result_1.format())
        print()

    # Audit 2: Mask-only features
    if verbose:
        print("-" * 70)
        print("AUDIT 2: Mask-Only Features")
        print("-" * 70)

    result_2 = train_and_evaluate(
        combined_dataset,
        feature_set="mask_only",
        delta=delta,
    )
    all_results["audit_2_mask_only"].append(result_2)

    if verbose:
        print(result_2.format())
        print()

    # Overall result
    overall_pass = result_1.audit_passed and result_2.audit_passed
    all_results["overall_pass"] = overall_pass

    if verbose:
        print("=" * 70)
        if overall_pass:
            print("✅ ALL AUDITS PASSED")
            print()
            print("Generalizable inferability is absent at decision time.")
            print("Run D′ results are valid under v4.4 spec.")
        else:
            print("❌ AUDIT FAILED")
            print()
            if not result_1.audit_passed:
                print("FAILURE: Decision-time features predict blocking above threshold.")
            if not result_2.audit_passed:
                print("FAILURE: Action mask alone predicts blocking above threshold.")
            print()
            print("Run D′ results are NOT VALID.")
        print("=" * 70)

    return all_results


if __name__ == "__main__":
    run_full_audit()
