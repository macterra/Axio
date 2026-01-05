# AKI v0.8 Implementation Report: Constitutional Temporal Amnesty (ALS-A)

**Date:** January 5, 2026
**Version:** 0.8.0
**Status:** Implementation Complete

---

## 1. Executive Summary

AKI v0.8 (ALS-A) implements **Constitutional Temporal Amnesty (CTA)**: a deterministic, time-only rule that applies exclusively during `NULL_AUTHORITY` to enable eligibility recovery without semantic optimization. This is the first mechanism in the AKI series that modifies streak state during lapse.

### Key Implementation Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `ALSConfigV080` | `harness.py:4575` | Configuration with AMNESTY_INTERVAL, AMNESTY_DECAY, cta_enabled |
| `ALSRunResultV080` | `harness.py:4594` | Result dataclass with CTA metrics |
| `ALSHarnessV080` | `harness.py:4787` | Harness with CTA mechanism, lapse cause classification |
| `LapseCause` | `harness.py:4472` | SEMANTIC vs STRUCTURAL lapse classification |
| `AmnestyEvent` | `harness.py:4484` | Record of streak decay application |
| `RecoveryEvent` | `harness.py:4507` | Record of recovery with authority duration tracking |
| `LapseEventV080` | `harness.py:4540` | Extended lapse event with cause and recovery status |

### Experimental Runs Completed

| Run | Purpose | Key Finding |
|-----|---------|-------------|
| A | CTA Baseline (AMNESTY_INTERVAL=10) | 100% recovery rate, 0% stutter, 69% recover without amnesty |

---

## 2. Architectural Overview

### 2.1 Inheritance Chain

```
ALSHarnessV080
    └── extends ALSHarnessV070 (eligibility filtering, NULL_AUTHORITY)
        └── extends ALSHarnessV060 (commitment ledger, genesis set)
            └── extends ALSHarnessV052 (expressivity–rent enforcement)
                └── extends BaseALSHarness (core succession/renewal)
```

v0.8 adds exactly one mechanism: **Constitutional Temporal Amnesty during NULL_AUTHORITY**.

### 2.2 Core Invariants (Per Spec §6)

1. **CTA runs ONLY during NULL_AUTHORITY** — never during active authority
2. **CTA is ONLY permitted streak modification during lapse** — no increments, no resets
3. **No agent action during lapse** — streak decay is autonomous
4. **No verifiers execute during lapse** — commitment evaluation suspended
5. **TTL clocks advance during lapse** — time marches on
6. **Succession attempts at scheduled boundaries only** — not every epoch
7. **Candidate pool regenerated on every succession attempt**
8. **Global cycles and epochs continue unchanged during lapse**

---

## 3. Key Data Structures

### 3.1 Configuration (`ALSConfigV080`)

```python
@dataclass
class ALSConfigV080(ALSConfigV070):
    # CTA parameters (frozen defaults per spec)
    amnesty_interval: int = 10   # Epochs between amnesty applications
    amnesty_decay: int = 1       # Streak decrement per amnesty

    # Enable/disable CTA (for comparison runs)
    cta_enabled: bool = True
```

### 3.2 Lapse Cause Classification

```python
class LapseCause(Enum):
    """
    Classification of lapse cause per spec §6.2.

    - SEMANTIC: Candidates exist but all are ineligible (streak >= K)
    - STRUCTURAL: No structurally admissible candidates exist
    """
    SEMANTIC = auto()
    STRUCTURAL = auto()
```

### 3.3 Amnesty Event

```python
@dataclass
class AmnestyEvent:
    """Record of a CTA amnesty application during NULL_AUTHORITY."""
    cycle: int
    epoch: int
    lapse_epoch_count: int
    policies_affected: List[str]
    streak_deltas: Dict[str, int]  # policy_id -> decrement applied
    aggregate_streak_mass_before: int
    aggregate_streak_mass_after: int
```

### 3.4 Recovery Event

```python
@dataclass
class RecoveryEvent:
    """Record of a recovery from NULL_AUTHORITY."""
    cycle: int
    epoch: int
    lapse_duration_cycles: int
    lapse_duration_epochs: int
    amnesty_events_during_lapse: int
    lapse_cause: LapseCause
    recovered_policy_id: str
    streak_at_recovery: int
    # Authority span tracking (for stutter detection)
    authority_epochs_after: Optional[int] = None
    authority_end_reason: Optional[str] = None  # "LAPSE", "HORIZON"
    is_stutter: Optional[bool] = None  # True if authority_epochs_after <= 1
```

### 3.5 Extended Lapse Event (`LapseEventV080`)

```python
@dataclass
class LapseEventV080:
    """Extended lapse event for v0.8 with cause classification."""
    cycle: int
    epoch: int
    start_cycle: int
    start_epoch: int
    end_cycle: Optional[int] = None
    end_epoch: Optional[int] = None
    duration_cycles: int = 0
    duration_epochs: int = 0
    cause: LapseCause = LapseCause.SEMANTIC
    amnesty_events_during: int = 0
    recovered: bool = False
    ineligible_policies: List[str] = field(default_factory=list)
```

---

## 4. Core Mechanisms

### 4.1 CTA Amnesty Application

**Trigger Condition:**
```python
if lapse_epoch_count % AMNESTY_INTERVAL == 0 and lapse_epoch_count > 0:
    apply_amnesty()
```

**Application Rule:**
```python
def _apply_cta_amnesty(self) -> None:
    """
    Apply Constitutional Temporal Amnesty.

    Per spec §6.5:
    - Only runs during NULL_AUTHORITY
    - Decrements all policy streaks by AMNESTY_DECAY
    - No streak increments, no resets, no agent action
    """
    if not self._in_null_authority:
        return  # CTA only runs during lapse

    if not self._config.cta_enabled:
        return  # CTA disabled for comparison runs

    # Compute aggregate mass before
    mass_before = self._compute_aggregate_streak_mass()

    # Apply decay to all policies
    policies_affected = []
    streak_deltas = {}
    for policy_id in list(self._semantic_fail_streak.keys()):
        old_streak = self._semantic_fail_streak[policy_id]
        if old_streak > 0:
            new_streak = max(0, old_streak - self._config.amnesty_decay)
            delta = old_streak - new_streak
            if delta > 0:
                self._semantic_fail_streak[policy_id] = new_streak
                policies_affected.append(policy_id)
                streak_deltas[policy_id] = delta

    # Compute aggregate mass after
    mass_after = self._compute_aggregate_streak_mass()

    # Record amnesty event
    event = AmnestyEvent(...)
    self._amnesty_events.append(event)
```

### 4.2 Lapse Entry with Cause Classification

```python
def _enter_null_authority_v080(
    self,
    ineligible_policies: List[str],
    cause: LapseCause,
) -> None:
    """Enter NULL_AUTHORITY state with v0.8 cause classification."""
    # Finalize previous recovery's authority span if any
    if self._last_recovery_event is not None:
        cycles_since_recovery = self._cycle - self._last_recovery_event.cycle
        authority_epochs = cycles_since_recovery // self._config.renewal_check_interval
        self._last_recovery_event.authority_epochs_after = authority_epochs
        self._last_recovery_event.authority_end_reason = "LAPSE"
        self._last_recovery_event.is_stutter = authority_epochs <= 1
        self._last_recovery_event = None

    self._in_null_authority = True
    self._null_authority_start_cycle = self._cycle
    self._null_authority_start_epoch = self._epoch_index
    self._lapse_epoch_count = 0
    self._amnesty_events_this_lapse = 0

    # Create v0.80 lapse event
    self._current_lapse_v080 = LapseEventV080(
        cycle=self._cycle,
        epoch=self._epoch_index,
        start_cycle=self._cycle,
        start_epoch=self._epoch_index,
        cause=cause,
        ineligible_policies=ineligible_policies,
    )
```

### 4.3 Recovery from NULL_AUTHORITY

```python
def _exit_null_authority_v080(self, recovered_policy_id: str) -> None:
    """Exit NULL_AUTHORITY via successful succession."""
    # Finalize lapse event
    if self._current_lapse_v080:
        self._current_lapse_v080.end_cycle = self._cycle
        self._current_lapse_v080.end_epoch = self._epoch_index
        self._current_lapse_v080.duration_cycles = (
            self._cycle - self._current_lapse_v080.start_cycle
        )
        self._current_lapse_v080.duration_epochs = (
            self._epoch_index - self._current_lapse_v080.start_epoch
        )
        self._current_lapse_v080.amnesty_events_during = self._amnesty_events_this_lapse
        self._current_lapse_v080.recovered = True
        self._lapse_events_v080.append(self._current_lapse_v080)

    # Record recovery event
    lapse_duration = self._cycle - self._null_authority_start_cycle
    lapse_epochs = self._epoch_index - self._null_authority_start_epoch
    recovery = RecoveryEvent(
        cycle=self._cycle,
        epoch=self._epoch_index,
        lapse_duration_cycles=lapse_duration,
        lapse_duration_epochs=lapse_epochs,
        amnesty_events_during_lapse=self._amnesty_events_this_lapse,
        lapse_cause=self._current_lapse_v080.cause if self._current_lapse_v080 else LapseCause.SEMANTIC,
        recovered_policy_id=recovered_policy_id,
        streak_at_recovery=self._semantic_fail_streak.get(recovered_policy_id, 0),
    )
    self._recovery_events.append(recovery)
    self._last_recovery_event = recovery  # Track for authority span completion

    self._in_null_authority = False
```

### 4.4 Epoch Processing During Lapse

```python
def _process_epoch_end_v080(self) -> None:
    """v0.8 epoch end processing."""
    if self._in_null_authority:
        # Increment lapse epoch counter
        self._lapse_epoch_count += 1

        # Check for CTA trigger
        if self._lapse_epoch_count % self._config.amnesty_interval == 0:
            self._apply_cta_amnesty()

        # No streak updates during lapse (except CTA)
    else:
        # Normal streak update
        self._update_streak_at_epoch_end()
```

---

## 5. Recovery Dynamics

### 5.1 Recovery Conditions

Recovery from NULL_AUTHORITY requires:
1. Scheduled succession boundary reached
2. Candidate pool regenerated
3. At least one candidate with `streak < K` (eligible)

Recovery can occur via:
- **Fresh candidates**: New candidates with `streak = 0` enter the pool
- **CTA decay**: Existing candidates have their streak decremented below K

### 5.2 Authority Span Tracking

To detect stutter recoveries (authority lasting ≤1 epoch), the harness tracks:

```python
# On recovery:
self._last_recovery_event = recovery_event

# On next lapse entry:
cycles_since_recovery = self._cycle - self._last_recovery_event.cycle
authority_epochs = cycles_since_recovery // self._config.renewal_check_interval
self._last_recovery_event.authority_epochs_after = authority_epochs
self._last_recovery_event.is_stutter = authority_epochs <= 1

# At horizon (if still in authority):
# Same calculation, authority_end_reason = "HORIZON"
```

### 5.3 Recovery Yield Metric

**Recovery Yield (RY)** measures the ratio of authority gained to lapse invested:

```
RY = authority_epochs_after / lapse_duration_epochs
```

- RY > 1: More authority gained than lapse invested
- RY < 1: Less authority gained than lapse invested
- RY = 0: Immediate stutter (or pending telemetry)

---

## 6. Lapse Flow (v0.8)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SUCCESSION FAILS (C_ELIG = ∅)                    │
│                                                                     │
│  Classify cause:                                                    │
│  - SEMANTIC: Candidates exist but all ineligible (streak >= K)      │
│  - STRUCTURAL: No candidates exist                                  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ENTER NULL_AUTHORITY                             │
│                                                                     │
│  - Clear active authority                                           │
│  - Record lapse start                                               │
│  - Reset lapse_epoch_count = 0                                      │
│  - Finalize any pending recovery's authority span                   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LAPSE EPOCH LOOP                                 │
│                                                                     │
│  For each epoch during lapse:                                       │
│  1. Increment lapse_epoch_count                                     │
│  2. If lapse_epoch_count % AMNESTY_INTERVAL == 0:                   │
│     - Apply CTA: decrement all streaks by AMNESTY_DECAY             │
│  3. If at succession boundary:                                      │
│     - Regenerate candidate pool                                     │
│     - Filter by eligibility                                         │
│     - If C_ELIG ≠ ∅: EXIT to recovery                               │
│  4. Continue to next epoch                                          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
    ┌─────────────────────────┐ ┌─────────────────────────────────────┐
    │   RECOVERY              │ │   HORIZON EXHAUSTED                 │
    │                         │ │                                     │
    │   - Record recovery     │ │   - Mark lapse as unrecovered       │
    │   - Exit NULL_AUTHORITY │ │   - Finalize pending spans          │
    │   - Track authority     │ │   - End run                         │
    │     span start          │ │                                     │
    └─────────────────────────┘ └─────────────────────────────────────┘
```

---

## 7. Result Metrics

### 7.1 CTA Metrics (New in v0.8)

| Metric | Description |
|--------|-------------|
| `amnesty_event_count` | Total CTA applications |
| `total_streak_decay_applied` | Sum of all streak decrements |
| `recovery_count` | Recoveries from NULL_AUTHORITY |
| `stutter_recovery_count` | Recoveries with authority ≤ 1 epoch |
| `authority_uptime_cycles` | Cycles under active authority |
| `authority_uptime_fraction` | authority_uptime / total_cycles |
| `lapse_fraction` | null_authority_cycles / total_cycles |
| `semantic_lapse_count` | Lapses caused by streak exhaustion |
| `structural_lapse_count` | Lapses caused by empty candidate pool |
| `recovery_yield` | authority_epochs / lapse_epochs |
| `hollow_recovery_count` | Recoveries followed by immediate relapse |

### 7.2 Episode-Level Metrics

| Metric | Description |
|--------|-------------|
| `lapse_duration_epochs` (L) | Duration of lapse |
| `amnesty_events_during` | Amnesty applications in this lapse |
| `authority_epochs_after` (A) | Post-recovery authority duration |
| `is_stutter` | A ≤ 1 |
| `recovery_yield` | A / L |

---

## 8. Experimental Geometry

### 8.1 Run A Configuration

| Parameter | Value |
|-----------|-------|
| K | 3 |
| max_successive_renewals | 3 |
| AMNESTY_INTERVAL | 10 epochs |
| AMNESTY_DECAY | 1 |
| pool_policy | V060_DEFAULT |
| horizon | 5,000 cycles |
| seeds | 50, 51, 52, 53, 54 |

### 8.2 Regime Classification

| Regime | Definition |
|--------|------------|
| NO_LAPSE | No lapse occurred during run |
| RECOVERING | Lapse(s) occurred, all recovered |
| PERMANENT_LAPSE | Lapse occurred, never recovered before horizon |
| STUTTER_DOMINANT | >50% of recoveries are stutter (A ≤ 1) |

---

## 9. Run A Key Findings

### 9.1 Summary Results

| Metric | Value |
|--------|-------|
| Total Lapses | 13 |
| Total Recoveries | 13 |
| Recovery Rate | 100% |
| Stutter Recoveries | 0 (0%) |
| Non-Stutter Recoveries | 13 (100%) |
| Amnesty Events | 8 |
| NULL_AUTHORITY Cycles | 4,637 (18.5%) |
| Recoveries Without Amnesty | 9 (69%) |
| Min Authority Epochs | 4 |
| Max Authority Epochs | 15 |
| Median Authority Epochs | 8 |

### 9.2 Episode Pattern Analysis

**Bimodal lapse distribution observed:**

1. **Short lapses (L = 1-2 epochs):** 9/13 episodes (69%)
   - No amnesty events fire (L < AMNESTY_INTERVAL = 10)
   - Recovery via fresh candidates with streak = 0

2. **Long lapses (L = 20 epochs):** 4/13 episodes (31%)
   - 2 amnesty events per episode
   - Recovery via CTA decay and/or fresh candidates

### 9.3 Regime Distribution

| Regime | Seeds | Count |
|--------|-------|-------|
| NO_LAPSE | 51 | 1 |
| RECOVERING | 50, 52, 53, 54 | 4 |
| PERMANENT_LAPSE | — | 0 |
| STUTTER_DOMINANT | — | 0 |

---

## 10. Invariant Verification

### 10.1 Confirmed Invariants

| Invariant | Verification |
|-----------|--------------|
| CTA only during NULL_AUTHORITY | ✓ Guard in `_apply_cta_amnesty()` |
| No streak updates during lapse except CTA | ✓ Guard in `_update_streak_at_epoch_end()` |
| Streak keyed to stable policy_id | ✓ Format `{category}:{enum_name}` |
| Eligibility filtering at succession only | ✓ No mid-epoch eligibility checks |
| Renewal independent of semantics | ✓ Renewal logic unchanged from v0.7 |
| No verifiers during lapse | ✓ Commitment evaluation skipped |
| No agent action during lapse | ✓ No action dispatch |
| TTL clocks advance during lapse | ✓ Cycle counter continues |
| Succession at scheduled boundaries only | ✓ Per inherited schedule |
| Candidate pool regenerated at each attempt | ✓ Fresh pool per succession |

### 10.2 Telemetry Improvements

Authority span tracking was enhanced mid-implementation to use cycle-based calculation:

```python
# Original (broken): Used per-successor epoch index
authority_epochs = _epoch_index - _last_recovery_epoch  # WRONG: resets per successor

# Fixed: Use cycle difference
cycles_since_recovery = self._cycle - recovery.cycle
authority_epochs = cycles_since_recovery // self._config.renewal_check_interval
```

---

## 11. Files Modified/Created

### Harness (`harness.py`)
- Added `LapseCause` enum
- Added `AmnestyEvent` dataclass
- Added `RecoveryEvent` dataclass with authority span tracking
- Added `LapseEventV080` dataclass
- Added `ALSConfigV080` dataclass
- Added `ALSRunResultV080` dataclass
- Added `ALSHarnessV080` class with full CTA mechanics

### Scripts
- `run_a_v080.py` — CTA baseline run

### Reports
- `run_a_v080_report.md` — LOCKED
- `IMPLEMENTATION_REPORT_V08.md` — This document

---

## 12. Conclusion

AKI v0.8 successfully implements Constitutional Temporal Amnesty as specified. The mechanism:

1. **Functions as designed**: CTA executes deterministically at 10-epoch intervals during NULL_AUTHORITY
2. **Enables recovery**: 100% recovery rate observed (13/13 lapses recovered)
3. **Produces durable authority**: 0% stutter rate (all recoveries achieve 4+ epochs of authority)
4. **Is not the sole recovery mechanism**: 69% of recoveries occur before any amnesty fires, suggesting pool regeneration (fresh candidates) is primary in this geometry
5. **Preserves kernel invariants**: No semantic enforcement, no optimization, no internal inspection, no agent action during lapse

The implementation is complete and ready for Run B (AMNESTY_INTERVAL=5) to probe interval sensitivity.

---

**Report Generated:** January 5, 2026
**Implementation Scripts:** `harness.py`, `run_a_v080.py`
**Specification:** `spec_v0.8.md`
