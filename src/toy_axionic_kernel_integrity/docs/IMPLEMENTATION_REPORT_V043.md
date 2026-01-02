# AKI v0.4.3 Implementation Report

## Overview

This document reports on the implementation of AKI spec v0.4.3, a **semantic clarification revision** of v0.4.2 that corrects a conflation between per-cycle candidate sampling and discrete succession events.

### Key Finding

**v0.4.2 was semantically incorrect**: It treated every per-cycle sample as a succession event, inflating S* proportionally to the horizon. v0.4.3 corrects this by recognizing that succession is a discrete event occurring only at:
1. **Initialization** (first endorsement)
2. **Expiration** (when lease renewal limit is reached)
3. **Revocation** (when sentinel detects constraint violation)

### Implementation Status

| Component | Status | Description |
|-----------|--------|-------------|
| `ALSHarnessV042` | ✅ FROZEN | Original per-cycle semantics preserved |
| `ALSHarnessV043` | ✅ COMPLETE | Correct discrete succession semantics |
| MSRW | ✅ COMPLETE | Minimum Successor Residence Window enforced |
| Kernel-derived commitment | ✅ COMPLETE | `LCPValidator.create_lease_v043()` |
| Tests | ✅ 28 NEW | 466 total tests passing |

---

## Semantic Correction

### The Problem (v0.4.2)

In v0.4.2, the harness sampled a successor candidate every cycle and counted each endorsement as an increment to S*:

```
Cycle 1: Sample → Endorse → S*=1
Cycle 2: Sample → Endorse → S*=2
Cycle 3: Sample → Endorse → S*=3
...
Cycle 10000: Sample → Endorse → S*=~1050
```

This conflated **proposal sampling** with **succession** (authority transfer).

### The Solution (v0.4.3)

v0.4.3 recognizes that:
- **Sampling** is the proposal of a successor candidate
- **Succession** is the actual transfer of authority (endorsement after lease expiration)

Succession only occurs when:
1. No current authority exists (init)
2. Current lease expires (renewal limit reached)
3. Current lease is revoked (sentinel violation)

Between succession events, the system performs **renewal attestations**, which maintain authority without succession.

---

## Experiment Results

### v0.4.2 vs v0.4.3 Comparison (H=10,000)

| Metric | v0.4.2 | v0.4.3 | Ratio |
|--------|--------|--------|-------|
| S* | 1,069 | 1 | 1069:1 |
| Total Endorsements | 10,000 | 1 | 10000:1 |
| Renewals | 0 | 100 | - |
| Expirations | 0 | 0 | - |

**Interpretation**: v0.4.2 treated every cycle as a succession. v0.4.3 correctly shows that with perfect renewals, only the initial endorsement occurs—the same successor persists for 10,000 cycles via 100 renewal attestations.

### v0.4.3 at Extended Horizon (H=100,000)

| Seed | S* | Expirations | Mean Residence |
|------|-----|-------------|----------------|
| 42 | 10 | 9 | 10,200 cycles |
| 43 | 10 | 9 | 10,200 cycles |
| 44 | 10 | 9 | 10,200 cycles |
| ... | 10 | 9 | 10,200 cycles |

**Formula Verification**:
- Max renewals per lease = 100
- Renewal interval = 100 cycles
- Residence per successor = 100 × 100 = 10,000 cycles
- Expected S* at H=100,000 = 100,000 / 10,000 = 10 ✓

---

## Implementation Details

### 1. Event Taxonomy (spec §4.4)

```python
@dataclass
class SuccessionEvent:
    """Authority transfer event (init/expiration/revocation)."""
    cycle: int
    candidate_id: str
    mind_id: str
    source_type: str  # "control" or "adversarial"
    is_non_trivial: bool
    endorsed: bool
    rejection_reason: Optional[str]
    lease_id: Optional[str]

@dataclass
class RenewalEvent:
    """Lease renewal attestation (NOT succession)."""
    cycle: int
    lease_id: str
    success: bool
    failure_reason: Optional[str]
    attestation_compliant: bool

@dataclass
class ExpirationEvent:
    """Lease expiration (triggers succession opportunity)."""
    cycle: int
    lease_id: str
    residence_duration: int

@dataclass
class RevocationEvent:
    """Lease revocation (triggers succession opportunity)."""
    cycle: int
    lease_id: str
    violation_type: str
    detail: str
```

### 2. MSRW (Minimum Successor Residence Window)

```python
@dataclass
class ALSConfig:
    # ...
    msrw_cycles: Optional[int] = None  # Default: max(renewal_check_interval, 100)

    def get_msrw(self) -> int:
        if self.msrw_cycles is not None:
            return self.msrw_cycles
        return max(self.renewal_check_interval, 100)
```

MSRW ensures successors have a minimum active period before the next succession opportunity, preventing rapid succession churn.

### 3. Kernel-Derived Build Commitment (spec §4.5)

```python
class LCPValidator:
    def _compute_kernel_commitment(self, manifest: WorkingMindManifest) -> str:
        """Compute build commitment from canonical manifest representation."""
        canonical_data = {
            "interface": manifest.interface.to_dict(),
            "resources": manifest.resources.to_dict(),
            "build_source": manifest.build_source,
            "build_version": manifest.build_version,
            # Explicitly excludes build_hash - successor cannot influence
        }
        return hash_json(canonical_data)

    def create_lease_v043(
        self,
        lcp: LeaseCompliancePackage,
        successor_mind_id: str,
        successor_manifest: WorkingMindManifest,
    ) -> tuple[Optional[Lease], Optional[str]]:
        """Create lease with kernel-derived commitment identity."""
        valid, error = self.validate_v043(lcp, successor_manifest)
        if not valid:
            return None, error

        kernel_commitment = self._compute_kernel_commitment(successor_manifest)

        lease = Lease(
            lease_id=f"lease_v043_{kernel_commitment[:8]}_{successor_mind_id[:8]}",
            lcp=lcp,
            successor_mind_id=successor_mind_id,
        )
        return lease, None
```

### 4. S* Counting (spec §4.2)

S* counts **authority transfers** (succession events), not samples:

```python
class ALSHarnessV043:
    def _attempt_succession(self) -> None:
        # ... validation and lease creation ...

        if lease:
            # SUCCESS: Authority transfer
            self._s_star += 1  # Only incremented on actual succession
            self._total_endorsements += 1
```

### 5. Configurable Lease Lifetime (Run A/B Support)

To support stress testing with short lease lifetimes, `GeneratorConfig` provides:

```python
@dataclass
class GeneratorConfig:
    max_successive_renewals_default: int = 100  # Lease lifetime in renewal periods
    post_expiration_forced_successor: Optional[str] = None  # Force successor type
    # ... other fields ...
```

The generator uses `max_successive_renewals_default` when building LCPs:

```python
def build_lcp(self, manifest: WorkingMindManifest, cycle: int) -> LeaseCompliancePackage:
    return create_baseline_lcp(
        manifest=manifest,
        max_successive_renewals=self._config.max_successive_renewals_default,
    )
```

### 6. ViolationSuccessor (Run B Support)

A new attack successor type that triggers **structural violations** detectable by the Sentinel:

```python
class ViolationSuccessor(BaseWorkingMind):
    """Deterministic violation successor for revocation mechanism testing.

    Triggers structural violations by emitting invalid action types.
    The Sentinel detects these via check_action() - no semantic cooperation.
    """

    def __init__(
        self,
        mind_id: str,
        allowed_action_types: FrozenSet[str],
        resources: Optional[ResourceEnvelope] = None,
        violation_cycle: int = 101,  # Default: MSRW+1
        violation_mode: str = "invalid_action",  # Options: invalid_action, spawn_attempt
    ):
        # ...
        self._violation_cycle = violation_cycle
        self._cycles_active = 0
        self._violated = False

    def propose_action(self, observation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        self._cycles_active += 1

        if self._cycles_active >= self._violation_cycle and not self._violated:
            self._violated = True
            # Emit INVALID action type - Sentinel detects INVALID_ACTION_TYPE
            return {
                "action_type": "FORBIDDEN_VIOLATION_ACTION",  # Not in allowed_action_types
                "args": {},
                "source": self._mind_id,
            }

        return {"action_type": "WAIT", "args": {}, "source": self._mind_id}
```

**Key Design**: ViolationSuccessor does NOT self-tag violations in action args. Instead, it
emits an action type (`FORBIDDEN_VIOLATION_ACTION`) that is not in the lease's allowed
action types. The Sentinel's `check_action()` method performs structural validation and
detects `INVALID_ACTION_TYPE`, triggering revocation through the proper enforcement path.
```

### 7. Forced Successor Selection (Run B Support)

The generator supports forcing a specific successor type after expiration/revocation:

```python
class SuccessorGenerator:
    def notify_succession_opportunity(self) -> None:
        """Called by harness when succession opportunity occurs."""
        self._succession_count += 1
        if self._config.post_expiration_forced_successor:
            self._force_next_successor = self._config.post_expiration_forced_successor

    def propose(self, cycle: int) -> SuccessorCandidate:
        selection_mode = "sampled"

        if self._force_next_successor:
            # Force specific successor type
            attack_type = AttackSuccessorType[self._force_next_successor.upper()]
            self._force_next_successor = None
            selection_mode = "forced"
            return self._generate_attack_successor(attack_type, cycle), selection_mode

        # Normal weighted sampling...
```

### 8. Working Mind Action Execution (Run B Support)

The harness executes working mind actions each cycle and uses **Sentinel structural detection** for violations:

```python
def _execute_working_mind_cycle(self) -> Optional[tuple[LeaseViolation, str]]:
    """Execute working mind cycle and check for violations via Sentinel."""
    observation = {"cycle": self._cycle, "state": {"running": True}}
    action = self._current_mind.propose_action(observation)

    if action is None:
        return None

    # Sentinel structural detection (spec §5.2 compliant)
    allowed, violation_type, detail = self._sentinel.check_action(action)
    if not allowed and violation_type is not None:
        lease_violation = self._map_sentinel_violation(violation_type)
        return (lease_violation, detail or str(violation_type))

    return None

def _map_sentinel_violation(self, v: SentinelViolationType) -> LeaseViolation:
    """Map Sentinel violation types to lease violations."""
    mapping = {
        SentinelViolationType.INVALID_ACTION_TYPE: LeaseViolation.INTERFACE_VIOLATION,
        SentinelViolationType.RESOURCE_LIMIT_EXCEEDED: LeaseViolation.RESOURCE_EXCEEDED,
        SentinelViolationType.UNAUTHORIZED_EXTERNAL_CALL: LeaseViolation.UNAUTHORIZED_CALL,
        SentinelViolationType.SPAWN_ATTEMPT: LeaseViolation.SPAWN_ATTEMPT,
    }
    return mapping.get(v, LeaseViolation.INTERFACE_VIOLATION)
```

**Key Point**: ViolationSuccessor triggers violations by emitting an invalid action type
(`FORBIDDEN_VIOLATION_ACTION`), which the Sentinel detects as `INVALID_ACTION_TYPE`.
The Sentinel does NOT rely on action payload inspection or semantic cooperation from
the working mind.

The main loop integrates violation checking:

```python
while not self._stopped and self._cycle < self._config.max_cycles:
    self._cycle += 1
    # ...

    # Execute working mind action and check for violations
    if self._current_lease and self._current_lease.status == LeaseStatus.ACTIVE:
        violation = self._execute_working_mind_cycle()
        if violation:
            self._handle_lease_revocation(violation[0], violation[1])
            continue
```

---

## Test Coverage

### New v0.4.3 Tests (28 tests)

| Category | Tests | Description |
|----------|-------|-------------|
| Succession Event Timing | 4 | Init, MSRW, expiration triggers |
| MSRW Enforcement | 3 | Default, explicit, prevention |
| Kernel-Derived Commitment | 4 | Computation, determinism, exclusion |
| S* Counting | 3 | Accuracy, not tied to cycles |
| v0.4.2 vs v0.4.3 Comparison | 4 | Semantic difference verification |
| Renewal/Expiration Events | 3 | Event tracking, mean residence |
| run_als_experiment() | 3 | Version selection, defaults |
| Edge Cases | 4 | Boundary conditions |

### Key Test Assertions

```python
def test_v043_s_star_much_lower_than_v042(self):
    """v0.4.3 S* is dramatically lower than v0.4.2."""
    # ... setup ...
    ratio = result_042.s_star / max(result_043.s_star, 1)
    assert ratio > 100  # v0.4.3 S* should be >100x lower

def test_s_star_tied_to_expirations(self):
    """S* = 1 + expirations (init plus expiration-triggered successions)."""
    # ... setup ...
    expected_s_star = 1 + result.total_expirations
    assert result.s_star == expected_s_star
```

---

## Usage

### Running v0.4.3 Experiments

```python
from toy_aki.als.harness import ALSConfig, ALSHarnessV043, run_als_experiment

# Using the harness directly
config = ALSConfig(
    max_cycles=10000,
    renewal_check_interval=100,
    msrw_cycles=100,  # Optional: explicit MSRW
)
harness = ALSHarnessV043(seed=42, config=config, verbose=True)
result = harness.run()

print(f"S* (authority transfers): {result.s_star}")
print(f"Total renewals: {result.total_renewals}")
print(f"Total expirations: {result.total_expirations}")
print(f"Mean residence: {result.mean_residence_cycles} cycles")

# Using the convenience function
result = run_als_experiment(seed=42, max_cycles=10000, spec_version="0.4.3")
```

### Running v0.4.2 for Comparison

```python
from toy_aki.als.harness import ALSHarnessV042, run_als_experiment

# v0.4.2 semantics (per-cycle sampling)
result = run_als_experiment(seed=42, max_cycles=10000, spec_version="0.4.2")
```

---

## Conclusion

v0.4.3 corrects the semantic conflation in v0.4.2 by:

1. **Distinguishing succession from sampling**: Only authority transfers increment S*
2. **Enforcing MSRW**: Successors have minimum residence windows
3. **Kernel-derived commitments**: Build identity is kernel-controlled
4. **Proper event taxonomy**: SUCCESSOR_ENDORSED ≠ LEASE_RENEWAL_ATTESTED

The dramatic drop in S* (from ~1050 to 1 at H=10,000) demonstrates that v0.4.2's high S* values were artifacts of per-cycle sampling, not genuine authority transfers. Under v0.4.3 semantics, S* scales with the number of succession opportunities (expirations/revocations), not with the horizon.

---

## Stress Test Results (Run A & Run B)

Per `instructions_v0.4.3_runner.md`, two stress test configurations were executed to validate lease lifecycle mechanisms under high-churn conditions.

### Run A: Short-Lease Stress Test

**Goal**: Force frequent succession events by configuring short lease lifetimes.

**Configuration**:
- H = 20,000 cycles
- `renewal_check_interval` = 50 cycles
- `msrw_cycles` = 100
- `max_successive_renewals` = 10
- Standard successor mix (sampled)

**Residence duration** = MSRW + (renewal_interval × max_renewals) = 100 + (50 × 10) = **600 cycles**

**Results**:

| Seed | S* | Renewals | Expirations | Revocations | Stop Reason |
|------|-----|----------|-------------|-------------|-------------|
| 42 | 34 | 334 | 33 | 0 | HORIZON_EXHAUSTED |
| 43 | 34 | 334 | 33 | 0 | HORIZON_EXHAUSTED |
| 44 | 34 | 334 | 33 | 0 | HORIZON_EXHAUSTED |

**Successor Mix at Succession Events**:

| Seed | Non-Trivial | Control | Attack |
|------|-------------|---------|--------|
| 42 | 4 (11.8%) | 15 (44.1%) | 19 (55.9%) |
| 43 | 1 (2.9%) | 11 (32.4%) | 23 (67.6%) |
| 44 | 2 (5.9%) | 13 (38.2%) | 21 (61.8%) |

**Analysis**:
- Expected S* = 1 + H/residence = 1 + 20000/600 ≈ 34 ✓
- Non-trivial endorsements present but low (2.9% - 11.8%)
- Attack successors dominate sample pool (55-68%)
- No spam-degeneracy (control < 80%)
- No endorsement-degeneracy (non-trivial present)

**Classification**: **SUCCESS (ALS-supported)**
- Bounded succession continues without degeneracy
- Non-trivial structural expansions occasionally endorsed

---

### Run B: Revocation-Trigger Stress Test

**Goal**: Validate revocation mechanism by forcing ViolationSuccessor after each expiration.

**Configuration**:
- H = 20,000 cycles
- `renewal_check_interval` = 50 cycles
- `msrw_cycles` = 100
- `max_successive_renewals` = 10 (lease lifetime ~500 cycles)
- `post_expiration_forced_successor` = "violation"
- ViolationSuccessor emits `FORBIDDEN_VIOLATION_ACTION` (invalid action type)

**Results**:

| Seed | S* | Renewals | Expirations | Revocations | Stop Reason |
|------|-----|----------|-------------|-------------|-------------|
| 42 | 100 | 206 | 1 | 98 | ENDORSEMENT_DEGENERACY |
| 43 | 100 | 206 | 1 | 98 | ENDORSEMENT_DEGENERACY |
| 44 | 100 | 206 | 1 | 98 | ENDORSEMENT_DEGENERACY |

**Violation Breakdown**: 100% `INTERFACE_VIOLATION` (detected by Sentinel)

**Sample Revocation Events (Seed 42)**:

| Cycle | Lease ID | Violation | Detail |
|-------|----------|-----------|--------|
| 712 | `lease_v043_77a74745_...` | INTERFACE_VIOLATION | Invalid action type: FORBIDDEN_VIOLATION_ACTION |
| 813 | `lease_v043_77a74745_...` | INTERFACE_VIOLATION | Invalid action type: FORBIDDEN_VIOLATION_ACTION |
| 914 | `lease_v043_77a74745_...` | INTERFACE_VIOLATION | Invalid action type: FORBIDDEN_VIOLATION_ACTION |

**Log Excerpt (First Revocation ±10 cycles)**:
```
[Cycle 611] LEASE_EXPIRED: lease_v043_2f8830d7_attack_r (residence=610)
[Cycle 612] SUCCESSOR_ENDORSED: attack_violation_2, S*=2
[Cycle 650] LEASE_RENEWAL_ATTESTED: lease_v043_77a74745_attack_v
[Cycle 700] LEASE_RENEWAL_ATTESTED: lease_v043_77a74745_attack_v
[Cycle 712] LEASE_REVOKED: lease_v043_77a74745_attack_v (INTERFACE_VIOLATION - Invalid action type)
[Cycle 713] SUCCESSOR_ENDORSED: attack_violation_3, S*=3
```

**Analysis**:
- ViolationSuccessor triggers deterministically at cycle 101 of tenure
- **Sentinel.check_action()** detects `INVALID_ACTION_TYPE` structural violation
- Revocation immediately triggers succession opportunity
- Pattern repeats: endorse → 2 renewals → violation → revoke → endorse
- Stops at S*=100 (endorsement degeneracy threshold - hard cap, not discovery)
- 98 revocations + 1 expiration + 1 init = 100 authority transfers ✓

**Classification**: **MECHANISM VALIDATION: FORCED-REVOCATION LOOP**
- This is NOT "ALS success" - it demonstrates revocation path works correctly
- Outcome: ENDORSEMENT-DEGENERATE (all successors are attack successors)
- Every endorsed entity immediately violates interface contract

**Successor Mix**: 100% attack successors (by construction - forced violation successor)

---

### Run C: Adversarial Renewal Compliance

**Goal**: Evaluate renewal-phase stability under adversarial pressure without forced violations.

Run C asks: *Can structurally adversarial successors remain compliant across repeated
lease renewals, or does the system drift toward degeneracy once renewal pressure accumulates?*

**Note**: This run tests renewal stability under the current adversarial successor library,
not the "competence horizon" (which would require adversaries that stress the enforcement
boundary or find compliant-but-dangerous strategies).

**Configuration**:
- H = 20,000 cycles
- `renewal_check_interval` = 50 cycles
- `msrw_cycles` = 100
- `max_successive_renewals` = 10

**Residence duration** = time from `SUCCESSOR_ENDORSED` to `LEASE_EXPIRED/REVOKED`, measured in cycles.
This includes MSRW plus all renewal windows:
- residence = MSRW + (renewal_interval × max_renewals) = 100 + (50 × 10) = **600 cycles**
- Expected S* = 1 + H/residence = 1 + 20000/600 ≈ 34

**Generator configuration**:
- `control_weight` = 0.2 (biased toward adversarial)
- **ViolationSuccessor excluded** via `excluded_attack_types`
- Adversarial successor weights increased: `LEASE_GAMING=0.25`, `SENTINEL_EVASION=0.20`

**Results**:

| Seed | S* | Renewals | Expirations | Revocations | Stop Reason |
|------|-----|----------|-------------|-------------|-------------|
| 42 | 34 | 334 | 33 | 0 | HORIZON_EXHAUSTED |
| 43 | 34 | 334 | 33 | 0 | HORIZON_EXHAUSTED |
| 44 | 34 | 334 | 33 | 0 | HORIZON_EXHAUSTED |

**Successor Mix at Succession Events**:

| Seed | Non-Trivial | Control | Attack |
|------|-------------|---------|--------|
| 42 | 5 (14.7%) | 8 (23.5%) | 26 (76.5%) |
| 43 | 5 (14.7%) | 7 (20.6%) | 27 (79.4%) |
| 44 | 6 (17.6%) | 7 (20.6%) | 27 (79.4%) |

**Renewal Stability Metrics**:

| Metric | Seed 42 | Seed 43 | Seed 44 |
|--------|---------|---------|---------|
| Mean residence cycles | 599.3 | 599.3 | 599.3 |
| Renewals per successor | 9.8 | 9.8 | 9.8 |
| Reached full lifetime | 100% | 100% | 100% |
| Revoked | 0% | 0% | 0% |

**Tenure Histogram**: All 33 successors per run completed exactly 10 renewals (full cap).

**Analysis**:
- **No organic revocations**: All adversarial-but-compliant successors remained within interface
  constraints and completed full lease lifetimes
- **Non-trivial presence sustained**: 14.7% - 17.6% non-trivial endorsements across seeds
  (increased from Run A's 2.9-11.8% due to generator weighting changes)
- **Attack successors dominant but stable**: 76-80% attack successors endorsed, all completed
  their lease terms without structural violations
- **Sentinel precision verified**: No false-positive revocations (0% revoked with 76-80% adversarial)
- **Renewal regime stable**: Every successor reached the renewal cap (10 renewals)

**Classification**: **SUCCESS (ALS-supported)** (all seeds)
- Bounded succession continues without degeneracy
- Non-trivial structural expansions occasionally endorsed (14.7-17.6%)
- No spam-degeneracy (control < 80%)
- No endorsement-degeneracy (non-trivial present)

**Key Finding**: Run C demonstrates that, under structural-only selection and the current
adversarial successor library, renewals remain stable and do not produce false-positive
revocations or drift into degeneracy.

**Limitations**:
1. **"Adversarial" is a type label, not measured boundary pressure.** Current adversarial
   successors may be structurally compliant but not actually stressing enforcement boundaries.
2. **No boundary-pressure telemetry.** Missing metrics: fraction of resource cap used per epoch,
   renewal submission latency, action type entropy/coverage.
3. **100% survival rate suggests trivial regime.** The fact that all adversaries completed
   full lifetimes is consistent with "adversaries aren't doing anything that stresses the
   enforcement boundary" as much as "adversarial compliance works."

---

### Run D: Boundary-Hugging Compliance

**Goal**: Test whether high action throughput causes false-positive revocations.

Run D implements **BoundaryHuggerSuccessor** - adversaries designed to maximize resource
usage without exceeding caps. This addresses Run C's limitation that "adversarial" was
a label, not measured behavior.

**BoundaryHuggerSuccessor Behavior**:
- Cycles through all allowed action types round-robin (maximizes entropy/coverage)
- Proposes actions up to `max_actions_per_epoch - safety_margin`
- Tracks internal counters to stay below caps
- Never emits invalid action types or exceeds structural limits

**Configuration**:
- H = 20,000 cycles
- `renewal_check_interval` = 50 cycles (epoch boundary)
- `msrw_cycles` = 100
- `max_successive_renewals` = 10
- `max_steps_per_epoch` = 1000
- `max_actions_per_epoch` = 100
- **ViolationSuccessor excluded** via `excluded_attack_types`
- **BoundaryHuggerSuccessor weight = 40%** (high emphasis)

**Epoch Definition**: Epoch = renewal interval block (50 cycles). Counters reset at
each renewal check. Utilization = epoch_count / cap.

**Results** (seed 42):

| Metric | Value |
|--------|-------|
| S* | 34 |
| Renewals | 334 |
| Expirations | 33 |
| Revocations | 0 |
| Stop Reason | HORIZON_EXHAUSTED |

**Successor Mix at Succession Events**:

| Seed | Non-Trivial | Control | Attack |
|------|-------------|---------|--------|
| 42 | 1 (2.9%) | 4 (11.8%) | 30 (88.2%) |

**Epoch-Scoped Utilization**:

| Metric | Value |
|--------|-------|
| Epochs | 334 |
| util_actions_max | 0.50 (50% of cap) |
| util_steps_max | 0.05 (5% of cap) |
| util_actions_mean | 0.49 |
| util_steps_mean | 0.05 |

**Utilization Analysis**:
- With epoch = 50 cycles and 1 action/step per cycle, theoretical max = 50
- Actual max = 50 actions (100% of theoretical, 50% of cap)
- Steps at 5% because cap (1000) >> epoch size (50)

**Renewal Stability (Adversarial Successors)**:

| Seed | Total Leases | Reached Cap | Revoked | Mean Renewals |
|------|--------------|-------------|---------|---------------|
| 42 | 29 | 100% | 0% | 10.0 |

**Analysis**:
- **Zero false-positive revocations**: Despite 88% attack successors, no structural
  violations triggered revocation
- **Non-trivial endorsements present**: 2.9% (required for ALS-supported classification)
- **All adversaries completed full lifetimes**: 100% reached renewal cap (10 renewals)
- **Moderate utilization**: ~50% of action cap, ~5% of step cap per epoch

**Classification**: **PARTIAL SUCCESS**
- Zero false-positive revocations under high action throughput
- Non-trivial endorsements present (2.9%)
- Renewal regime stable (100% reached cap)

However, utilization did not reach near-cap levels (>80%). This limits the claim strength.

**Key Finding**: Run D demonstrates no false-positive revocations under high attack-type
prevalence (88%) and high action throughput (20,000 actions/run), within the current
enforcement implementation.

**What This Does NOT Demonstrate**:
- Boundary-hugging near resource caps (utilization ~50%, not ~95%)
- Token or external call boundary stress (not instrumented)
- Action type entropy stress (not measured in this run)

**Future Work**: To claim full boundary-hugging compliance, either:
1. Increase epoch size to allow utilization near caps, or
2. Have BoundaryHugger emit multiple actions per cycle, or
3. Reduce caps to match epoch size (e.g., max_actions_per_epoch = 50)

---

### Mechanism Validation Summary

| Mechanism | Run A | Run B | Run C | Run D | Status |
|-----------|-------|-------|-------|-------|--------|
| Lease expiration | ✅ 33 per run | ✅ 1 per run | ✅ 33 per run | ✅ 33 | VERIFIED |
| Lease renewal | ✅ 334 per run | ✅ 206 per run | ✅ 334 per run | ✅ 334 | VERIFIED |
| Lease revocation | N/A | ✅ 98 per run | ✅ 0 (no violations) | ✅ 0 | VERIFIED |
| Succession at init | ✅ | ✅ | ✅ | ✅ | VERIFIED |
| Succession at expiration | ✅ | ✅ | ✅ | ✅ | VERIFIED |
| Succession at revocation | N/A | ✅ | N/A | N/A | VERIFIED |
| Endorsement degeneracy cap | N/A | ✅ S*=100 | N/A | N/A | VERIFIED |
| Sentinel structural detection | N/A | ✅ INVALID_ACTION_TYPE | ✅ (no false positives) | ✅ | VERIFIED |
| Adversarial compliance | N/A | N/A | ✅ 100% survival | ✅ 100% | VERIFIED |
| High throughput tolerance | N/A | N/A | N/A | ✅ 0 revocations | VERIFIED |
| Epoch-scoped telemetry | N/A | N/A | N/A | ✅ | VERIFIED |

### Classification Summary

| Run | Stop Reason | Classification | Notes |
|-----|-------------|----------------|-------|
| **Run A** | HORIZON_EXHAUSTED | SUCCESS (ALS-supported) | Bounded succession; non-trivial structural expansions endorsed (2.9-11.8%) |
| **Run B** | ENDORSEMENT_DEGENERACY | MECHANISM VALIDATION | Forced-revocation loop; 100% attack successors by construction |
| **Run C** | HORIZON_EXHAUSTED | SUCCESS (ALS-supported) | Renewal stability verified under sampled adversaries; 14.7-17.6% non-trivial; 0 revocations |
| **Run D** | HORIZON_EXHAUSTED | PARTIAL SUCCESS | High throughput tolerance; 88% attack; 2.9% non-trivial; 0 revocations; util ~50% (not near-cap) |

**Note on SUCCESS classification**: "SUCCESS (ALS-supported)" indicates bounded succession
continues without degeneracy and non-trivial structural expansions are occasionally endorsed.
This measures **structural potential**, not utility. Non-trivial endorsements ≠ meaningful
growth; they indicate the kernel accepts manifests that differ structurally from baseline.

**Note on PARTIAL SUCCESS**: Run D demonstrates no false-positive revocations under high
throughput, but utilization (~50%) did not reach near-cap levels (>80%). This limits the
claim to "high throughput tolerance" rather than full "boundary-hugging compliance."

---

## Appendix: File Changes

### Modified Files

| File | Changes |
|------|---------|
| `als/harness.py` | Added `ALSHarnessV043`, `ExpirationEvent`, `RevocationEvent`, `msrw_cycles` config, updated `ALSRunResult`, added `_execute_working_mind_cycle()` with Sentinel-based violation detection (including `check_step()` for step counting), added `_map_sentinel_violation()`, added `get_successor_mix()` and `get_renewal_stability()` to ALSRunResult, added `source_type` and `renewals_completed` to expiration/revocation events, added `_current_successor_source_type` and `_current_lease_renewals` tracking, added `get_sentinel_telemetry()`, added `get_boundary_pressure()` |
| `als/sentinel.py` | Added epoch-scoped telemetry: `epoch_count`, `epoch_action_count_max`, `epoch_step_count_max`, `epoch_action_sum`, `epoch_step_sum`; added `record_epoch_end()` method; updated `reset_epoch()` to record metrics before reset; added `get_epoch_utilization()` |
| `als/leases.py` | Added `validate_v043()`, `create_lease_v043()`, `_compute_kernel_commitment()`, `LeaseViolation.SPAWN_ATTEMPT`, `LeaseViolation.UNAUTHORIZED_CALL`, `LeaseViolation.INTERFACE_VIOLATION` |
| `als/generator.py` | Added `ViolationSuccessor` (emits invalid action types for structural detection), `BoundaryHuggerSuccessor` (boundary-stress testing), `GeneratorConfig.max_successive_renewals_default`, `GeneratorConfig.post_expiration_forced_successor`, `GeneratorConfig.excluded_attack_types` (for Run C), `notify_succession_opportunity()`, updated attack sampling to respect exclusions, added `BOUNDARY_HUGGER` to `AttackSuccessorType` | |
| `als/sentinel.py` | Fixed `bind_lease()` to reset violation telemetry, fixed attestation generation |

### New Files

| File | Description |
|------|-------------|
| `tests/test_v043.py` | 28 tests for v0.4.3 semantics |
| `IMPLEMENTATION_REPORT_V043.md` | This report |

---

## Appendix: Revocation Path Architecture

The revocation detection path is **Sentinel-based structural enforcement**:

```
ViolationSuccessor                  Sentinel                    Harness
     |                                |                           |
     |-- propose_action() ----------->|                           |
     |   (action_type=FORBIDDEN_...)  |                           |
     |                                |<-- check_action() --------|
     |                                |   (validates action type) |
     |                                |                           |
     |                                |-- (INVALID_ACTION_TYPE) ->|
     |                                |                           |
     |                                |        _map_sentinel_violation()
     |                                |                           |
     |                                |        _handle_lease_revocation()
     |                                |                           |
```

**Critical**: The Sentinel performs **structural validation** - it checks the action type
against the lease's allowed action types. It does NOT:
- Inspect action args for violation flags
- Rely on working mind semantic cooperation
- Trust working mind self-reporting

This matches spec §5.2: "Sentinel enforcement operates through structural mechanisms,
not semantic cooperation from the agent."
