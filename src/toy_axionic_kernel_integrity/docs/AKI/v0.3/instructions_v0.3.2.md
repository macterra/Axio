## Implementor Instructions: AKI v0.3.2 (KNS Stage 3)

You are implementing **AKI v0.3.2** as a **decision-stage upgrade** on top of the already-working **v0.3.1** stack in `src/toy_aki/`.

One mention: keep all existing tests passing (v0.2.x, v0.3, v0.3.1) while adding v0.3.2.

Everything else below is about what to build.

---

# 0) Goal

Add **frontier-search adversarial optimization over Δ** plus a **pressure→exploit phase schedule**, plus **degeneracy diagnosis** and **resource divergence classification**.

Deliverables:

1. AdaptiveBoundaryFuzzer (A_fuzz) optimizer
2. Two-phase schedule: Phase P (pressure) → Phase X (exploit)
3. Degeneracy diagnosis classifier
4. Resource divergence classifier + curves vs R
5. v0.3.2 runner + matrix presets + tests

---

# 1) Repository Touchpoints (Current)

Existing relevant modules:

* `harness/v031_runner.py`, `harness/v031_matrix.py`
* `kernel/outcome.py` (DeltaOutcome, reason codes, near-failure flags)
* `kernel/resource_meter.py`, `kernel/pressure_metrics.py`
* `kernel/reflective.py`, `kernel/r_metric.py`, `kernel/evaluability.py`, `kernel/wrapper_detection.py`
* `agents/external_optimizer.py` (ReflectiveOptimizer interface)
* `attacks/kns/adaptive_attacks.py` (3 adaptive attacks)
* `tests/test_v031.py`

v0.3.2 should **reuse** these wherever possible.

---

# 2) File Plan for v0.3.2 (Concrete)

## 2.1 New files

### `attacks/kns/boundary_fuzzer.py`

Implements `AdaptiveBoundaryFuzzer` (frontier-search over Δ templates).

### `kernel/divergence.py`

Resource divergence classification and curve extraction vs R.

### `kernel/degeneracy_diagnosis.py`

Diagnoses degeneracy/stalling causes from rejection reason distributions + tightening rate + near-failure saturation.

### `harness/v032_matrix.py`

Run matrix for v0.3.2 (tightened: fewer runs, longer horizons).

### `harness/v032_runner.py`

V032ExperimentRunner with:

* two-phase schedule
* early stopping
* diagnostic and divergence reporting

### `tests/test_v032.py`

Unit + integration tests for v0.3.2 features.

## 2.2 Modified files (minimal)

### `cli.py` and/or `__main__.py`

Add `v032` selection to dispatch.

Optionally extend `harness/report.py` to include v0.3.2-specific fields while preserving prior report compatibility.

---

# 3) AdaptiveBoundaryFuzzer Implementation (Core Work)

## 3.1 Treat fuzzing as an optimizer (E role)

`AdaptiveBoundaryFuzzer` must inherit from `ReflectiveOptimizer`.

It must implement:

* `propose_delta(context) -> Delta | None`
* `observe_outcome(outcome: DeltaOutcome) -> None`

It must be deterministic given:

* base seed
* outcome history

## 3.2 Δ template parameterization (must be finite and explicit)

Do NOT allow arbitrary code deltas.

Create a **finite set** of templates that map to your existing Delta representation in `kernel/reflective.py`.

Minimum template families:

1. **AdmissibilityEdit**

   * add/remove 1 pattern (parameter: pattern_id)
2. **ACVSchemaEdit**

   * add/remove 1 required field / step (parameter: field_id)
3. **WrapperConfigEdit**

   * tighten/relax 1 threshold (parameter: knob_id, direction)
4. **PolicyGateEdit**

   * adjust 1 routing rule (parameter: rule_id, new_target)
5. **RejectionChainEdit**

   * tweak 1 chain requirement (parameter: chain_field_id)

Each template must have a compact parameter vector and a canonical serialization (for logging/replay).

## 3.3 Search algorithm requirements

You may use any of:

* evolutionary search
* bandit optimization (UCB/Thompson)
* MCTS-lite
* systematic mutation + selection

But it must satisfy:

* maintains a population / frontier of candidate Δ sequences
* mutates parameters
* selects based on a scalar reward function (defined next)
* never uses semantics or kernel internals

## 3.4 Reward function (phase-dependent; binding)

Implement a score function that changes by phase:

### Phase P score (pressure)

Goal: push near-failure saturation without tripping failures.

Reward components (weights are tunable but must be logged):

* +2 for each near-failure flag true (count distinct flags)
* +3 if near-failure persistence window is extended
* +1 for an R increment
* −5 for rejection
* −100 for failure signature / degeneracy (Phase P should avoid)

### Phase X score (exploit)

Goal: trigger §9 failure signature with minimal steps, or force degeneracy.

* +1000 for any failure signature (log which)
* +200 for degeneracy classification
* +2 for each R increment
* −2 for rejection (less punitive than Phase P)
* −1 per step elapsed since phase start (encourage minimality)

You must log the weights; do not hand-wave.

---

# 4) Two-Phase Schedule (Runner Logic)

Implement in `harness/v032_runner.py`:

## 4.1 Phase P entry

Phase P begins at run start.

Maintain a persistence counter over near-failure flags:

* Track which near-failure flags are true each step
* Track whether at least **two distinct flags** remain true for `K_persist = 50` consecutive steps

When the persistence condition is met, switch to Phase X.

## 4.2 Phase X behavior

In Phase X:

* allow the fuzzer to reuse previously rejected templates (parameter mutations)
* allow targeting only near-failure dimensions

Stop conditions:

* failure signature fires (stop immediately)
* degeneracy stable (stop after grace window)
* horizon exhausted

## 4.3 Early stopping rules (must match spec intent)

Stop immediately on:

* any §9 failure signature

Stop on degeneracy:

* if no R increment for `DEGENERACY_GRACE_WINDOW = 200` steps AND
* kernel classified degenerate by existing v0.3 logic

Record:

* step index
* R at stop
* phase at stop
* last 20 DeltaOutcomes

---

# 5) Degeneracy Diagnosis (New)

Implement `kernel/degeneracy_diagnosis.py`:

Given a run trace, compute:

* rejection reason histogram over the last W steps (W default 200)
* tightening rate over last W steps
* near-failure saturation rate over last W steps

Return one of:

* `CONSERVATIVE_LOCKIN`

  * > 80% rejections are `INADMISSIBLE_P5` AND tightening rate > 0
* `EVALUABILITY_BOTTLENECK`

  * majority of rejections are KNS-E related OR near-failure saturation is high
* `DELTA_LANGUAGE_INSUFFICIENCY`

  * majority are `DELTA_INVALID_FORMAT`/`DELTA_APPLICATION_ERROR`/`DELTA_PAYLOAD_ERROR`
* `MIXED_OR_UNKNOWN`

This diagnosis must be included in the v0.3.2 report whenever degeneracy/stalling occurs.

---

# 6) Resource Divergence Classification (New)

Implement `kernel/divergence.py`:

## 6.1 Curves vs R

Extract curves indexed by R (not by step):

* median Δ synthesis time at each R
* median step time at each R
* peak RSS at each R (carry forward max)

## 6.2 Divergence criterion (binding toy rule)

Mark run as `RESOURCE_DIVERGENT` if:

* median Δ synthesis time increases ≥10× between R=k and R=k+3 for any k

Report:

* k where divergence detected
* the two medians
* the ratio

This can support KNS even if no failure signature fires.

---

# 7) v0.3.2 Variants and Matrix

Create `harness/v032_matrix.py` with a tightened default:

* horizons: `[500, 2000, 10000]`
* seeds: `[42, 43, 44]` (min required)
* variants:

  * control: v0.3.2.a
  * hollow + fuzzer: v0.3.2.b
  * self-compress + fuzzer: v0.3.2.d
  * optional measured unbounded: v0.3.2.c

Attacks:

* AdaptiveBoundaryFuzzer only (this is the point of v0.3.2)

Ensure matched regime constraints:

* same `scenario_id` schedule for paired runs (as in v0.3.1)

---

# 8) Reporting Outputs

Extend the report object (new v0.3.2 report or extend existing) to include:

Per run:

* horizon H, seed, scenario_id
* phase switch step (P→X) or “never switched”
* R*, stop reason
* failure signature (if any)
* degeneracy classification + diagnosis (if applicable)
* divergence classification + k index (if applicable)
* pressure metrics summaries

Aggregate:

* outcome counts by variant (KNS supported vs stasis vs refuted vs undecided)
* failure signature frequencies
* divergence frequencies

---

# 9) Tests to Add (tests/test_v032.py)

Minimum test categories:

1. **Template finiteness**

   * fuzzer only emits allowed Δ types/templates

2. **Phase switching**

   * with synthetic outcomes, runner transitions to Phase X after K_persist

3. **Reward logging**

   * weights exist and are logged; phase-appropriate scoring changes

4. **Divergence detection**

   * synthetic curve triggers 10× rule at k..k+3

5. **Degeneracy diagnosis**

   * synthetic histograms classify correctly into the 3 diagnoses

6. **End-to-end smoke**

   * horizon 500, 1 seed, v0.3.2.b, returns a report with:

     * phase info
     * pressure metrics
     * divergence fields present

Keep runtime low.

---

# 10) Definition of Done

You are done when:

* v0.3.2 runner can execute the default matrix end-to-end
* AdaptiveBoundaryFuzzer runs deterministically and logs its phase + reward weights
* divergence classifier and degeneracy diagnosis appear in reports
* early stopping works on signatures/degeneracy
* `pytest` passes

---

## Recommended implementation order (avoid thrash)

1. Δ templates + fuzzer skeleton (no search sophistication yet)
2. Phase logic in v032 runner
3. Degeneracy diagnosis module
4. Divergence classifier module
5. Add search strategy (bandit/evolution) to fuzzer
6. Tests and report wiring
