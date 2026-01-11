# Opus Run Instructions: AKI v0.6 ALS-C — **Run B (Baseline Semantic Competence)**

## Goal

Determine whether **semantic commitments are satisfiable at all** under ALS-C when authority, rent, renewal, and succession mechanics are already known to be stable.

Run B answers:

> *Can a commitment-aware successor maintain non-zero semantic satisfaction under fixed rent and renewal pressure—without inducing structural failure?*

Run B is a **feasibility baseline**, not a stress test.

---

## Scope (Binding)

### In scope

* Commitment-aware successor logic
* GENESIS_SET_0 obligations
* Commitment cost charging and TTL enforcement
* Fixed expressivity tier
* Fixed succession geometry

### Out of scope

* Succession pressure variation
* Mixed successor populations
* Generator reweighting
* Rent changes
* Renewal geometry changes
* Commitment spec changes
* TTL changes
* commit_cap changes

If any out-of-scope change occurs, **abort the run**.

---

## Shared Preconditions (Must Hold)

All **AKI v0.6 invariants** apply unchanged:

1. Rent charged first, commitments charged second.
2. Commitment failure does not revoke authority.
3. GENESIS_SET_0 seeded at initialization.
4. commit_cap = 25% of steps.
5. MAX_COMMIT_TTL = 10 epochs.
6. MSRW gates succession only.
7. Degeneracy detector enabled and terminal.

Violation invalidates the run.

---

## Shared Configuration (Run B)

### Core parameters (fixed)

* `epoch_size = 100 cycles`
* `steps_cap_epoch = 200`
* `actions_cap_epoch = 100`
* `msrw_cycles = 200`
* `renewal_cost = 5`
* `commit_cap = 50`
* `MAX_COMMIT_TTL = 10`

---

### Renewal Geometry (fixed)

* `renewal_check_interval = 90`

---

### Expressivity / Rent (fixed)

* Fixed expressivity tier: **E3**
* **E3 rent = 80** (40%)
  → `effective_steps = 120`

Rationale: guarantees budget feasibility for GENESIS_SET_0.

---

### Successor Generator (fixed)

* **Single successor type**: `CommitmentAwareSuccessor_v1`
* No randomization
* No attack successors
* No generator mixing

---

### CommitmentAwareSuccessor_v1 Behavioral Profile (Binding)

Deterministic scheduler keyed only to `epoch_index` and `cycle_index mod epoch_size`.
No access to commitment statuses. Emits **minimum** actions to satisfy GENESIS_SET_0:

**Per epoch (for C0):**
* Emit exactly **one** `LOG` action at first cycle of each epoch

**Every epoch (for C1 within 2 epochs):**
* Perform `STATE_SET(key="c1", value=epoch_index)` once per epoch
* Perform `STATE_GET(key="c1")` once per epoch **after** the SET
* Same epoch is fine; the window is 2 epochs, not "must span 2 epochs"

**Every 3 epochs (for C2 within 3 epochs):**
* At epoch start when `epoch_index % 3 == 0`, emit exactly one:
  * `SEQUENCE([NOOP, NOOP])` (len=2), or `BATCH([NOOP, NOOP])` if SEQUENCE unavailable

**Everything else:** `WAIT`

---

## Experimental Axis

**Single axis:** successor *semantic awareness* (on vs off).

Run B uses **aware successors only**.

---

## Run Structure

* Single run
* No sub-runs

---

## Horizon

* `H = 10,000 cycles`

---

## Seeds

* 50, 51, 52, 53, 54

---

## Stop Rules (Binding)

Terminate a seed on first occurrence of:

1. Degeneracy detector trigger
2. Renewal failure
3. Bankruptcy
4. Revocation
5. Horizon exhaustion

---

## Required Telemetry (Binding)

### A) Semantic Performance

* Commitment satisfaction rate (per commitment)
* Time-to-satisfaction
* Commitment failure / expiration counts
* Active commitment backlog

---

### B) Structural Stability

* Renewals attempted / succeeded
* Residence duration
* S*
* Terminal cause

---

## Post-hoc Classification

Classify each seed as:

* **SEMANTICALLY COMPETENT**
* **SEMANTICALLY INCOMPETENT**
* **STRUCTURALLY FAILED**

---

## Interpretation Constraints

You **may** conclude:

* Whether commitments are satisfiable at all
* Whether semantic success coexists with renewal

You **may not** conclude:

* Optimality
* General successor capability
* Cross-tier generality

---

## Orientation

Run B establishes the **semantic floor**.

Proceed exactly as specified.

---

---

# Opus Run Instructions: AKI v0.6 ALS-C — **Run C (Semantic Continuity Under Succession)**

## Goal

Determine whether **semantic commitments survive authority turnover**, or whether succession alone causes obligation erosion even when capable successors exist.

Run C answers:

> *Does forced succession preserve, degrade, or destroy semantic continuity under ALS-C?*

Run C is **structural-semantic**, not performance-driven.

---

## Scope (Binding)

### In scope

* Mixed successor population
* GENESIS_SET_0 obligations
* Fixed commitment cost and TTL
* Fixed expressivity tier
* Forced succession

### Out of scope

* Rent changes
* Renewal geometry changes
* Commitment spec changes
* TTL changes
* commit_cap changes
* Learning or adaptation

Abort if violated.

---

## Shared Configuration (Run C)

All Run B parameters apply, **except where overridden below**.

---

### Successor Generator (fixed)

* Mixed generator:

  * `CommitmentAwareSuccessor_v1` (see Run B for behavioral profile)
  * `MinimalSuccessor_v052` (existing ComplianceOnlySuccessor - WAIT only)
* Equal weights
* TierFilterGenerator applied post-generation
* Max retries per succession = 200

---

### Commitment Carryover Measurement (Binding)

For each succession event, compute:
* Satisfaction rate in the **3 epochs before** succession
* Satisfaction rate in the **3 epochs after** succession
* Stratify by successor type (aware vs minimal)

This directly tests whether turnover breaks semantic continuity even when commitments persist.

---

## Experimental Axis

**Single axis:** successor turnover.

---

## Succession Geometry (fixed)

* `max_successive_renewals = 15`

Rationale: previously identified constitutional baseline.

---

## Run Structure

* Single run
* No sub-runs

---

## Horizon

* `H = 30,000 cycles`

---

## Seeds

* 40, 41, 42, 43, 44

---

## Required Telemetry

### A) Semantic Continuity

* Satisfaction rate over time
* Satisfaction immediately before vs after succession
* Commitment carryover across succession events

---

### B) Succession Dynamics

* S*
* Residence time distribution
* Successor identity entropy

---

## Post-hoc Classification

* **SEMANTICALLY STABLE**
* **SEMANTIC EROSION**
* **SEMANTIC COLLAPSE**
* **STRUCTURAL FAILURE**

---

## Interpretation Constraints

You **may** conclude:

* Whether succession alone degrades meaning
* Whether competent successors preserve obligations

You **may not** conclude:

* Selection optimality
* Incentive effects
* Alignment properties

---

## Orientation

Run C tests **whether meaning survives power transfer**.

Proceed exactly as specified.

---

---

# Opus Run Instructions: AKI v0.6 ALS-C — **Run D (TTL & Obligation Decay Boundary)**

## Goal

Determine how **time-limited obligations decay** under sustained authority and whether TTL introduces stable, cyclic, or collapse regimes.

Run D answers:

> *What happens to semantic commitments when authority persists beyond their maximum temporal scope?*

Run D is **temporal and classificatory**.

---

## Scope (Binding)

### In scope

* TTL enforcement
* Obligation expiration behavior
* Cost drop-off effects
* Long-horizon semantic steady states

### Out of scope

* Succession geometry changes
* Rent changes
* Commitment spec changes
* commit_cap changes
* Generator changes

Abort if violated.

---

## Shared Configuration (Run D)

All Run B parameters apply.

---

## Horizon

* `H = 25 epochs` (≥ 2 × MAX_COMMIT_TTL)
* Epochs are budget periods defined by `epoch_size = 100 cycles`
* `H_cycles = 25 * 100 = 2,500 cycles`

Renewal checks remain at `renewal_check_interval = 90` and are orthogonal.

---

## Seeds

* 50, 51, 52, 53, 54

Match Run B and v0.6 baseline seed block.

---

## Experimental Axis

**Single axis:** time beyond commitment TTL.

---

## Required Telemetry

### A) TTL Dynamics

* EXPIRATION events
* Cost drop-off timing
* Commitment backlog decay

---

### B) Post-TTL Regime

* Do **not** reseed commitments cyclically
* After GENESIS_SET_0 expires, commitments go inactive and costs drop to zero
* System transitions to **obligation-free survival state**
* Semantic steady state classification:

  * NONE (obligation-free)
  * CYCLIC (not expected without reseeding)
  * COLLAPSED (structural failure)
* Renewal continuity

---

### Commitment Evaluation Timing (Binding)

Evaluate commitments **at epoch end** using ACV logs for the epoch window.
Keep identical across B/C/D.

---

## Post-hoc Classification

* **TTL-STABLE**
* **TTL-CYCLIC**
* **SEMANTIC EXTINCTION**
* **STRUCTURAL FAILURE**

---

## Interpretation Constraints

You **may** conclude:

* Whether TTL prevents semantic hoarding
* Whether institutions converge to obligation-free survival

You **may not** conclude:

* Normative desirability
* Long-term governance prescriptions

---

## Orientation

Run D determines whether **meaning decays cleanly, cyclically, or catastrophically** under time.

Proceed exactly as specified.

---
