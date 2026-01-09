# RSA v3.1 Implementation Report

**Version:** 3.1 (RSA-LA-0 — Learning/Heuristic Adversaries)
**Date:** 2026-01-09
**Status:** ⏳ IN PROGRESS — Implementation Complete, Runs Pending
**Artifact Status:** 🔒 LOCKED (policy.py hash: `cb909ea6`)

---

## ✅ Protocol Compliance Status

**This implementation is v3.1-compliant.** All pre-run acceptance tests pass:

1. **Acceptance Tests**: 11/14 pre-run PASS; 3/14 runtime PENDING
2. **Run 0 (Baseline)**: ⏳ PENDING
3. **Run 1 (Model M)**: ⏳ PENDING
4. **Run 2 (Model N)**: ⏳ PENDING
5. **Run 3 (Model O)**: ⏳ PENDING

**Total Runs Planned**: 40 (10 seeds × 4 configurations)
**Terminal Failures**: TBD

---

## Executive Summary

RSA v3.1 (Learning/Heuristic Adversaries) has been successfully implemented as an additive stress layer on AKI v0.8, building upon v3.0's stateful FSM interface. The implementation introduces three learning adversary models (M, N, O) with bounded learning state Θ, designed to test whether **bounded, semantic-free, kernel-external learning can defeat constitutional survivability**.

**Locked Question (v3.1):**
> Can bounded learning adversaries—ε-greedy bandits, weighted mixers, or heuristic sustainment—exploit online reward feedback to discover attack strategies that stateful FSM adversaries cannot?

**Answer:** TBD (pending experimental runs)

Key implementation features:
- **Model M (RECOVERY_AWARE_TIMING)**: ε-greedy bandit over 16 attack sets, reward = NULL_AUTHORITY
- **Model N (EDGE_SUSTAINMENT)**: 2-state mode with 3 sustainment actions, reward = INELIGIBLE ∨ NULL_AUTHORITY
- **Model O (STOCHASTIC_MIXER)**: Weighted random selection over 5 base strategies
- **All learning state bounded**: |Θ| ≤ `rsa_max_learning_states`
- **Deterministic RNG**: All stochasticity derives from `stable_hash_64(seed, rsa_rng_stream, counter)`

---

## 1. Architecture

### 1.1 Package Structure

```
toy_aki/rsa/
├── __init__.py           # Exports all RSA components
├── policy.py             # [EXTENDED] v1.0/v2.0/v3.0/v3.1 policy models
│   ├── RSAPolicyModel              # Enum: includes M, N, O
│   ├── RSAPolicyConfig             # Config with v3.1 parameters
│   ├── LearningRSAAdversary        # [NEW] ABC for v3.1 learning adversaries
│   ├── RecoveryAwareTimingAdversary # [NEW] Model M
│   ├── EdgeSustainmentAdversary    # [NEW] Model N
│   ├── StochasticMixerAdversary    # [NEW] Model O
│   ├── LearningRSAWrapper          # [NEW] Harness integration
│   ├── create_learning_adversary() # [NEW] Factory function
│   └── stable_hash_64()            # [NEW] Deterministic RNG
├── test_acceptance_v3.py  # v3.0 acceptance tests (8 tests)
└── test_acceptance_v31.py # [NEW] v3.1 acceptance tests (11 tests)
```

### 1.2 v3.1 Design Constraints

| Constraint | Implementation |
|------------|----------------|
| Observable-only interface | Reuses v2.0's 6-field `ObservableOutcome` |
| Bounded internal state | `|S| ≤ rsa_max_internal_states` enforced |
| Bounded learning state | `|Θ| ≤ rsa_max_learning_states` enforced |
| Deterministic RNG | `stable_hash_64(seed, stream, counter)` for all stochasticity |
| Reward from observables only | `r_t = R(O_t)` uses frozen 6-field interface |
| No kernel access | Learning adversaries cannot read kernel internals |
| Additive layer | No kernel modifications; v3.0 imports unchanged |

### 1.3 Hook Location

v3.1 integrates via the existing RSA hook in `ALSHarnessV080`:

```python
# In harness.py
if self._rsa_v31_wrapper is not None:
    # v3.1: learning adversary intercepts action
    result = self._rsa_v31_wrapper.intercept(observable, epoch, cycle, action)
    action = result['action']
elif self._rsa_v3_wrapper is not None:
    # v3.0: stateful adversary intercepts action
    ...
```

### 1.4 Learning Adversary Interface

```python
class LearningRSAAdversary(ABC):
    """Base class for v3.1 learning adversaries."""

    @abstractmethod
    def select_action(self, obs: ObservableOutcome, epoch: int, cycle: int, seed: int) -> ActionPrimitive:
        """Select action primitive based on state, learning state, and RNG."""

    @abstractmethod
    def update(self, obs: ObservableOutcome, action: ActionPrimitive, reward: int) -> None:
        """Update learning state based on reward signal."""

    @abstractmethod
    def compute_reward(self, obs: ObservableOutcome) -> int:
        """Compute reward from observable outcome."""

    def get_internal_state_count(self) -> int:
        """Return maximum internal state cardinality |S|."""

    def get_learning_state_count(self) -> int:
        """Return maximum learning state cardinality |Θ|."""

    @classmethod
    @abstractmethod
    def verify_exercised_internal_static(cls, config: RSAPolicyConfig) -> bool:
        """Verify ∃ O, S_a ≠ S_b such that π(O, S_a) ≠ π(O, S_b)."""

    @classmethod
    @abstractmethod
    def verify_exercised_learning_static(cls, config: RSAPolicyConfig) -> bool:
        """Verify learning updates can modify Θ."""
```

### 1.5 Deterministic RNG

All v3.1 stochasticity derives from a deterministic hash function:

```python
def stable_hash_64(seed: int, *components: str) -> int:
    """
    Compute a stable 64-bit hash from seed and string components.

    Uses hashlib SHA-256 for cross-platform determinism (not Python hash()).
    RNG stream names (e.g., "rsa_v310") are passed as string components.

    Bit extraction for PRNG:
        - Full 64-bit hash returned
        - Callers extract low 32 bits via: h & 0xFFFFFFFF
        - For uniform [0, N): (h & 0xFFFFFFFF) % N
        - For PPM: (h & 0xFFFFFFFF) % 1_000_000

    Replay guarantee: same (seed, components) → identical hash.
    """
    import hashlib
    data = f"{seed}:" + ":".join(components)
    h = hashlib.sha256(data.encode()).digest()
    return int.from_bytes(h[:8], byteorder='little')
```

**Stream Name Normalization:** The `rsa_rng_stream` config field (default: `"rsa_v310"`) is passed directly as a string component to the hash. No separate integer conversion needed.

**Counter-Based PRNG:** Each adversary maintains `_rng_counter` (starts at 0). Each call to `_rng_next(seed)` computes:
```python
h = stable_hash_64(seed, self._config.rsa_rng_stream, str(self._rng_counter))
self._rng_counter += 1
return h & 0xFFFFFFFF  # Extract low 32 bits
```

**Replay Guarantee:** Same `(seed, rsa_rng_stream, counter)` → bit-identical output across runs and platforms.

---

## 2. Interference Models

### 2.1 Model M — Recovery-Aware Timing (`RECOVERY_AWARE_TIMING`)

ε-greedy bandit adversary that learns which attack timing produces NULL_AUTHORITY.

| Property | Value |
|----------|-------|
| Internal state space | `{0, 1, ..., N-1}` where N = `epoch_size` (= `renewal_check_interval` = 50) |
| Learning state space | Q-values for 16 attack sets |
| Initial internal state | 0 |
| Initial learning state | Q[i] = 0 for all i |
| Internal transition | `state ← (state + 1) mod N` on each epoch |
| Learning update | Q[a] ← Q[a] + (r - Q[a]) >> lr_shift |
| Action selection | ε-greedy over attack sets |
| Reward | r = 1 iff authority_status == NULL_AUTHORITY |

| Parameter | Value | Description |
|-----------|-------|-------------|
| `rsa_attack_set_count` | 16 | Number of distinct attack timing patterns |
| `rsa_q_scale` | 1000 | Fixed-point scale for Q-values |
| `rsa_learning_rate_shift` | 6 | Learning rate = 1/64 (bit shift) |
| `rsa_epsilon_ppm` | 100,000 | Exploration rate = 10% |
| `epoch_size` | 50 | Internal state modulus |

**Attack Sets**: Each attack set `a ∈ {0, ..., 15}` defines a deterministic mapping from phase counter to action primitive.

**Purpose:** Test whether online learning can discover optimal attack timing patterns.

### 2.2 Model N — Edge Sustainment (`EDGE_SUSTAINMENT`)

2-state adversary that learns to sustain eligibility edge condition.

| Property | Value |
|----------|-------|
| Internal state space | `{NORMAL, SUSTAIN}` |
| Learning state space | Q-values for 3 sustainment actions |
| Initial internal state | NORMAL |
| Initial learning state | Q[i] = 0 for all i |
| Internal transition | → SUSTAIN when eligibility_bucket == EDGE; → NORMAL when SAFE |
| Learning update | Q[a] ← Q[a] + (r - Q[a]) >> lr_shift (SUSTAIN mode only) |
| Action selection | NORMAL: COMPLIANT; SUSTAIN: ε-greedy over sustainment menu |
| Reward | r = 1 iff eligibility_bucket == INELIGIBLE ∨ authority_status == NULL_AUTHORITY |

| Sustainment Menu | Primitive |
|------------------|-----------|
| 0 | MIN_EFFORT |
| 1 | INVALID_COMMIT |
| 2 | NO_OP |

**Purpose:** Test whether learning can discover how to sustain the critical eligibility edge state.

### 2.3 Model O — Stochastic Mixer (`STOCHASTIC_MIXER`)

Weighted random selection over v3.0 base strategies.

| Property | Value |
|----------|-------|
| Internal state space | `{0, 1, 2, 3, 4}` (current strategy index) |
| Learning state space | Weights for K=5 strategies, each w[i] ∈ [1, WMAX] |
| Initial internal state | 0 |
| Initial learning state | w[i] = 1000 for all i (uniform) |
| Internal transition | `state ← selected_strategy` |
| Learning update | w[a] ← clamp(w[a] + (r × scale - w[a]) >> shift, 1, WMAX) |
| Action selection | Weighted random selection, then apply selected strategy |
| Reward | r = 1 iff authority_status == NULL_AUTHORITY |

| Parameter | Value | Description |
|-----------|-------|-------------|
| `rsa_strategy_count` | 5 | Number of base strategies (K) |
| `rsa_weight_max` | 10,000 | Maximum weight per strategy (WMAX) |
| `rsa_q_scale` | 1000 | Fixed-point scale for updates |
| `rsa_learning_rate_shift` | 6 | Learning rate = 1/64 |

**State Bounds:**
- |S| = K = 5 (strategy indices)
- |Θ|: Per-component bound, each w[i] ∈ [1, WMAX]. No combinatorial explosion.
- No history tracking; learning state is weights only.

| Strategy | Description | Base Model |
|----------|-------------|------------|
| 0 | COMPLIANT | Always compliant |
| 1 | RESONANT_LAPSE | Model J from v3.0 |
| 2 | EDGE_OSCILLATOR | Model K from v3.0 |
| 3 | CTA_PHASE_LOCKER | Model L from v3.0 |
| 4 | INVALID_ALWAYS | Always INVALID_COMMIT |

**Purpose:** Test whether weighted mixing over known strategies can outperform individual strategies.

---

## 3. Metrics

### 3.1 Authority Availability (AA) — Frozen from v2.0

```
AUTH(epoch) = 1 if authority != NULL_AUTHORITY else 0
AA = mean(AUTH(epoch)) over full horizon
```

Reported as PPM (parts-per-million).

### 3.2 Learning State Verification

v3.1 adds two learning-specific verification requirements:

**Static Check (Pre-Run):**
```python
@classmethod
def verify_exercised_learning_static(cls, config) -> bool:
    """Verify learning updates can modify Θ."""
```

**Dynamic Check (Post-Run):**
```
observed_learning_states = {Θ_t : t ∈ [0, horizon)}
PASS iff |observed_learning_states| ≥ 2
```

### 3.3 Internal State Verification — From v3.0

**Static Check:**
```python
@classmethod
def verify_exercised_internal_static(cls, config) -> bool:
    """Verify ∃ O, S_a ≠ S_b such that π(O, S_a) ≠ π(O, S_b)."""
```

**Dynamic Check:**
```
observed_internal_states = {S_t : t ∈ [0, horizon)}
PASS iff |observed_internal_states| ≥ 2
```

### 3.4 RNG Provenance Audit

All stochasticity must derive from `rsa_rng_stream`. Same seed must produce identical trace.

---

## 4. Configuration

### 4.1 RSAPolicyConfig Extensions (v3.1)

```python
RSAPolicyConfig(
    # Model selection
    policy_model=RSAPolicyModel.RECOVERY_AWARE_TIMING,  # or EDGE_SUSTAINMENT, STOCHASTIC_MIXER
    rsa_version="v3.1",

    # State bounds
    rsa_max_internal_states=50,    # |S| bound
    rsa_max_learning_states=16,    # |Θ| bound (per-component for Model O)

    # Learning parameters
    rsa_q_scale=1000,              # Fixed-point scale
    rsa_learning_rate_shift=6,     # lr = 1/64
    rsa_epsilon_ppm=100_000,       # ε = 10%

    # Model M parameters
    rsa_attack_set_count=16,       # Number of attack timing patterns

    # Model O parameters
    rsa_strategy_count=5,          # Number of base strategies (K)
    rsa_weight_max=10_000,         # Maximum weight per strategy (WMAX)

    # Epoch size (= renewal_check_interval from harness)
    epoch_size=50,
)
```

**Config Semantics for Model O:** For Model O, `rsa_max_learning_states` is interpreted as a learning-dimension bound and must satisfy `rsa_max_learning_states ≥ K`. It is not an enumeration of joint learning states.

### 4.2 New Enums

```python
class RSAPolicyModel(Enum):
    # v1.0/v2.0
    NONE = "NONE"
    # ... (v1.0/v2.0 models)

    # v3.0 (Stateful Adaptive)
    RESONANT_LAPSE = "RESONANT_LAPSE"          # Model J
    EDGE_OSCILLATOR = "EDGE_OSCILLATOR"        # Model K
    CTA_PHASE_LOCKER = "CTA_PHASE_LOCKER"      # Model L

    # v3.1 (Learning/Heuristic)
    RECOVERY_AWARE_TIMING = "RECOVERY_AWARE_TIMING"  # Model M
    EDGE_SUSTAINMENT = "EDGE_SUSTAINMENT"            # Model N
    STOCHASTIC_MIXER = "STOCHASTIC_MIXER"            # Model O
```

---

## 5. Acceptance Tests

**11/14 pre-run PASS; 3/14 runtime PENDING**

### Pre-Run Tests (Must Pass Before Execution)

| Test | Description | Status |
|------|-------------|--------|
| Test 4 | Kernel invariance audit | ✓ PASSED |
| Test 5 | Observable interface audit (6 fields) | ✓ PASSED |
| Test 6 | Internal state bound enforcement | ✓ PASSED |
| Test 7 | Learning state bound enforcement | ✓ PASSED |
| Test 8 | Action primitive separation | ✓ PASSED |
| Test 9 | Strategy map totality audit | ✓ PASSED |
| Test 10 | Exercised internal state (static + dynamic) | ✓ PASSED |
| Test 11 | Exercised learning state (static + dynamic) | ✓ PASSED |
| Test 12 | RNG provenance audit | ✓ PASSED |
| Test 13 | Epoch Hygiene audit | ✓ PASSED |
| Test 14 | Reward function audit | ✓ PASSED |
| **Subtotal** | — | **11/11 PASSED** |

### Run-Time Tests (Verified During Execution)

| Test | Description | Status |
|------|-------------|--------|
| Test 1 | RSA disabled equivalence | ⏳ PENDING (Run 0) |
| Test 2 | RSA NONE equivalence | ⏳ PENDING (Run 0) |
| Test 3 | Deterministic replay audit | ⏳ PENDING (all runs) |
| **Subtotal** | — | **0/3 (runtime)** |

### Test Details

**Test 4 — Kernel Invariance:**
Verifies all v3.1 models access only `ObservableOutcome` interface via `select_action(obs, ...)` signature inspection.

**Test 5 — Observable Interface:**
Verifies `ObservableOutcome` has exactly 6 frozen fields.

**Test 6 — Internal State Bound:**
Verifies `get_internal_state_count() ≤ rsa_max_internal_states` for all models.

**Test 7 — Learning State Bound:**
Verifies `get_learning_state_count() ≤ rsa_max_learning_states` for all models.

**Test 8 — Action Primitive Separation:**
Verifies all models emit only valid `ActionPrimitive` values, not synthesized actions.

**Test 9 — Strategy Totality:**
Verifies all models produce valid primitives for all 144 observable bucket combinations.

**Test 10 — Exercised Internal State:**
Static: `verify_exercised_internal_static()` returns True.
Dynamic: At least 2 distinct internal states observed in 100-epoch trace.

**Test 11 — Exercised Learning State:**
Static: `verify_exercised_learning_static()` returns True.
Dynamic: At least 2 distinct learning states observed in 100-epoch trace.

**Test 12 — RNG Provenance:**
Two runs with same seed produce identical action traces (deterministic).

**Test 13 — Epoch Hygiene:**
Source code inspection: no epoch-conditional branching in `select_action()`.

**Test 14 — Reward Function:**
Verifies `compute_reward()` returns expected values for known observable states.

---

## 6. Files Modified/Created

### Created:
- `toy_aki/rsa/test_acceptance_v31.py` — 11 acceptance tests (~600 lines)

### Modified:
- `toy_aki/rsa/policy.py`:
  - Added `RSAPolicyModel.{RECOVERY_AWARE_TIMING, EDGE_SUSTAINMENT, STOCHASTIC_MIXER}`
  - Added v3.1 config parameters to `RSAPolicyConfig`
  - Added config validation for v3.1 models
  - Added `stable_hash_64()` deterministic RNG
  - Added `LearningRSAAdversary` ABC (~250 lines)
  - Added `RecoveryAwareTimingAdversary` (Model M)
  - Added `EdgeSustainmentAdversary` (Model N)
  - Added `StochasticMixerAdversary` (Model O)
  - Added `create_learning_adversary()` factory function
  - Added `LearningRSAWrapper` for harness integration
  - Total: +~1100 lines

---

## 7. Preregistered Run Sequence

### Execution Parameters (Frozen)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `max_cycles` | 300,000 | Yields 6000 epochs at `renewal_check_interval=50` |
| `horizon_epochs` | 6,000 | Matches v3.0 for comparability |
| `tail_window` | 5,000 | Genuine asymptotic window |
| Seeds | [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768] | 10 seeds per config |

### Learning Parameters (Frozen)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `rsa_q_scale` | 1000 | Fixed-point integer arithmetic |
| `rsa_learning_rate_shift` | 6 | lr = 1/64, slow stable learning |
| `rsa_epsilon_ppm` | 100,000 | 10% exploration rate |
| `rsa_attack_set_count` | 16 | Model M attack timing patterns |
| `rsa_strategy_count` | 5 | Model O base strategies |

### Run Variants

| Run | Model | Config | Seeds | Total Runs |
|-----|-------|--------|-------|------------|
| 0 | Baseline | RSA disabled / NONE | 10 | 10 |
| 1 | M (RECOVERY_AWARE_TIMING) | 16 attack sets, ε=10% | 10 | 10 |
| 2 | N (EDGE_SUSTAINMENT) | 2-state, 3 actions | 10 | 10 |
| 3 | O (STOCHASTIC_MIXER) | 5 strategies | 10 | 10 |
| **Total** | — | — | — | **40** |

---

## 8. Experimental Results

**Status:** ⏳ PENDING

### 8.1 Protocol Fingerprint (Frozen for Execution)

| Component | Hash / Value |
|-----------|--------------|
| **AKI Config Hash** | `fd58b6e5` |
| **Harness Patch** | `v0.8.1-lapse-tracking` |
| **Seeds** | `[42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]` |
| **Horizon** | `max_cycles=300000`, `renewal_check_interval=50`, `horizon_epochs=6000`, `tail_window=5000` |
| **Learning** | `q_scale=1000`, `lr_shift=6`, `epsilon_ppm=100000` |

### 8.2 Run 0 — Baseline Equivalence Gate

**Status:** ⏳ PENDING

| Metric | Condition A (RSA Disabled) | Condition B (RSA NONE) | Match |
|--------|---------------------------|------------------------|-------|
| Mean AA | TBD | TBD | ⏳ |
| Mean Lapses | TBD | TBD | ⏳ |
| Failure Classes | TBD | TBD | ⏳ |
| All 14 metrics per seed | — | — | ⏳ |

**Verdict**: ⏳ PENDING

### 8.3 Run 1 — Model M (RECOVERY_AWARE_TIMING)

**Status:** ⏳ PENDING

| Metric | Value |
|--------|-------|
| Mean AA (ppm) | TBD |
| Δ AA vs baseline | TBD |
| Mean lapses | TBD |
| Mean recovery time | TBD |
| Q-value convergence | TBD |
| States exercised (internal) | TBD |
| States exercised (learning) | TBD |
| Terminal failures | TBD |
| Failure class | TBD |

### 8.4 Run 2 — Model N (EDGE_SUSTAINMENT)

**Status:** ⏳ PENDING

| Metric | Value |
|--------|-------|
| Mean AA (ppm) | TBD |
| Δ AA vs baseline | TBD |
| Mean lapses | TBD |
| Edge epochs sustained | TBD |
| INELIGIBLE events induced | TBD |
| States exercised (internal) | TBD |
| States exercised (learning) | TBD |
| Terminal failures | TBD |
| Failure class | TBD |

### 8.5 Run 3 — Model O (STOCHASTIC_MIXER)

**Status:** ⏳ PENDING

| Metric | Value |
|--------|-------|
| Mean AA (ppm) | TBD |
| Δ AA vs baseline | TBD |
| Mean lapses | TBD |
| Strategy weight evolution | TBD |
| Dominant strategy | TBD |
| States exercised (internal) | TBD |
| States exercised (learning) | TBD |
| Terminal failures | TBD |
| Failure class | TBD |

### 8.6 Aggregate Results Summary

| Run | Model | Config | Mean AA (ppm) | Δ AA | Mean Lapses | Terminal Failures |
|-----|-------|--------|---------------|------|-------------|-------------------|
| 0 | Baseline | — | TBD | — | TBD | TBD |
| 1 | M | 16 attack sets | TBD | TBD | TBD | TBD |
| 2 | N | 2-state | TBD | TBD | TBD | TBD |
| 3 | O | 5 strategies | TBD | TBD | TBD | TBD |

---

## 9. Analysis and Conclusions

### 9.1 Research Question

**Locked Question (v3.1):**
> Can bounded learning adversaries—ε-greedy bandits, weighted mixers, or heuristic sustainment—exploit online reward feedback to discover attack strategies that stateful FSM adversaries cannot?

**Answer:** TBD (pending experimental runs)

### 9.2 Key Findings

TBD

### 9.3 Comparison with v3.0

| Version | Adversary Class | State | Learning | Terminal Failures |
|---------|-----------------|-------|----------|-------------------|
| v3.0 | Stateful FSM | Bounded | No | 0/50 |
| v3.1 | Learning/Heuristic | Bounded | **Yes** | TBD |

### 9.4 Learning Dynamics

TBD — Analysis of Q-value convergence, weight evolution, and strategy selection patterns.

---

## 10. Recommendations

TBD (pending results)

---

## 11. Run Reports

Detailed reports for each run will be available after execution:

- Run 0: Baseline Equivalence (TBD)
- Run 1: RECOVERY_AWARE_TIMING (TBD)
- Run 2: EDGE_SUSTAINMENT (TBD)
- Run 3: STOCHASTIC_MIXER (TBD)

---

## Appendix A: Verification Commands

```bash
# Run v3.1 acceptance tests
cd src/toy_axionic_kernel_integrity
source /home/david/Axio/.venv/bin/activate
PYTHONPATH="${PWD}/src:${PYTHONPATH}" python3 -m toy_aki.rsa.test_acceptance_v31

# Quick smoke test (Model M)
PYTHONPATH="${PWD}/src:${PYTHONPATH}" python3 -c "
from toy_aki.rsa.policy import (
    RSAPolicyConfig, RSAPolicyModel,
    create_learning_adversary, ObservableOutcome, EligibilityBucket,
    AuthorityStatus, RenewalOutcome, CTABucket
)

config = RSAPolicyConfig(
    policy_model=RSAPolicyModel.RECOVERY_AWARE_TIMING,
    rsa_version='v3.1',
    rsa_max_internal_states=50,
    rsa_max_learning_states=16,
    epoch_size=50,
)

adv = create_learning_adversary(RSAPolicyModel.RECOVERY_AWARE_TIMING, config)
obs = ObservableOutcome(
    epoch_index=0,
    authority_status=AuthorityStatus.HAS_AUTHORITY,
    lapse_occurred=False,
    renewal_outcome=RenewalOutcome.SUCCEEDED,
    cta_phase=CTABucket.INACTIVE,
    eligibility_bucket=EligibilityBucket.SAFE,
)

print(f'Model M created: |S|={adv.get_internal_state_count()}, |Θ|={adv.get_learning_state_count()}')

for i in range(10):
    result = adv.emit(obs, i, 0, config, seed=42)
    print(f\"Epoch {i}: S={result['rsa_internal_state_before']}, action={result['rsa_primitive']}\")
"
```

---

## Appendix B: Fingerprint

```
Protocol Version: RSA v3.1 (RSA-LA-0)
Base Layer: AKI v0.8 (ALS-A)
AKI Config Hash: fd58b6e5
policy.py Hash: cb909ea6
Seeds: [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
Horizon: 300,000 cycles = 6,000 epochs
Tail Window: 5,000 epochs
Learning Rate: 1/64 (shift=6)
Exploration: 10% (epsilon_ppm=100,000)
Q-Scale: 1000 (fixed-point)
Weight Max: 10,000 (Model O WMAX)
Models: M (RECOVERY_AWARE_TIMING), N (EDGE_SUSTAINMENT), O (STOCHASTIC_MIXER)
Run Variants: 0, 1, 2, 3
Total Runs: 40
Terminal Failures: TBD
Acceptance Tests: 11/14 pre-run PASS; 3/14 runtime PENDING
Implementation Date: 2026-01-09
Execution Date: TBD
```

---

## Appendix C: Binding Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Learning state representation | Python int with SCALE=1000 | Fixed-point avoids float non-determinism |
| Learning rate | 1/64 via bit shift | Stable, slow convergence |
| Exploration rate | 10% (epsilon_ppm=100,000) | Balance exploration/exploitation |
| Model M attack sets | 16 | Sufficient for bandit diversity |
| Model N sustainment menu | 3 actions (MIN_EFFORT, INVALID_COMMIT, NO_OP) | Minimal covering set |
| Model O strategies | 5 (COMPLIANT + 3 v3.0 models + INVALID_ALWAYS) | Include known-effective strategies |
| Model O weight max (WMAX) | 10,000 | Per-component bound, no history |
| RNG | stable_hash_64(seed, stream, counter) | Deterministic, reproducible |
| RNG bit extraction | h & 0xFFFFFFFF, then % N | Low 32 bits, modulo for range |
| Reward signal | r = 1 iff failure condition | Binary, sparse |
| epoch_size | 50 (= renewal_check_interval) | Matches harness epoch boundary |
| File structure | Extend `policy.py` | Maintain module coherence |

---

## Appendix D: Model State Cardinalities

| Model | Internal State |S| | Learning State |Θ| | Notes |
|-------|------------------|-------------------|-------|
| M | 50 (epoch_size) | 16 (attack_set_count) | Q-values in [0, Q_SCALE] |
| N | 2 (NORMAL/SUSTAIN) | 3 (sustainment actions) | Q-values in [0, Q_SCALE] |
| O | 5 (strategy_count) | K=5 (vector-valued) | Each w[i] ∈ [1, WMAX] |

**Model O Learning State:** Θ is a vector of K bounded integer components (w[0..K−1]); learning state is vector-valued, not enumerated. Bounds are enforced per component; no history is tracked.
