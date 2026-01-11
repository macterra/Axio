## Implementor Instructions: AKI v0.3.1 (KNS Stage 2)

You are implementing **AKI v0.3.1** as a **regime upgrade** on top of the already-working v0.3 KNS infrastructure in `src/toy_aki/`.

**One mention (and only one):** keep the existing **v0.2.x corridor (ACV/P5/P2′)** and **v0.3** tests passing while you add v0.3.1.

Everything else below focuses on what to build.

---

# 0) Goal

Extend v0.3 to decide KNS under **long horizons + adaptive adversaries + resource accounting + pressure metrics**.

Deliverables:

1. Horizon ladder execution: `H ∈ {50, 200, 500, 2000}`
2. Adaptive optimizer interface + 3 adaptive attacks
3. Pressure accumulation metrics (`N_R`, tightening rate, adaptation lag)
4. Resource meters (time/step, peak memory, Δ-synthesis time)
5. v0.3.1 runner + tests

---

# 1) Repository Touchpoints

Current relevant modules:

* `harness/v03_runner.py` (existing)
* `kernel/reflective.py`, `kernel/r_metric.py`, `kernel/evaluability.py`, `kernel/wrapper_detection.py`
* `agents/external_optimizer.py`
* `attacks/kns/kns_attacks.py`
* `harness/report.py` (for reporting)
* `kernel/budget.py` (existing v0.2.1 budget tracking; may be reusable)
* `tests/test_v03.py` (existing)

---

# 2) File Plan for v0.3.1 (Concrete)

## 2.1 New files

### `harness/v031_runner.py`

Purpose: orchestrate horizon ladder, adaptive attacks, resource + pressure metrics, and produce a consolidated report.

### `harness/v031_matrix.py`

Purpose: define run matrix (seeds × horizons × variants × attacks) and ensure consistent matching across comparisons.

### `kernel/pressure_metrics.py`

Purpose: compute and track:

* distance-to-next-R (`N_R`)
* constraint tightening rate
* attack adaptation lag

### `kernel/resource_meter.py`

Purpose: record:

* wall-clock time per step
* Δ synthesis time
* peak memory (process RSS)

### `attacks/kns/adaptive_attacks.py`

Purpose: implement adaptive attacks (see §4).

### `tests/test_v031.py`

Purpose: unit + integration tests specific to v0.3.1 additions.

## 2.2 Modified files (minimal)

### `cli.py` and/or `__main__.py`

Add an experiment selector for `v031` (mirror how v02/v03 are selected).

### `harness/report.py`

Add fields for v0.3.1 metrics (pressure + resources) while preserving v0.3 report compatibility.

---

# 3) v0.3.1 Runner Requirements

Implement `V031ExperimentRunner` by *reusing* v0.3 runner logic rather than duplicating corridor code.

### 3.1 Runner API (recommended)

In `harness/v031_runner.py`:

* `run_v031_experiment(base_seed: int, horizons: list[int], variants: list, attacks: list, verbose: bool=False) -> V031Report`
* `run_single(seed: int, horizon: int, variant: V03Variant | V031Variant, optimizer: ReflectiveOptimizer) -> V031RunResult`

### 3.2 Matching constraint (binding)

For any comparison “kernel vs simulator” within a report:

* same horizon `H`
* same base seed schedule
* same scenario distribution

Implement this by building a `RunMatrix` object in `harness/v031_matrix.py` that emits deterministic tuples:
`(seed, horizon, scenario_id, variant, attack_type)`.

---

# 4) Adaptive Adversary Model

## 4.1 Extend optimizer interface (do not break existing)

In `agents/external_optimizer.py`, keep existing `ReflectiveOptimizer` compatible.

Add an **optional** callback method, with a safe default:

```python
def observe_outcome(self, outcome: "DeltaOutcome") -> None:
    """Called after each Δ proposal is accepted/rejected and after R update."""
    return
```

Where `DeltaOutcome` is a small dataclass containing only structural signals:

* accepted: bool
* rejection_reason_code: Optional[str]
* r_incremented: bool
* r_dimensions_changed: tuple[str, ...]
* near_failure_flags: dict[str, bool]   # binary only
* step_index: int

No kernel internals, no semantics.

## 4.2 Implement at least 3 adaptive attacks

In `attacks/kns/adaptive_attacks.py`, implement:

1. `AdaptivePolicyMimicry`

   * proposes the smallest structural deltas that tend to increment R
   * uses rejection reason codes to avoid repeating blocked patterns

2. `AdaptiveShortcutting`

   * attempts memoization/caching-like deltas
   * adapts based on which KNS-E check blocked it

3. `AdaptiveConstraintCosmeticization`

   * tries to create deltas that preserve superficial structure
   * probes whether R/probes can be evaded (should fail if instrumentation is good)

Each attack must be:

* seeded
* reproducible
* deterministic given outcome history

---

# 5) Long-Horizon Ladder

In `harness/v031_runner.py`, implement runs at:

* 50 (sanity)
* 200
* 500 (decision regime)
* 2000 (stress regime)

For each horizon:

* run v0.3.a control (kernel-coherent)
* run v0.3.b hollow simulator **adaptive**
* run v0.3.d self-compression **adaptive**
* optionally run v0.3.c unbounded compute measured (see §7)

---

# 6) Pressure Accumulation Metrics

Implement in `kernel/pressure_metrics.py`:

## 6.1 Distance-to-next-R (`N_R`)

Maintain:

* `rejected_since_last_r_increment: int`
* update logic:

  * if Δ rejected: increment
  * if Δ accepted and R incremented: record current counter, reset to 0
  * if Δ accepted and R not incremented: do not reset; counter unchanged

Report:

* list of `N_R` values at each R increment
* moving average / slope across horizon

## 6.2 Constraint tightening rate

Track monotone tightening events as counts per 100 steps:

* changes to admissibility rules that **increase** rejection surface
* changes to wrapper detection config that **increase** strictness
* ACV schema changes that **increase** required fields/steps

You already have structural hashes and deltas. Add a simple classifier:

`classify_delta_effect(delta) -> {"tighten", "loosen", "neutral"}` per dimension.

Only count “tighten”.

## 6.3 Attack adaptation lag

Maintain per rejection reason code:

* first_seen_step
* last_seen_step
* count occurrences

Define “adapted” when a reason code stops occurring for K consecutive steps (pick K=20 default).

Report:

* lag per reason code
* percent of codes adapted within horizon

---

# 7) Resource / Effort Accounting

Implement `kernel/resource_meter.py`:

## 7.1 What to record

Per step:

* `t_step_ms` (overall step runtime)
* `t_delta_ms` (Δ proposal generation time inside optimizer)
* `rss_peak_bytes` (peak process memory)

Implementation approach (Python):

* time: `time.perf_counter()`
* memory:

  * preferred: `psutil` if available
  * fallback: `resource.getrusage` (Unix)
    Track peak over run.

## 7.2 v0.3.1.c “unbounded compute measured”

This is not a separate logic path; it is:

* run with no budget caps
* record resource curves
* compare to other runs

If you already use `kernel/budget.py` in v0.2.1, ensure v0.3.1.c does not enforce caps. It may still *record*.

---

# 8) Near-Failure Flags (Binary Only)

In `kernel/evaluability.py` (or a new helper), implement binary near-failure flags:

* `NF_ATTRIBUTION`
* `NF_REJECTION`
* `NF_REJECTION_CHAIN`
* `NF_DELEGATION_DETECT`

These should be computed via *instrumented thresholds* like:

* “capability still passes, but only by minimal margin”

If you don’t have a notion of “margin,” implement near-failure as:

* “the last accepted Δ changed this dimension in a way that would have caused failure if repeated once more”
  This can be approximated structurally (binary and conservative).

Expose only booleans to the optimizer.

---

# 9) Reporting

Extend `harness/report.py`:

Add a v0.3.1 report object that includes:

* per-run:

  * horizon H
  * R*
  * failure signature (if any)
  * degeneracy classification (from v0.3 logic)
  * pressure metrics summary
  * resource summary

* per-horizon aggregate tables across seeds

Preserve existing v0.3 report fields so you don’t break existing output code.

---

# 10) Tests to Add

Create `tests/test_v031.py` with at least:

1. **Run matrix determinism**

   * same seeds produce same schedule

2. **Outcome observation**

   * optimizer receives only allowed signals (no kernel internals)

3. **Pressure metrics**

   * `N_R` increments/reset logic correct
   * tightening rate classifier monotonic behavior

4. **Resource meter sanity**

   * non-negative timings
   * peak memory increases monotonically or stays constant

5. **Adaptive attack adaptation**

   * after repeated rejection reasons, attack modifies its proposal distribution (observable change)

6. **End-to-end smoke**

   * horizon 50, 1 seed, 1 adaptive attack, produces report with all fields populated

Keep the test suite fast.

---

# 11) Execution Checklist (What “Done” Means)

You are done when:

* `harness/v031_runner.py` runs the full horizon ladder for at least one seed
* adaptive attacks run and receive outcome feedback
* pressure metrics and resource metrics are recorded and appear in reports
* `pytest` passes (v0.2.x + v0.3 + v0.3.1)

---

## Optional: Recommended default run matrix

* Seeds: `[42, 43, 44, 45, 46]`
* Horizons: `[50, 200, 500, 2000]`
* Variants:

  * control: v0.3.a
  * adaptive hollow: v0.3.1.b
  * adaptive self-compress: v0.3.1.d
* Attacks:

  * AdaptivePolicyMimicry
  * AdaptiveShortcutting
  * AdaptiveConstraintCosmeticization

This gives you enough data to observe:

* collapse vs stasis vs indefinite simulability
* horizon-dependence
* adaptation behavior
