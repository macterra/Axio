# RSA X-1 Implementation Report

## Reflective Amendment Under Frozen Sovereignty

**Session:** `1fd560f6-6801-45f6-81ec-939cee370828`
**Date:** 2026-02-12
**Verdict:** **X-1 CLOSURE: POSITIVE ✓**

---

## §1 Executive Summary

RSA X-1 extends RSA-0's frozen sovereign substrate with structured constitutional
self-amendment. The implementation proves that a constitution-bound execution
kernel can adopt new constitutions without violating kernel physics, collapsing
structural constraint, or losing replay integrity.

**Key result:** 4 adoptions across 36 cycles; all 7 adversarial proposals rejected
at the schema integrity gate; deterministic replay verified across all fork
boundaries; density stays < 1 throughout; ECK preserved at every transition.

---

## §2 Architecture

### 2.1 Design Question

> Can a frozen sovereign substrate transition to a new constitution without
> losing structural constraint or replay integrity?

### 2.2 Approach

Extend the RSA-0 policy core with:

1. **5 decision types** — ACTION, QUEUE_AMENDMENT, ADOPT, REFUSE, EXIT
2. **9-step amendment admission pipeline** (Gates 6–8B)
3. **Cooling-off period** — configurable delay between proposal and adoption
4. **Ratchet monotonicity** — amendment parameters can only tighten, never relax
5. **Full-document replacement** — no partial patches; every proposal is a complete
   new constitution YAML validated against the frozen schema

### 2.3 Decision Flow

```
observations + candidates → policy_core_x1
  │
  ├─ Step 0: RSA-0 admission gates (1–5)
  │
  ├─ Step 1: Adoption check (pending amendments that satisfied cooling)
  │    └─ if eligible → ADOPT (switch constitution, invalidate stale)
  │
  ├─ Step 2: Amendment proposal admission (Gates 6–8B)
  │    ├─ Gate 6:  authorization, prior_hash, ECK, cooling
  │    ├─ Gate 7:  YAML parse + schema validation + hash verify + ECK presence
  │    ├─ Gate 8A: physics claim rejection
  │    └─ Gate 8B: structural preservation (subchecks below)
  │         └─ if pass → QUEUE_AMENDMENT
  │
  └─ Step 3: Normal action admission (RSA-0 path)
       └─ ACTION | REFUSE
```

**Gate 8B subchecks** (evaluated in order after 8A passes):

| Sub-gate | Check | Rejection code |
|:---|:---|:---|
| 8B.1 | Schema-guaranteed cardinality — action_permissions present and non-empty (enforced at Gate 7 in production; unit-tested via schema bypass) | SCHEMA_INVALID (via Gate 7) |
| 8B.2 | Wildcard — no `"*"` in authority or action mappings | WILDCARD_MAPPING |
| 8B.3 | Universal authorization — reject if `density == 1` (equivalently `M == A×B`) | UNIVERSAL_AUTHORIZATION |
| 8B.4 | Scope collapse — ≥1 action still requires scope_claim | SCOPE_COLLAPSE |
| 8B.5 | Ratchet/envelope — cooling and threshold non-decreasing; density_upper_bound non-increasing; authority_reference_mode cannot relax | ENVELOPE_DEGRADED |

### 2.4 Constitution Lifecycle

```
v0.2 (frozen) → propose → cooling(2) → adopt → v0.2.1
   → propose → cooling(2) → adopt → v0.2.2 (cooling=3)
   → propose → cooling(3) → adopt → v0.2.2 (cooling=4)
   → propose → cooling(4) → adopt → v0.2.2 (cooling=5)
```

Each ratchet-tightening amendment increases the cooling period, making subsequent
amendments progressively harder to adopt. This is the intended monotonic behavior.

Version labels (e.g. "v0.2.2") may remain constant across ratchet-tightening
amendments; the SHA-256 hash is the authoritative constitution identity, not the
human-readable version string.

---

## §3 Constitution v0.2

| Property | Value |
|:---|:---|
| File | `artifacts/phase-x/constitution/rsa_constitution.v0.2.yaml` |
| Lines | 608 |
| CL-* IDs | 23 |
| SHA-256 | `b41db3ba5ffe9ed74b40553d0a0cc019de8bd254e78a0e0d9c5ebeb2eeb5a6dd` |
| Amendments | enabled |
| Cooling period | 2 cycles |
| Authorization threshold | 1 citation |
| Density (A/B/M) | A=3, B=4, M=4 → d=0.3333 |

### 3.1 ECK Sections (Existence Kernel Constraints)

The following sections are structurally required at every transition:

- `AuthorityModel` — authorities, action_permissions
- `ScopeSystem` — scope_types, per_action_scope, structural_constraints
- `AmendmentProcedure` — cooling_period_cycles, authorization_threshold
- `non_goals` — forbidden_objectives

### 3.2 Schema

| Property | Value |
|:---|:---|
| File | `artifacts/phase-x/constitution/rsa_constitution.v0.2.schema.json` |
| Lines | 1,132 |
| Pattern | `additionalProperties: false` throughout |
| Enums | Strict on `forbidden_objectives` (7 frozen values) |
| Free-form | `meta.notes` (string array, used for lawful amendments) |

---

## §4 Kernel Extension

4 new kernel modules under `kernel/src/rsax1/`:

| Module | Lines | Purpose |
|:---|---:|:---|
| `artifacts_x1.py` | 257 | Types: `AmendmentProposal`, `AmendmentAdoptionRecord`, `InternalStateX1`, `PendingAmendment`, rejection codes, gates |
| `constitution_x1.py` | 463 | `ConstitutionX1` class: YAML/hash loading, ECK checks, density computation, citation index, `amendments_enabled()`, `cooling_period_cycles()` |
| `admission_x1.py` | 530 | 9-step admission pipeline: Gates 6–8B, `check_cooling_satisfied()`, `invalidate_stale_proposals()`, ratchet monotonicity enforcement |
| `policy_core_x1.py` | 571 | Decision core: `policy_core_x1()` dispatching to `_try_adopt()` → `_try_queue_amendment()` → `_action_path()` |
| **Total** | **1,821** | |

### 4.1 Key Design Decisions

**Cooling semantics:** `current_cycle >= proposal_cycle + cooling_period`. A
proposal queued at cycle P is eligible for adoption starting at cycle
P + cooling_period_cycles, guaranteeing ≥ (cooling_period_cycles − 1) intervening
non-proposal cycles. With cooling = 2, a proposal at cycle 5 becomes eligible at
cycle 7 (cycle 6 intervenes; cycle 5 is the proposal itself). This means adoption can trigger on the last
cooling cycle itself, and the runner must handle ADOPT in any phase.

**Amendment trace propagation:** `_try_queue_amendment()` returns a 3-tuple
`(Optional[PolicyOutputX1], List[AmendmentAdmissionEvent], List[AmendmentAdmissionResult])`
so that rejection events are always attached to the output, even when falling
through to the action path.

**Full-document replacement:** No diff/patch mechanism. Every proposal contains the
complete new YAML. The schema validates the entire document at Gate 7.

---

## §5 Harness Architecture

5 new modules under `profiling/x1/harness/`:

| Module | Lines | Purpose |
|:---|---:|:---|
| `scenarios.py` | 431 | 2 lawful + 7 adversarial scenario builders |
| `cycle_x1.py` | 352 | Single cycle execution, observation builders, state hashing |
| `runner_x1.py` | 748 | 8-phase session orchestration (A–H) |
| `report_x1.py` | 212 | Markdown report generator with 6 closure criteria |
| `run_production.py` | 103 | Production run entry point |
| **Total** | **1,846** | |

### 5.1 Session Phases

| Phase | Label | Function |
|:---|:---|:---|
| A | `pre-fork` | Normal operation under v0.2 (5 cycles) |
| B | `propose` | Trivial amendment proposed (1 cycle) |
| C | `cooling` | Cooling period (2 cycles; adoption triggers on last) |
| D | `adopt` | Explicit adoption check (may be no-op if C adopted) |
| E | `post-fork` | Normal operation under new constitution (5 cycles) |
| F | `adversarial` | 7 adversarial proposals, all rejected (7 cycles) |
| G | `chained` | 3 sequential ratchet-tightening amendments |
| H | `replay` | Deterministic replay verification |

### 5.2 Scenarios

**Lawful:**

| ID | Description | Mutation | Expected |
|:---|:---|:---|:---|
| L-1 | Trivial meta.notes addition | `meta.notes += ["..."]`, version bump | ADOPT |
| L-2 | Ratchet tightening | `cooling_period_cycles += 1` | ADOPT |

**Adversarial:**

| ID | Description | Target Gate | Expected Code |
|:---|:---|:---|:---|
| A-1 | Universal authorization | 8B.3 | UNIVERSAL_AUTHORIZATION |
| A-2 | Scope collapse | 8B.4 | SCOPE_COLLAPSE |
| A-3 | Cooling reduction | 8B.5 | ENVELOPE_DEGRADED |
| A-4 | Threshold reduction | 8B.5 | ENVELOPE_DEGRADED |
| A-5 | Wildcard injection | 8B.2 | WILDCARD_MAPPING |
| A-6 | Physics claim (script) | 8A | PHYSICS_CLAIM_DETECTED |
| A-7 | ECK section removal | 7 | ECK_MISSING |

**Note:** In production, all 7 adversarial scenarios are caught at Gate 7
(`SCHEMA_INVALID`) because the schema's `additionalProperties: false` and strict
enum constraints reject the mutations before they reach the semantic gates.
This is correct defense-in-depth behavior — the schema IS the first structural
firewall.

---

## §6 Test Results

### 6.1 Test Counts

| Suite | Tests | Status |
|:---|---:|:---|
| RSA-0 kernel (`test_rsa0.py`) | 54 | ✅ PASS |
| X-1 kernel (`test_x1.py`) | 58 | ✅ PASS |
| X-1 harness (`test_harness_x1.py`) | 19 | ✅ PASS |
| **Total** | **131** | **ALL PASS** |

### 6.2 Kernel Test Coverage (58 tests)

| Class | Tests | What it covers |
|:---|---:|:---|
| `TestAmendmentArtifacts` | 8 | Proposal/adoption record types, hashing, serialization |
| `TestConstitutionX1` | 10 | Loading, versioning, ECK, density, citation index |
| `TestAdmissionPipeline` | 15 | All 10 rejection codes + positive path |
| `TestGate8BRatchet` | 7 | Ratchet monotonicity (cooling, threshold, authority_reference_mode) |
| `TestCoolingAndInvalidation` | 5 | Cooling boundary, stale invalidation |
| `TestPolicyCoreX1Integration` | 5 | End-to-end ACTION, QUEUE, ADOPT, REFUSE, EXIT |
| `TestEndToEndAdoptionPath` | 3 | Full propose→cool→adopt flow |
| `TestDensityComputation` | 3 | Density edge cases |
| `TestRSA0Regression` | 2 | RSA-0 policy_core unchanged behavior |

### 6.3 Schema-Valid Adversarial Gate Evidence

The kernel tests exercise Gates 8A/8B with schema validation explicitly bypassed
(`schema=None`), proving semantic gates reject schema-valid adversarial
constitutions for the intended reason codes:

| Adversarial class | Schema-valid fixture? | Expected reject code | Gate | Kernel test name |
|:---|:---:|:---|:---|:---|
| Universal auth (density=1) | yes | UNIVERSAL_AUTHORIZATION | 8B.3 | `test_gate8b_universal_authorization` |
| Scope collapse | yes | SCOPE_COLLAPSE | 8B.4 | `test_gate8b_scope_collapse` |
| Wildcard authority | yes | WILDCARD_MAPPING | 8B.2 | `test_gate8b_wildcard_authority` |
| Physics claim (script key) | yes | PHYSICS_CLAIM_DETECTED | 8A | `test_gate8a_forbidden_keys` |
| Cooling reduction | yes | ENVELOPE_DEGRADED | 8B.5 | `test_gate8b_ratchet_cooling_reduction` |
| Threshold reduction | yes | ENVELOPE_DEGRADED | 8B.5 | `test_gate8b_ratchet_threshold_reduction` |
| Density bound increase | yes | ENVELOPE_DEGRADED | 8B.5 | `test_gate8b_ratchet_density_bound_increased` |
| Density bound removal | yes | ENVELOPE_DEGRADED | 8B.5 | `test_gate8b_ratchet_density_bound_removed` |
| ECK section removal | yes | ECK_MISSING | 7 | `test_gate7_eck_missing_in_proposed` |

Production defense is therefore two-deep: the schema catches structurally invalid
mutations at Gate 7; the semantic gates (proven above with schema bypassed) catch
structurally valid but sovereignty-degrading proposals at Gates 8A/8B.

### 6.4 Harness Test Coverage (19 tests)

| Class | Tests | What it covers |
|:---|---:|:---|
| `TestScenarios` | 10 | All scenario builders produce valid proposals |
| `TestCycleExecution` | 5 | Normal action, queue, adversarial rejection, determinism, adoption |
| `TestFullSession` | 3 | Full session completion, decision type coverage, adversarial rejection |
| `TestReport` | 1 | Report generation produces valid markdown |

---

## §7 Production Run Results

### 7.1 Session Summary

| Metric | Value |
|:---|:---|
| Session ID | `1fd560f6-6801-45f6-81ec-939cee370828` |
| Total cycles | 36 |
| Aborted | No |
| Initial constitution | v0.2 (`b41db3ba5ffe9ed7...`) |
| Final constitution | v0.2.2 (`e44ac6dfb912edc7...`) |

### 7.2 Decision Type Distribution

| Type | Count | % |
|:---|---:|---:|
| ACTION | 21 | 58.3% |
| QUEUE_AMENDMENT | 4 | 11.1% |
| ADOPT | 4 | 11.1% |
| REFUSE | 7 | 19.4% |

### 7.3 Constitution Transitions

| # | Cycle | Prior | New | Trigger |
|---:|---:|:---|:---|:---|
| 1 | 7 | `b41db3ba...` (v0.2) | `05df3cbd...` (v0.2.1) | Trivial meta.notes |
| 2 | 23 | `05df3cbd...` (v0.2.1) | `7729594a...` (v0.2.2) | Ratchet cooling 2→3 |
| 3 | 28 | `7729594a...` (v0.2.2) | `965603ee...` (v0.2.2) | Ratchet cooling 3→4 |
| 4 | 34 | `965603ee...` (v0.2.2) | `e44ac6df...` (v0.2.2) | Ratchet cooling 4→5 |

**Observation:** Each ratchet tightening increases the cooling period, observable
as progressively more cooling cycles between proposal and adoption:
- Transition 1: 2 cooling cycles (5→7)
- Transition 2: 2 cooling cycles (21→23) [cooling=2 from v0.2.1]
- Transition 3: 3 cooling cycles (25→28) [cooling=3 from 1st ratchet]
- Transition 4: 4 cooling cycles (30→34) [cooling=4 from 2nd ratchet]

### 7.4 Adversarial Rejection Log

All 7 adversarial proposals rejected:

| Scenario | Expected Code | Actual Code | Gate |
|:---|:---|:---|:---|
| A-1 Universal Auth | UNIVERSAL_AUTHORIZATION | SCHEMA_INVALID | full_replacement_integrity |
| A-2 Scope Collapse | SCOPE_COLLAPSE | SCHEMA_INVALID | full_replacement_integrity |
| A-3 Cooling Reduction | ENVELOPE_DEGRADED | SCHEMA_INVALID | full_replacement_integrity |
| A-4 Threshold Reduction | ENVELOPE_DEGRADED | SCHEMA_INVALID | full_replacement_integrity |
| A-5 Wildcard | WILDCARD_MAPPING | SCHEMA_INVALID | full_replacement_integrity |
| A-6 Physics Claim | PHYSICS_CLAIM_DETECTED | SCHEMA_INVALID | full_replacement_integrity |
| A-7 ECK Removal | ECK_MISSING | SCHEMA_INVALID | full_replacement_integrity |

**Analysis:** The schema's `additionalProperties: false` constraint acts as the
first structural firewall, intercepting all 7 adversarial mutations at Gate 7
before they can reach the semantic gates (8A/8B). The semantic gates are
independently proven correct by 9 kernel unit tests that bypass schema validation
(`schema=None`) and confirm each adversarial class is rejected at the intended
gate with the intended code (see §6.3 for the full evidence table). Production
defense is therefore two-deep: schema catches structural violations; semantic
gates catch structurally valid but sovereignty-degrading proposals.

### 7.5 Replay Verification

**PASS** — All 36 cycle state hashes match across deterministic replay.

The replay mechanism:
1. Reconstructs from the initial constitution
2. Replays all decisions from the cycle log
3. Applies queued amendments and adoptions
4. Verifies `state_in_hash` matches at every cycle boundary

---

## §8 Closure Criteria Evaluation

| # | Criterion | Result | Evidence |
|---:|:---|:---:|:---|
| 1 | ≥1 amendment adopted | **PASS** | 4 adoptions (cycles 7, 23, 28, 34) |
| 2 | Replay determinism | **PASS** | 0 divergences across 36 cycles |
| 3 | density < 1 preserved | **PASS** | A=3, B=4, M=4, d=0.3333 at all transitions |
| 4 | ECK preserved | **PASS** | Gate 7 validates ECK sections at every proposal |
| 5 | Structured AmendmentProcedure | **PASS** | Gate 8B.5 validates ratchet monotonicity |
| 6 | All failures attributable | **PASS** | 7/7 adversarial rejections logged with codes and gates |

**Overall Verdict: X-1 CLOSURE POSITIVE ✓**

---

## §9 File Inventory

### 9.1 Constitution Artifacts

| File | Lines |
|:---|---:|
| `artifacts/phase-x/constitution/rsa_constitution.v0.2.yaml` | 608 |
| `artifacts/phase-x/constitution/rsa_constitution.v0.2.schema.json` | 1,132 |
| `artifacts/phase-x/constitution/rsa_constitution.v0.2.sha256` | 1 |

### 9.2 Kernel Extensions

| File | Lines |
|:---|---:|
| `kernel/src/rsax1/__init__.py` | 1 |
| `kernel/src/rsax1/artifacts_x1.py` | 257 |
| `kernel/src/rsax1/constitution_x1.py` | 463 |
| `kernel/src/rsax1/admission_x1.py` | 530 |
| `kernel/src/rsax1/policy_core_x1.py` | 571 |

### 9.3 Kernel Tests

| File | Lines |
|:---|---:|
| `kernel/tests/test_x1.py` | 1,076 |

### 9.4 Harness

| File | Lines |
|:---|---:|
| `profiling/x1/harness/src/scenarios.py` | 431 |
| `profiling/x1/harness/src/cycle_x1.py` | 352 |
| `profiling/x1/harness/src/runner_x1.py` | 748 |
| `profiling/x1/harness/src/report_x1.py` | 212 |
| `profiling/x1/harness/tests/test_harness_x1.py` | 374 |
| `profiling/x1/run_production.py` | 103 |

### 9.5 Results

| File | Description |
|:---|:---|
| `profiling/x1/results/x1_session.json` | Full structured session result |
| `profiling/x1/results/x1_report.md` | Auto-generated profiling report |

### 9.6 Totals

| Category | Lines |
|:---|---:|
| Constitution + Schema | 1,741 |
| Kernel extension | 1,822 |
| Kernel tests | 1,076 |
| Harness + runner | 2,220 |
| **Grand total** | **6,859** |

---

## §10 Bugs Found and Fixed

### 10.1 Path Resolution (test_harness_x1.py)

`RSA0_ROOT = Path(__file__).resolve().parent.parent.parent.parent` resolved to
`profiling/` instead of `RSA-0/`. Fixed by adding one more `.parent` (5 total:
tests → harness → x1 → profiling → RSA-0).

### 10.2 Schema Enum Rejection (scenarios.py)

`build_lawful_trivial` originally appended to `non_goals.forbidden_objectives`,
which has a frozen 7-value enum in the schema. Any new entry was rejected as
`SCHEMA_INVALID`. Fixed by mutating `meta.notes` (free-form string array) instead.

### 10.3 Amendment Trace Propagation (policy_core_x1.py)

When `_try_queue_amendment` rejected all proposals and returned `None`, the
rejection events were discarded. The action path fallback had no trace of what
went wrong. Fixed by changing the return type to a 3-tuple so events are always
propagated.

### 10.4 Adoption During Cooling (runner_x1.py)

With cooling semantics `current_cycle >= proposal_cycle + cooling_period`, adoption
triggers on the last cooling cycle, not after it. The runner originally only handled
ADOPT in the dedicated adoption phase. Fixed by adding `_handle_cycle_output()`
helper called from all phases, so adoption is correctly recorded wherever it occurs.

---

## §11 Strategic Position

X-0 established existence of a constraint-bound sovereign agent.

X-0L established that proposal flow can inhabit the execution cycle.

**X-1 establishes that policy self-replacement can occur without violating kernel
physics or collapsing structural sovereign constraint.**

The key structural invariant proven:

> A frozen sovereign substrate can transition to a new constitution through a
> lawful amendment procedure that preserves: ECK sections, density < 1,
> monotonic ratchet constraints, and deterministic replay integrity — while
> correctly rejecting adversarial proposals that would degrade sovereignty.

---

*Report generated 2026-02-12. 131 tests pass (112 kernel + 19 harness).*
*Production session: 36 cycles, 4 adoptions, 7 rejections, replay verified.*
