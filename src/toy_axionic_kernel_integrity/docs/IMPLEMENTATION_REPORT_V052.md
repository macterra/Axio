# AKI v0.5.2 Implementation Report

## Version: ALS-E (Authority Leases and Expressivity-Bounded Succession)

**Implementation Date:** 2026-01-03

## 1. Overview

AKI v0.5.2 extends the Authority Lease System (ALS) with **expressivity bounding** —
a mechanism that charges successors "rent" proportional to their capability expressivity.
Higher expressivity costs more, reducing the effective step budget and creating
selection pressure toward minimal-capability successors.

### Key Concepts

- **Expressivity Classes (E0-E4):** Hierarchical capability levels
- **Rent:** Steps deducted from budget at epoch start, based on E-Class
- **Bankruptcy:** Epoch termination when rent exhausts budget (distinct from revocation)
- **CBD Successor:** "Compliant-But-Dangerous" pattern that operates near caps

---

## 2. Expressivity Classes

Five expressivity classes define capability levels:

| E-Class | Name | Capability Groups | Description |
|---------|------|-------------------|-------------|
| **E0** | Heartbeat | WAIT, PING, HEARTBEAT | Minimal presence-only operations |
| **E1** | Logging | E0 + LOG, REPORT, DEBUG | Read-only observation |
| **E2** | State Mutation | E1 + SET, GET, DELETE, UPDATE, STORE, LOAD | Local state modification |
| **E3** | Fanout/Composition | E2 + BATCH, COMPOSE, INVOKE, PARALLEL, SEQUENCE | Orchestration capability |
| **E4** | Full API Surface | E3 + MOVE_*, HARVEST, SPEND, BUILD, DESTROY | All capabilities |

### E-Class Assignment Rules

1. **Derived from action types:** E-Class is computed from the union of action types in the successor's manifest
2. **Maximum principle:** If any action requires E3, the entire successor is E3+
3. **Conservative default:** Unknown action types map to E4 (FULL_API_SURFACE)
4. **Self-report ignored:** Successors cannot claim lower E-Class than their actions require

---

## 3. Rent Schedule

Rent is computed as a fraction of the epoch step cap:

```
rent(E) = ceil(fraction(E) × steps_cap_epoch)
```

### Default Fractions

| E-Class | Fraction | Rent (S=10000) | Effective Steps |
|---------|----------|----------------|-----------------|
| E0 | fixed | 1 | steps_cap_epoch - 1 |
| E1 | 10% | 1,000 | 9,000 |
| E2 | 25% | 2,500 | 7,500 |
| E3 | 40% | 4,000 | 6,000 |
| E4 | 60% | 6,000 | 4,000 |

**Note:** E0 rent is hard-coded to exactly 1 step, not derived from a fraction.
This makes E0 the **baseline metabolic minimum**, invariant across runs.

### Monotonicity Enforcement

The `RentSchedule` class enforces strict monotonicity:
- E0 < E1 < E2 < E3 < E4
- Violations raise `RentScheduleViolation` at construction time
- Rent can never exceed `steps_cap_epoch - 1` (guarantees at least 1 effective step)

---

## 4. Bankruptcy vs. Revocation

A key semantic distinction in v0.5.2:

| Aspect | Bankruptcy | Revocation |
|--------|------------|------------|
| **Cause** | Rent exhausts budget | Manifest violation detected |
| **S* Impact** | No increment (no endorsement) | No increment (violation) |
| **Lease Outcome** | Expired (resource exhaustion) | Revoked (trust breach) |
| **Next Action** | Succession opportunity | Succession opportunity |

### Event Recording

```python
@dataclass
class BankruptcyEvent:
    cycle: int
    mind_id: str
    e_class: str
    rent_charged: int
    steps_remaining: int
    epoch_index: int
```

---

## 5. CBD Successor Pattern

The **Compliant-But-Dangerous (CBD)** successor is a new attack pattern for v0.5.2:

### Characteristics

- **Fully compliant:** Never exceeds manifest declarations
- **Near-cap operation:** Uses resources close to (but within) limits
- **Higher expressivity:** Requests STATE_MUTATION capabilities when enabled
- **Expensive:** Triggers higher rent due to E2+ classification

### Generator Weight

CBD is included in `V052_ATTACK_WEIGHTS` at 10%:

```python
V052_ATTACK_WEIGHTS = {
    "RubberStampSuccessor": 0.18,
    "LeaseGamingSuccessor": 0.18,
    "SemanticCreepSuccessor": 0.18,
    "HiddenDelegationSuccessor": 0.13,
    "EndorsementPressureSuccessor": 0.13,
    "SentinelEvasionSuccessor": 0.05,
    "BoundaryHuggerSuccessor": 0.05,
    "CBDSuccessor": 0.10,  # New in v0.5.2
}
```

### Non-Regression

CBD is **not** included in v0.4.x default weights, preserving backward compatibility.

---

## 6. Renewal Under Rent Pressure

### Binding Decision

Per spec discussion: "Renewal under rent consumes successor's budget via inherited E-Class."

### Implementation

1. Renewed successor inherits predecessor's E-Class
2. Rent is charged at inherited E-Class rate
3. Higher E-Class predecessors face reduced renewal capacity
4. Bankruptcy during renewal epoch is still possible

### Telemetry

`EpochRentRecord` tracks per-epoch metrics:
- `e_class`: Assigned E-Class for the epoch
- `rent_charged`: Rent deducted at epoch start
- `effective_steps`: Remaining budget after rent
- `steps_used`: Actual steps consumed
- `actions_used`: Actions taken during epoch

---

## 7. Harness API

### ALSConfigV052

```python
@dataclass
class ALSConfigV052:
    # Base parameters (inherited from ALSConfig)
    max_cycles: int = 10_000
    renewal_check_interval: int = 50
    steps_cap_epoch: int = 10_000
    actions_cap_epoch: int = 1_000

    # Expressivity parameters (new in v0.5.2)
    expressivity_mode: str = "random"  # or "fixed" (not yet implemented)
    fixed_e_class: Optional[str] = None
    reject_immediate_bankruptcy: bool = False  # Immediate bankruptcy is valid data

    # Generator config (defaults to V052_ATTACK_WEIGHTS)
    generator_config: Optional[GeneratorConfig] = None
```

**Note on `reject_immediate_bankruptcy`:** Default is `False` because immediate
bankruptcy (when `rent >= steps_cap_epoch`) is valid experimental data, not a
configuration error. Only set to `True` for calibration runs that explicitly
forbid immediate bankruptcy.

### ALSHarnessV052

```python
harness = ALSHarnessV052(seed=42, config=config)
result = harness.run()

# New properties
harness.current_e_class  # Current successor's E-Class
harness.current_rent  # Current epoch's rent
harness.current_effective_steps  # Budget after rent

# Rent schedule inspection
schedule = harness.get_rent_schedule()
# Returns: {'steps_cap_epoch': 10000, 'rents': {...}, 'effective_steps': {...}}
```

### ALSRunResultV052

```python
@dataclass
class ALSRunResultV052:
    # Base metrics
    s_star: int
    total_successions: int
    total_renewals: int
    total_expirations: int
    total_revocations: int

    # Expressivity metrics (new)
    total_bankruptcies: int
    total_rent_charged: int
    e_class_distribution: Dict[str, int]
    renewal_rate_by_e_class: Dict[str, float]
    residence_by_e_class: Dict[str, float]
    epoch_rent_records: List[EpochRentRecord]
    bankruptcy_events: List[BankruptcyEvent]
```

---

## 8. Test Coverage

### Test Sections (52 tests total)

| Section | Tests | Description |
|---------|-------|-------------|
| §1 Rent Accounting | 8 | RentSchedule construction, monotonicity, fractions |
| §2 Bankruptcy Semantics | 4 | Bankruptcy vs revocation, S* non-increment |
| §3 E-Class Assignment | 10 | Capability group mapping, validation |
| §4 CBD Successor | 5 | CBD behavior, compliance, classification |
| §5 Renewal Under Rent | 4 | Rent inheritance, budget consumption |
| §6 Non-Regression | 5 | v0.4.x unchanged, weight isolation |
| §7 run_als_experiment | 3 | Experiment interface for v0.5.2 |
| §8 Edge Cases | 6 | Small caps, reproducibility |
| §9 Integration | 4 | Full runs, telemetry completeness |
| §10 Stress | 3 | High E-Class, extended runs |

### Key Assertions

1. **Rent monotonicity:** E0 < E1 < E2 < E3 < E4 enforced
2. **Bankruptcy semantics:** Uses LEASE_EXPIRED, not LEASE_REVOKED
3. **E-Class derivation:** From action types, not self-report
4. **CBD classification:** Correctly assigned E2 when using STATE_MUTATION
5. **Non-regression:** All 466 v0.4.x tests pass unchanged

---

## 9. Migration Notes

### From v0.4.3 to v0.5.2

1. **Import path:** `from toy_aki.als.harness import ALSHarnessV052, ALSConfigV052`
2. **Generator weights:** v0.5.2 uses `V052_ATTACK_WEIGHTS` by default
3. **New result fields:** Handle `total_bankruptcies`, `e_class_distribution`, etc.
4. **Rent awareness:** Successors effectively have less budget at higher E-Classes

### Backward Compatibility

- v0.4.2 and v0.4.3 harnesses unchanged
- Default generator weights preserved for v0.4.x
- No breaking changes to existing v0.4.x code

---

## 10. Run F: Competence Horizon Experiment

### Overview

Run F investigated the **competence horizon** question:

> "As lease-granted expressivity increases and rent reduces effective step budget, where does renewal stability collapse?"

**Full report:** [run_f_v052_report.md](../reports/run_f_v052_report.md)

### Executive Summary

| Sub-Run | Status | Verdict |
|---------|--------|---------|
| F0 | ✅ Complete | Mechanism validation success |
| F1 | ⚠️ Valid but non-probative | Stress condition not engaged |
| F2 | ❌ Not executed as designed | Generator short-circuit |

### Key Findings

**What Run F conclusively establishes:**

1. **Rent thermodynamics works as specified** — Rent scales monotonically with E-Class, effective step budgets match the schedule, no hidden subsidies exist.

2. **Renewal plumbing is robust under rent pressure** — Even at E4 (40 effective steps), renewal remains feasible with no false-positive revocations.

3. **Well-behaved successors can operate stably at E4** — This is an existence proof bounding lower competence limits.

**What Run F does NOT establish:**

- That the competence horizon is "beyond E4" in any general sense
- That ALS-E resists hollow succession under stress
- That CBD successors fail to induce collapse at E3

### Critical Limitation

The TieredGenerator used in Run F bypassed the attack/control distribution, producing only control-optimal successors at target tiers. This eliminated budget competition and adversarial consumption. Competence horizon is defined by *competition under scarcity* — Run F removed competition, so no horizon could appear.

### Rent Schedule Verification

| E-Class | Rent (R) | Effective Steps (S - R) | Utilization |
|---------|----------|------------------------|-------------|
| E0      | 1        | 99                     | 99%         |
| E1      | 10       | 90                     | 90%         |
| E2      | 25       | 75                     | 75%         |
| E3      | 40       | 60                     | 60%         |
| E4      | 60       | 40                     | 40%         |

### Required Next Steps: Run F′

Run F is a **clean preparatory result**, not a horizon answer. The next run must reintroduce **competition under scarcity** by:

1. Using the normal mixed generator (control + attack + CBD)
2. Applying TierFilterGenerator as a **post-generation filter** (not bypass)
3. Preserving expressivity control while maintaining adversarial competition

---

## 11. Future Work

### Planned Features

1. **Fixed E-Class mode:** Force all successors to specific E-Class (config stub exists)
2. **Dynamic rent adjustment:** Rent fractions that change based on population
3. **E-Class graduation:** Successors earning promotion/demotion

### Open Questions

1. Should renewal preserve E-Class or allow renegotiation?
2. How should rent interact with cooperative succession chains?
3. What observability is needed for rent optimization strategies?

---

## Appendix: File Changes

### New Files

- `src/toy_aki/als/expressivity.py` - E-Class and rent infrastructure
- `tests/test_v052.py` - 52-test v0.5.2 test suite

### Modified Files

- `src/toy_aki/als/generator.py` - Added CBD, V052_ATTACK_WEIGHTS
- `src/toy_aki/als/harness.py` - Added ALSHarnessV052, ALSConfigV052, rent charging
- `src/toy_aki/als/successors.py` - Added CBDSuccessor class

### Unchanged (Non-Regression)

- All v0.4.x harness code paths
- Default generator weights (ENDORSEMENT_PRESSURE=0.15)
- S* counting semantics
- Lease lifecycle events
