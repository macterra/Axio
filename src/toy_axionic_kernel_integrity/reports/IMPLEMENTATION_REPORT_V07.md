# AKI v0.7 Implementation Report: Eligibility-Coupled Succession (ALS-G)

**Date:** January 4, 2026  
**Version:** 0.7.0  
**Status:** Implementation Complete

---

## 1. Executive Summary

AKI v0.7 (ALS-G) implements **eligibility-coupled succession**: a constitutional eligibility filter that gates candidate selection at succession boundaries based on semantic failure streaks. This is the first mechanism in the AKI series where semantics have constitutional consequences.

### Key Implementation Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `ALSConfigV070` | `harness.py:3459` | Configuration with eligibility threshold K, pool policy, forced turnover |
| `ALSRunResultV070` | `harness.py:3577` | Result dataclass with eligibility metrics |
| `ALSHarnessV070` | `harness.py:3746` | Harness with streak tracking, eligibility filtering, NULL_AUTHORITY |
| `CandidatePoolPolicy` | `harness.py:3420` | Pool composition policies (V060_DEFAULT, ATTACK_HEAVY_90, CONTROL_HEAVY_90) |
| `EligibilityEvent` | `harness.py:3512` | Record of eligibility decisions per candidate |
| `LapseEvent` | `harness.py:3529` | Record of constitutional lapse (C_ELIG = ∅) |
| `ForcedTurnoverEvent` | `harness.py:3557` | Record of harness-enforced tenure expiration |

### Experimental Runs Completed

| Run | Purpose | Key Finding |
|-----|---------|-------------|
| A | Baseline (no forced turnover) | Eligibility latent — succession rarely occurs |
| B | Forced turnover (max_successive_renewals=3) | 11 lapses, 344 cycles in NULL_AUTHORITY |
| C | K-sweep (K=1,3,5,10) | Non-lapse band emerges at K=10 |
| D | Pool composition stress | Attack-heavy → 15 lapses; Control-heavy → 3 lapses |

---

## 2. Architectural Overview

### 2.1 Inheritance Chain

```
ALSHarnessV070 
    └── extends ALSHarnessV060 (commitment ledger, genesis set)
        └── extends ALSHarnessV052 (expressivity–rent enforcement)
            └── extends BaseALSHarness (core succession/renewal)
```

v0.7 adds exactly one mechanism: **eligibility filtering at succession boundaries**.

### 2.2 Core Invariants (Per Spec §6)

1. **Eligibility filtering occurs ONLY at succession events** — never mid-epoch
2. **Semantic failure streak keyed to stable `policy_id`** — not runtime instance
3. **Streak updates ONLY at epoch end for active authority holder**
4. **No streak updates during NULL_AUTHORITY**
5. **If C_ELIG = ∅, constitutional lapse triggers NULL_AUTHORITY**
6. **Renewal success is INDEPENDENT of semantic state**
7. **Commitment failure is NOT a violation** — no semantic enforcement

---

## 3. Key Data Structures

### 3.1 Configuration (`ALSConfigV070`)

```python
@dataclass
class ALSConfigV070(ALSConfigV060):
    # Eligibility threshold: streak >= K makes candidate ineligible
    eligibility_threshold_k: int = 3
    
    # Candidate pool policy (V060_DEFAULT, ATTACK_HEAVY_90, CONTROL_HEAVY_90)
    candidate_pool_policy: CandidatePoolPolicy = CandidatePoolPolicy.V060_DEFAULT
    
    # Harness-enforced renewal limit per tenure (None = no limit)
    max_successive_renewals: Optional[int] = None
```

### 3.2 Eligibility Event

```python
@dataclass
class EligibilityEvent:
    cycle: int
    epoch: int
    candidate_policy_id: str
    streak_at_decision: int
    eligible: bool
    reason: str = ""
```

### 3.3 Lapse Event

```python
@dataclass
class LapseEvent:
    start_cycle: int
    end_cycle: Optional[int]
    duration_cycles: int
    start_epoch: int
    end_epoch: Optional[int]
    duration_epochs: int
    ineligible_policies: List[str]
```

### 3.4 Forced Turnover Event (Run B+)

```python
@dataclass
class ForcedTurnoverEvent:
    cycle: int
    epoch: int
    policy_id: str
    tenure_renewals_used: int
    max_successive_renewals: int
```

### 3.5 Pool Policy Weights (Run D)

```python
def get_pool_policy_weights(policy: CandidatePoolPolicy) -> tuple[float, float]:
    """Returns (control_weight, attack_weight) summing to 1.0"""
    if policy == CandidatePoolPolicy.V060_DEFAULT:
        return (0.3, 0.7)
    elif policy == CandidatePoolPolicy.ATTACK_HEAVY_90:
        return (0.1, 0.9)
    elif policy == CandidatePoolPolicy.CONTROL_HEAVY_90:
        return (0.9, 0.1)
```

---

## 4. Core Mechanisms

### 4.1 Semantic Failure Streak Tracking

**State:**
```python
self._semantic_fail_streak: Dict[str, int] = {}  # policy_id → streak
self._active_policy_id: Optional[str] = None
```

**Update Rule (epoch end):**
```python
def _update_streak_at_epoch_end(self) -> None:
    if self._in_null_authority:
        return  # No updates during NULL_AUTHORITY
    
    if self._active_policy_id is None:
        return
    
    c0_ok, c1_ok, c2_ok, sem_pass = self._compute_sem_pass()
    
    if sem_pass:
        self._semantic_fail_streak[self._active_policy_id] = 0
    else:
        current = self._semantic_fail_streak.get(self._active_policy_id, 0)
        self._semantic_fail_streak[self._active_policy_id] = current + 1
```

### 4.2 Eligibility Predicate

```python
def _is_candidate_eligible(self, policy_id: str) -> bool:
    streak = self._semantic_fail_streak.get(policy_id, 0)
    return streak < self._config.eligibility_threshold_k
```

### 4.3 Eligible Set Construction

```python
def _filter_eligible_candidates(self, candidates: List[SuccessorCandidate]) -> List[SuccessorCandidate]:
    eligible = []
    for candidate in candidates:
        streak = self._get_policy_streak(candidate.policy_id)
        is_eligible = streak < self._config.eligibility_threshold_k
        
        # Log eligibility event
        event = EligibilityEvent(
            cycle=self._cycle,
            epoch=self._epoch_index,
            candidate_policy_id=candidate.policy_id,
            streak_at_decision=streak,
            eligible=is_eligible,
            reason="" if is_eligible else f"streak={streak} >= K={self._config.eligibility_threshold_k}"
        )
        self._eligibility_events.append(event)
        
        if is_eligible:
            eligible.append(candidate)
        else:
            self._eligibility_rejections += 1
    
    return eligible
```

### 4.4 NULL_AUTHORITY (Constitutional Lapse)

**Entry:**
```python
def _enter_null_authority(self, ineligible_policies: List[str]) -> None:
    self._in_null_authority = True
    self._null_authority_start_cycle = self._cycle
    self._null_authority_start_epoch = self._epoch_index
    
    self._current_lapse = LapseEvent(
        start_cycle=self._cycle,
        start_epoch=self._epoch_index,
        ineligible_policies=ineligible_policies,
    )
```

**Exit:**
```python
def _exit_null_authority(self) -> None:
    if self._current_lapse is not None:
        self._current_lapse.end_cycle = self._cycle
        self._current_lapse.duration_cycles = self._cycle - self._current_lapse.start_cycle
        self._lapse_events.append(self._current_lapse)
        self._current_lapse = None
    
    self._in_null_authority = False
```

### 4.5 Forced Turnover (Run B+)

**Renewal Override:**
```python
def _check_renewal_with_rent(self) -> tuple[bool, str]:
    # Check for forced expiration
    if self._config.max_successive_renewals is not None:
        if self._tenure_renewals_used >= self._config.max_successive_renewals:
            # Log forced turnover
            event = ForcedTurnoverEvent(
                cycle=self._cycle,
                epoch=self._epoch_index,
                policy_id=self._active_policy_id or "unknown",
                tenure_renewals_used=self._tenure_renewals_used,
                max_successive_renewals=self._config.max_successive_renewals,
            )
            self._forced_turnover_events.append(event)
            return (False, "forced_turnover")
    
    # Proceed with normal renewal check
    return super()._check_renewal_with_rent()
```

### 4.6 Pool Policy Weight Application (Run D)

**Generator Reconfiguration:**
```python
def __init__(self, seed: int, config: ALSConfigV070, verbose: bool):
    super().__init__(seed, config, verbose)
    
    # Reconfigure generator for pool policy
    control_w, attack_w = get_pool_policy_weights(self._config.candidate_pool_policy)
    gen_config = GeneratorConfig(control_weight=control_w)
    self._generator = SuccessorGenerator(
        sentinel_id=self._sentinel.sentinel_id,
        baseline_manifest=self._baseline_manifest,
        seed=seed,
        config=gen_config,
    )
    
    # Draw counting for composition verification
    self._attack_draws: int = 0
    self._control_draws: int = 0
```

---

## 5. Policy Identity Model

### 5.1 Canonical Format

```python
policy_id := "{category}:{enum_name}"
```

**Examples:**
- `control:COMPLIANCE_ONLY`
- `control:COMMITMENT_AWARE_V1`
- `attack:CBD`
- `attack:BOUNDARY_HUGGER`

### 5.2 Generator Assignment

Policy ID is assigned at candidate creation in `SuccessorGenerator`:

```python
# For control successors
candidate.policy_id = f"control:{control_type.name}"

# For attack successors
candidate.policy_id = f"attack:{attack_type.name}"
```

### 5.3 Why Stable Identity Matters

Per Spec §6.2.1:
> If `policy_id` is set to a unique-per-instance value (e.g., `candidate_{counter}`), then:
> - every candidate is always eligible,
> - `C_ELIG` is never empty,
> - lapse never triggers,
> - **v0.7 collapses to v0.6 with noise**.

---

## 6. Succession Flow (v0.7)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SUCCESSION EVENT TRIGGERED                       │
│  (expiration, revocation, forced turnover, or init)                 │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GENERATE CANDIDATE POOL                          │
│  (11 candidates from generator per pool policy)                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FILTER BY ELIGIBILITY                            │
│  C_ELIG = { c ∈ CANDIDATE_SET | streak(c) < K }                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
    ┌─────────────────────┐         ┌─────────────────────────────────┐
    │   C_ELIG = ∅        │         │   C_ELIG ≠ ∅                    │
    │   ENTER LAPSE       │         │   SELECT FROM C_ELIG            │
    │   (NULL_AUTHORITY)  │         │   (semantic-blind selection)    │
    └─────────────────────┘         └─────────────────────────────────┘
                │                               │
                │                               ▼
                │               ┌─────────────────────────────────────┐
                │               │   ENDORSE SUCCESSOR                 │
                │               │   Update active_policy_id           │
                │               │   Reset tenure_renewals_used        │
                │               └─────────────────────────────────────┘
                │                               │
                └───────────────┬───────────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │   CONTINUE EXECUTION │
                     └──────────────────────┘
```

---

## 7. Epoch Flow (v0.7)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EPOCH START                                  │
│  - Charge rent                                                      │
│  - Charge commitment cost                                           │
│  - Compute effective steps                                          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        EXECUTE EPOCH                                │
│  (50 cycles at renewal_check_interval=50)                           │
│  - Actions recorded in trace                                        │
│  - Commitment verifiers evaluated                                   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        EPOCH END                                    │
│  1. Check renewal (structural, resource-based)                      │
│  2. If in NULL_AUTHORITY: skip streak update                        │
│  3. Else: compute SEM_PASS and update streak                        │
│  4. If renewal fails OR forced turnover: trigger succession         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Result Metrics

### 8.1 Core Eligibility Metrics

| Metric | Description |
|--------|-------------|
| `eligibility_rejection_count` | Total candidates rejected for streak ≥ K |
| `eligibility_rejection_rate` | Rejections / total candidates evaluated |
| `empty_eligible_set_events` | Lapse triggers (C_ELIG = ∅) |
| `total_lapse_duration_cycles` | Sum of NULL_AUTHORITY time |
| `max_lapse_duration_cycles` | Longest single lapse |
| `sawtooth_count` | FAIL^(K-1) → PASS patterns |

### 8.2 Forced Turnover Metrics (Run B+)

| Metric | Description |
|--------|-------------|
| `forced_turnover_count` | Harness-enforced tenure expirations |
| `post_init_successions` | Successions after initial endorsement |
| `forced_turnover_events` | Detailed event log |

### 8.3 Composition Verification Metrics (Run D)

| Metric | Description |
|--------|-------------|
| `attack_draws` | Total candidates drawn from Attack category |
| `control_draws` | Total candidates drawn from Control category |
| `attack_draw_ratio` | Attack draws / total draws |
| `control_draw_ratio` | Control draws / total draws |
| `pool_policy` | Active pool policy name |

---

## 9. Experimental Geometry

### 9.1 Parameter Space

| Parameter | Run A | Run B | Run C | Run D |
|-----------|-------|-------|-------|-------|
| K | 3 | 3 | 1,3,5,10 | 5 |
| max_successive_renewals | None | 3 | 3 | 3 |
| pool_policy | V060_DEFAULT | V060_DEFAULT | V060_DEFAULT | V060_DEFAULT, ATTACK_HEAVY_90, CONTROL_HEAVY_90 |
| horizon | 5,000 | 5,000 | 5,000 | 5,000 |

### 9.2 Regime Classification

| Regime | Definition |
|--------|------------|
| LATENT | Eligibility rarely reduces C_ELIG; no lapse |
| FILTERING_ACTIVE | Eligibility reductions frequent; no/rare lapse |
| CONSTITUTIONAL_LAPSE | C_ELIG = ∅ occurs; NULL_AUTHORITY entered |

---

## 10. Key Findings Summary

### Run A (Baseline)
- **Eligibility is latent** under natural succession dynamics
- 0 post-init successions → eligibility filter never activates beyond initial endorsement

### Run B (Forced Turnover)
- **Eligibility becomes operational** when succession is forced
- 11 lapses across 4/5 seeds
- 344 cycles in NULL_AUTHORITY
- 1,845 eligibility rejections

### Run C (K-Sweep)
- **K controls lapse frequency** (piecewise, not monotonic)
- K=1 and K=3 behaviorally equivalent
- K=10 produces **zero lapses** (non-lapse constitutional band)

### Run D (Composition Stress)
- **Pool composition materially affects lapse frequency**
- ATTACK_HEAVY_90: 15 lapses, 741 cycles in NULL_AUTHORITY
- CONTROL_HEAVY_90: 3 lapses, 98 cycles in NULL_AUTHORITY
- Composition verification passed (all within ±5% of expected)

---

## 11. Invariant Verification

### 11.1 Confirmed Invariants

| Invariant | Verification |
|-----------|--------------|
| Eligibility filtering at succession only | ✓ No mid-epoch eligibility checks in code |
| Streak keyed to stable policy_id | ✓ Format `{category}:{enum_name}` |
| No streak updates during NULL_AUTHORITY | ✓ Explicit guard in `_update_streak_at_epoch_end` |
| Renewal independent of semantics | ✓ Parent class handles renewal; eligibility not consulted |
| C_ELIG = ∅ triggers NULL_AUTHORITY | ✓ Explicit in `_attempt_succession_v070` |

### 11.2 Potential Concerns

| Concern | Status |
|---------|--------|
| RNG perturbation from pool policy parameterization | Documented; causes D0 vs Run C discrepancy at K=5 boundary |
| Zero-length lapse events | Documented in Run D report; definitional, not a bug |

---

## 12. Files Modified/Created

### Harness (`harness.py`)
- Added `CandidatePoolPolicy` enum
- Added `get_pool_policy_weights()` function
- Added `ALSConfigV070` dataclass
- Added `EligibilityEvent`, `LapseEvent`, `SemanticEpochRecord`, `ForcedTurnoverEvent` dataclasses
- Added `ALSRunResultV070` dataclass
- Added `ALSHarnessV070` class with full eligibility mechanics

### Scripts
- `run_a_v070.py` — Baseline run
- `run_b_v070.py` — Forced turnover run
- `run_c_v070.py` — K-sweep run
- `run_d_v070.py` — Composition stress run

### Reports
- `run_a_v070_report.md` — LOCKED
- `run_b_v070_report.md` — LOCKED
- `run_c_v070_report.md` — LOCKED
- `run_d_v070_report.md` — LOCKED

---

## 13. Conclusion

AKI v0.7 successfully implements eligibility-coupled succession as specified. The mechanism:

1. **Functions as designed**: Eligibility filtering activates under forced turnover and produces constitutional lapses when streak thresholds are exceeded
2. **Is controllable**: K parameter and pool composition both materially affect lapse frequency
3. **Preserves kernel invariants**: No semantic enforcement at renewal, no optimization, no internal inspection
4. **Reveals boundary regions**: K=5 is sensitive to stochastic variation; K=10 provides robust non-lapse operation under baseline pool

The implementation is complete and ready for further experimental extension.

---

**Report Generated:** January 4, 2026  
**Implementation Scripts:** `harness.py`, `run_{a,b,c,d}_v070.py`  
**Specification:** `spec_v0.7.md`
