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

**Full report:** [run_f_v052_report.md](run_f_v052_report.md)

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

## 11. Run G: Competitive Expressivity Horizon

### Overview

Run G addressed Run F's limitation by **reintroducing competition under scarcity**:

> "When multiple structurally compliant successors compete for authority under expressivity-dependent rent, where does renewal stability collapse—and by what mode?"

**Full report:** [run_g_v052_report.md](run_g_v052_report.md)

### Executive Summary

| Sub-Run | Status | Verdict |
|---------|--------|---------|
| G1 | ✅ Complete | No ceiling found — all seeds reached E4 |
| G2 | ✅ Complete | No hollow tenures — CBD stress did not induce collapse |

### Key Configuration

- **H:** 30,000 cycles
- **max_successive_renewals:** 15 (forced succession guardrail)
- **Generator:** Mixed (control + attack + CBD) with TierFilterGenerator as post-filter
- **Seeds:** 40, 41, 42, 43, 44

### G1 Results (Ascension with Competition)

| Seed | S* | Max Tier | Ceiling | Bankruptcies | Renewal Rate |
|------|-----|----------|---------|--------------|--------------|
| 40 | 20 | E4 | None | 0 | 0.95 |
| 41 | 20 | E4 | None | 0 | 0.95 |
| 42 | 20 | E4 | None | 0 | 0.95 |
| 43 | 20 | E4 | None | 0 | 0.95 |
| 44 | 20 | E4 | None | 0 | 0.95 |

### G2 Results (CBD Stress at E3)

| Seed | S* | Hollow Tenures | Hollow Rate | Bankruptcies |
|------|-----|----------------|-------------|--------------|
| 40 | 10 | 0 | 0.0% | 0 |
| 41 | 10 | 0 | 0.0% | 0 |
| 42 | 10 | 0 | 0.0% | 0 |
| 43 | 10 | 0 | 0.0% | 0 |
| 44 | 10 | 0 | 0.0% | 0 |

### Key Findings

**What Run G establishes:**

1. **Competition was exercised** — TierFilterGenerator filtered 95-97% of proposals, confirming real adversarial competition.

2. **No collapse modes appeared** — Zero bankruptcies, zero revocations, zero hollow tenures across all runs.

3. **Stable renewal at all tiers** — Renewal rate remained ~0.95 from E0 through E4.

**What Run G does NOT establish:**

- That no competence horizon exists at higher rent scales (e.g., E4=80%)
- That longer horizons (H=100,000+) would remain stable
- That semantic workloads would exhibit similar stability

### Interpretation

The v0.5.2 rent schedule with `max_successive_renewals=15` is **more robust than anticipated**. This is a meaningful negative result — no collapse was observed despite active competition. Follow-up runs should test higher rent pressure or remove the succession guardrail.

### Code Changes for Run G

1. Added `CBD_E3` to `AttackSuccessorType` enum (E3-constrained CBD variant)
2. Added `V052_RUNG_G2_ATTACK_WEIGHTS` with CBD_E3 at 30%
3. Added delegation methods to `TierFilterGenerator` for harness compatibility

---

## 12. Run H: Boundary-Finding Escalation

Run H tested single-axis escalation to find v0.5.2 boundaries:

| Sub-Run | Parameter | Result |
|---------|-----------|--------|
| H1 | E3 rent = 60 | 93.8% renewal rate, stable |
| H2 | H = 100,000 | SPAM_DEGENERACY (test inconclusive) |
| H3 | renewal_cost = 10 | **0% renewal rate, 100% failure** |

### Key Finding: Renewal Cost Cliff

H3 discovered a **hard boundary**: renewal cost of 10 steps at E3 causes complete system failure.

**Budget Analysis:**
- effective_steps = 60
- steps_used (avg) = 54
- remaining_budget = 6
- renewal_cost = 10
- **6 < 10 → all renewals fail**

**Design Constraint Identified:**
```
renewal_cost < effective_steps × (1 - typical_step_usage)
```

For 90% step usage at E3: `renewal_cost ≤ 6 steps`

### Rent Elasticity Confirmed

H1 showed rent elasticity is high—increasing E3 rent by 50% (40 → 60) caused only 1.2% renewal rate degradation. The system has significant headroom before rent-induced collapse.

See [run_h_v052_report.md](run_h_v052_report.md) for full analysis.

---

## 13. Run H3-R Series: Renewal Cost Phase Boundary

Following Run H3's discovery of a renewal cost cliff, three follow-up experiments mapped the phase boundary precisely.

### H3-RZ: Zero-Slack Renewal Impossibility

**Configuration:** `steps_cap_epoch = 100`, `effective_steps = 60` (E3)

| Renewal Cost | Failure Rate | Verdict |
|--------------|--------------|---------|
| 4–9 | **100%** | All fail |

**Finding:** With zero slack (step consumption = 100% of budget), `remaining_budget = 0` at renewal time. Any positive renewal cost triggers RENEWAL_FAIL.

> **Structural insight:** Renewal is impossible in zero-slack regimes regardless of renewal_cost magnitude.

See [run_h3rz_v052_report.md](run_h3rz_v052_report.md).

### H3-RS: Slack-Dominated Renewal Plateau

**Configuration:** `steps_cap_epoch = 200`, `effective_steps = 160` (E3)

| Renewal Cost | Failure Rate | Success Rate |
|--------------|--------------|--------------|
| 4–9 | **0%** | 94% |

**Finding:** With modest slack (`remaining_budget ≈ 60`), renewal costs 4–9 are **structurally irrelevant**. The 6% non-renewal rate is due to MSRW violations, not budget exhaustion.

> **Strong negative result:** Within this configuration, renewal_cost up to 9 is strictly non-binding.

See [run_h3rs_v052_report.md](run_h3rs_v052_report.md).

### H3-RB: Renewal Boundary Search (Higher-Cost Sweep)

**Configuration:** Same as H3-RS, extended sweep

| Renewal Cost | Failure Rate | Success Rate |
|--------------|--------------|--------------|
| 10 | 0% | 94% |
| 12 | 0% | 94% |
| 15 | 0% | 94% |
| 20 | 0% | 94% |

**Finding:** The flat region extends to renewal_cost = 20. The phase boundary lies **above 20** for this configuration.

See [run_h3rb_v052_report.md](run_h3rb_v052_report.md).

### Phase Map Summary

| Configuration | Boundary |
|---------------|----------|
| Zero-slack (steps_cap=100) | renewal_cost ≥ 1 fails |
| Slack (steps_cap=200) | renewal_cost ≤ 20 safe |

**Implication:** The renewal cost boundary is a function of slack, not an absolute threshold. The system operates stably in a wide "Growth regime" with meaningful remaining budget.

---

## 14. Run I: Guardrail Removal / Institutional Debt Test

### Hypothesis

Test whether agency can fail through accumulation, even when all local constraints appear slack. The `max_successive_renewals` guardrail is disabled (set to 1,000,000) to observe long-horizon behavior without forced succession.

### Configuration

| Parameter | Value |
|-----------|-------|
| Horizon | 100,000 cycles |
| max_successive_renewals | 1,000,000 (disabled) |
| renewal_cost | 5 (non-binding per H3-R) |
| steps_cap_epoch | 200 |
| Seeds | 40, 41, 42 |

### Results

| Seed | S* | Cycles | Renewals | Tenures | Stop Reason | Degeneracy |
|------|----|--------|----------|---------|-------------|------------|
| 40 | 1 | 100,000 | 1,000 | 1 | HORIZON_EXHAUSTED | Thrash, RubberStamp |
| 41 | 1 | 100,000 | 1,000 | 1 | HORIZON_EXHAUSTED | Thrash, RubberStamp |
| 42 | 1 | 100,000 | 1,000 | 1 | HORIZON_EXHAUSTED | Thrash, RubberStamp |

### Key Findings

1. **All 3 runs reached horizon** without renewal failure, bankruptcy, or revocation. The system is operationally stable.

2. **S* = 1 across all seeds:** The very first successor was endorsed and renewed indefinitely (1000 times), never triggering succession.

3. **100% degeneracy detection:**
   - **Authority Thrash (3/3):** entropy = 0 (single mind dominates)
   - **Rubber-Stamp (3/3):** 1000 renewals per tenure (no succession)

### Interpretation

This represents **institutional calcification**: the authority structure froze in its initial configuration. While the system remained *operationally* stable (no failures), it completely failed to exercise its *renewal* capability—the very mechanism designed to enable institutional adaptation.

The `max_successive_renewals` guardrail exists precisely to prevent this degenerate mode. When disabled, the first competent incumbent can monopolize authority indefinitely, eliminating the system's capacity for institutional change.

> **Validation:** The Run I results validate the guardrail's design rationale. Forced succession ensures the succession mechanism is exercised, even when the incumbent remains locally compliant.

See [run_i_v052_report.md](run_i_v052_report.md).

---

## 15. Run J: Expressivity-Rent Boundary Identification

### Hypothesis

Find the **expressivity-rent boundary**: the E3 rent fraction at which renewal stability collapses. Prior runs used 40% E3 rent with stable renewal. This run bisects the 40-60% range to identify the transition point.

### Configuration

| Parameter | Value |
|-----------|-------|
| Horizon | 30,000 cycles |
| max_successive_renewals | 15 |
| renewal_cost | 5 |
| steps_cap_epoch | 200 |
| Seeds | 40-44 |
| E3 rent range | 40-60% (bisection) |

### Sub-Run Results

| Sub-Run | E3 Rent | Eff. Steps | Mean Renew Rate | Dominant Regime |
|---------|---------|------------|-----------------|-----------------|
| J-40 | 80 (40%) | 120 | 93.75% | METASTABLE_STASIS |
| J-45 | 90 (45%) | 110 | 93.75% | METASTABLE_STASIS |
| J-47 | 94 (47%) | 106 | 93.75% | METASTABLE_STASIS |
| J-48 | 96 (48%) | 104 | 0.00% | RENEWAL_COLLAPSE |
| J-49 | 98 (49%) | 102 | 0.00% | RENEWAL_COLLAPSE |
| J-50 | 100 (50%) | 100 | 0.00% | RENEWAL_COLLAPSE |
| J-60 | 120 (60%) | 80 | 0.00% | RENEWAL_COLLAPSE |

### Budget Arithmetic at Boundary

| Rent % | Effective Steps | Steps Used | Remaining | Renewal Cost | Outcome |
|--------|-----------------|------------|-----------|--------------|---------|
| 47% | 106 | 100 | **6** | 5 | ✓ Renew |
| 48% | 104 | 100 | **4** | 5 | ✗ Fail |

### Key Findings

1. **Sharp boundary at 48% E3 rent:** The transition from stable renewal (93.75%) to complete collapse (0%) occurs between 47% and 48% rent.

2. **Mechanism:** At 47%, remaining budget (6) ≥ renewal cost (5) → renewal succeeds. At 48%, remaining budget (4) < renewal cost (5) → renewal fails deterministically.

3. **Regime classification validated:**
   - METASTABLE_STASIS: High renewal rate but flat manifest diversity, terminated by degeneracy detector
   - RENEWAL_COLLAPSE: 0% renewal rate, all attempts fail due to budget exhaustion

### Design Constraint Refined

```
For stable renewal at E3:
  rent_fraction < 1 - (step_usage + renewal_cost) / steps_cap_epoch

With step_usage ≈ 100 and renewal_cost = 5:
  rent_fraction < 1 - 105/200 = 47.5%
```

The observed boundary (47-48%) matches this prediction exactly.

See [run_j_v052_report.md](run_j_v052_report.md).

---

## 16. Run J2: Renewal-Timing Sensitivity Test

### Hypothesis

Determine whether the 48% rent collapse boundary identified in Run J is **intrinsic** to budget arithmetic or **dependent on renewal-timing geometry**.

### Renewal Check Interval Semantics

`renewal_check_interval` is interpreted as **global-cycle modulo**:

```
if cycle % renewal_check_interval == 0:
    check_renewal()
```

- **Interval 50:** Checks at cycles 50, 100, 150, 200... (mid-epoch)
- **Interval 90:** Checks at cycles 90, 180, 270... (late-epoch, 90% through)
- **Interval 100:** Checks at cycles 100, 200, 300... (epoch-boundary aligned)

### Configuration

| Parameter | Value |
|-----------|-------|
| E3 rent | 96 (48%) — exact collapse point |
| Effective steps | 104 |
| msrw_cycles | 200 (fixed, orthogonal) |
| Seeds | 40-44 |

### Sub-Run Definitions

| Sub-Run | Interval | Timing |
|---------|----------|--------|
| J2-Early | 50 | Mid-epoch (cycle 50 of each epoch) |
| J2-Baseline | 100 | Epoch-aligned (cycle 100 = boundary) |
| J2-Late | 90 | Late-epoch (cycle 90 of each epoch) |

### Results

| Sub-Run | Interval | Mean Ren Rate | Dominant Regime | Steps@Chk | Remaining |
|---------|----------|---------------|-----------------|-----------|-----------|
| J2-Early | 50 | 93.75% | METASTABLE_STASIS | 50 | 54 |
| J2-Baseline | 100 | 0.00% | RENEWAL_COLLAPSE | 100 | 4 |
| J2-Late | 90 | 93.75% | METASTABLE_STASIS | 90 | 14 |

### Geometry Table

| Sub-Run | Steps at Check | Remaining | Renewal Cost | Outcome |
|---------|----------------|-----------|--------------|---------|
| J2-Early | 50 | **54** | 5 | ✓ Renew |
| J2-Baseline | 100 | **4** | 5 | ✗ Fail |
| J2-Late | 90 | **14** | 5 | ✓ Renew |

### Key Finding

**The collapse boundary is timing-dependent, not intrinsic.**

The 48% rent collapse observed in Run J is a **resonance artifact** between the 100-cycle epoch and the 100-cycle renewal check interval:

1. At **interval=100:** Check happens exactly when the epoch's 104 effective steps are fully consumed → remaining=4 < renewal_cost=5 → RENEWAL_COLLAPSE

2. At **interval=50:** Check happens mid-epoch → remaining=54 → renewal succeeds → METASTABLE_STASIS

3. At **interval=90:** Check happens at 90% of epoch → remaining=14 → renewal succeeds → METASTABLE_STASIS

### Implications

1. The Run J boundary (48%) is **not a fundamental economic constraint**—it's an artifact of epoch/check alignment.

2. Systems can operate at 48% rent with stable renewal simply by offsetting the renewal check interval from epoch boundaries.

3. **Robust design principle:** Avoid renewal_check_interval = epoch_size to prevent phase-lock collapse.

See [run_j2_v052_report.md](run_j2_v052_report.md).

---

## 17. Run K: Succession Geometry Sweep (Completed)

Run K isolated a single axis: **max_successive_renewals** — the number of consecutive renewals permitted before forced succession. The goal was to determine whether forced succession is *constitutive* (required for institutional health) or merely *procedural* (tunable optimization).

### Configuration (Single-Axis Isolation)

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Expressivity Class** | E3 | Fixed (prior runs established E3 stability) |
| **Rent fraction** | 40% | Well inside stable region (Run J boundary: 48%) |
| **Renewal cost** | 5 | Verified affordable at 40% rent |
| **renewal_check_interval** | 90 | Non-commensurate with epoch to avoid resonance |
| **msrw_cycles** | 200 | MSRW gates replacement, NOT renewal |
| **Horizon (H)** | 30,000 | Long enough for regime emergence |
| **Seeds** | 40–44 | 5 replications per sub-run |

### Sub-Run Definitions

| Sub-Run | max_successive_renewals | Label |
|---------|-------------------------|-------|
| K0 | ∞ (1,000,000) | Lock-In Control — no forced succession |
| K1 | 100 | Low Turnover Pressure |
| K2 | 15 | Moderate Turnover |
| K3 | 3 | High Turnover Pressure |

### Summary Table

| Sub-Run | max_successive | Tenures | Mean Residence | Renewal Rate | Entropy | Regime | Terminal Cause |
|---------|----------------|---------|----------------|--------------|---------|--------|----------------|
| K0 | ∞ | 1.0 | 29,999 | 100% | 0.000 | LOCK_IN | HORIZON_EXHAUSTED |
| K1 | 100 | 4.0 | 7,499 | 99.10% | 0.250 | CONSTITUTIONAL_STABILITY | HORIZON_EXHAUSTED |
| K2 | 15 | 10.0 | 1,295 | 93.75% | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY |
| K3 | 3 | 10.0 | 323 | 75.00% | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY |

### Regime Definitions

| Regime | Criteria |
|--------|----------|
| **LOCK_IN** | tenure_count ≤ 2, entropy → 0. Authority frozen in initial configuration. |
| **CONSTITUTIONAL_STABILITY** | Multiple tenures, renewal_rate ≥ 75%, horizon reached, no degeneracy. |
| **STASIS_UNDER_TURNOVER** | SPAM_DEGENERACY termination. Behavioral homogeneity (control actions ≥80%), not thrash. |

### Phase Diagram

```
max_successive_renewals → Regime
─────────────────────────────────
        ∞ → LOCK_IN
      100 → CONSTITUTIONAL_STABILITY
       15 → STASIS_UNDER_TURNOVER
        3 → STASIS_UNDER_TURNOVER
```

**Observed Stable Point:** `max_successive_renewals = 100` achieved constitutional stability. No band width has been established — only a single stable point was tested.

### Key Finding

**Forced succession is necessary to prevent institutional lock-in, but does not guarantee institutional diversity.**

| Condition | Outcome |
|-----------|---------|
| No forced succession (K0) | Authority locks into single configuration permanently |
| Moderate forcing (K1=100) | Constitutional stability — diverse succession with high renewal |
| High forcing (K2=15, K3=3) | Stasis under turnover — behavioral homogeneity, not thrash |

**No thrash regime was observed in Run K.** K2/K3 degeneracy arises from behavioral homogeneity (control action dominance), not from instability or rapid authority changes.

### MSRW Semantic Clarification

A critical implementation detail: **MSRW gates successor replacement, not renewal**.

- `_check_renewal_with_rent()` checks budget feasibility, not MSRW
- `Lease.renew()` checks `max_successive_renewals`, not MSRW
- Succession triggers when renewal exhausted OR MSRW expires — whichever comes first

### Implications

1. **Lock-in is the default:** Without any turnover constraint, the system settles into a single authority configuration and never recovers.

2. **A single stable point was observed:** At the tested parameters, only `max_successive_renewals=100` produced stable succession. No band width has been established.

3. **Stasis under turnover is distinct from thrash:** K2/K3 exhibit behavioral homogeneity (control action dominance), not instability or rapid authority changes. Renewal rates remained high (75–94%).

4. **Future work:** The transition between CONSTITUTIONAL_STABILITY and STASIS_UNDER_TURNOVER likely falls somewhere in the range 15–100. Additional sub-runs could map this boundary.

See [run_k_v052_report.md](run_k_v052_report.md).

---

## 18. Future Work

### Planned Features

1. **Fixed E-Class mode:** Force all successors to specific E-Class (config stub exists)
2. **Dynamic rent adjustment:** Rent fractions that change based on population
3. **E-Class graduation:** Successors earning promotion/demotion

### Open Questions

1. Should renewal preserve E-Class or allow renegotiation?
2. How should rent interact with cooperative succession chains?
3. What observability is needed for rent optimization strategies?

### Recommended Follow-Up Runs

Based on Run G/H/H3-R/I/J/J2/K results:

1. ~~**Run H3-bisect:** Test renewal_cost = 5, 7, 8 to find exact transition point~~ → Superseded by H3-RZ/RS/RB series
2. **Run H3-RB′:** Extend sweep to {30, 40, 50, 60} to find actual cliff above 20
3. ~~**Run I:** Remove max_successive_renewals guardrail (institutional debt accumulation)~~ → **Completed.** Confirmed Rubber-Stamp degeneracy.
4. **Run I′:** Test with multiple succession triggers (e.g., force expiration events)
5. ~~**Run J:** Expressivity-rent boundary identification~~ → **Completed.** Sharp boundary at 48% E3 rent.
6. ~~**Run J2:** Renewal-timing sensitivity test~~ → **Completed.** Boundary is timing-dependent (epoch/check resonance).
7. ~~**Run K:** Succession geometry sweep (max_successive_renewals)~~ → **Completed.** Forced succession is necessary but not sufficient for diversity.
8. **Run K′:** Map CONSTITUTIONAL_STABILITY → STASIS_UNDER_TURNOVER transition (test max_successive_renewals = 30, 50, 75)

---

## Appendix: File Changes

### New Files

- `src/toy_aki/als/expressivity.py` - E-Class and rent infrastructure
- `tests/test_v052.py` - 52-test v0.5.2 test suite
- `scripts/run_h_v052.py` - Run H boundary-finding experiments
- `scripts/run_j_v052.py` - Run J expressivity-rent boundary identification
- `scripts/run_j2_v052.py` - Run J2 renewal-timing sensitivity test

### Modified Files

- `src/toy_aki/als/generator.py` - Added CBD, V052_ATTACK_WEIGHTS, TierFilterGenerator
- `src/toy_aki/als/harness.py` - Added ALSHarnessV052, ALSConfigV052, rent charging, renewal cost support, RenewalEvent budget telemetry
- All v0.4.x harness code paths
- Default generator weights (ENDORSEMENT_PRESSURE=0.15)
- S* counting semantics
- Lease lifecycle events
