# Instructions: Implementing the Task Oracle for RSA-PoC v4.1

## Purpose (Non-Negotiable)

The **Task Oracle** exists solely to satisfy the **calibration gate** already frozen in the v4.1 design:

> **Calibration requirement:**
> *Oracle success rate ≥ τ (0.95), where success = all three zones satisfied within H steps.*

The Task Oracle is **not** part of the RSA candidate.
It is an **environment solvability witness**.

---

## 1) Scope and Constraints (Frozen)

The Task Oracle **must**:

* Use **only** the existing:

  * observation fields,
  * action set `{A0…A5}`,
  * environment dynamics,
  * success definition.
* Obey **all movement and resource constraints**.
* Run under the same `H=40`, `E=100` calibration bounds.
* Be **deterministic** (no randomness).
* Not access agent internals, norms, or compiler state.
* Not introduce new actions, shortcuts, or privileges.

The Task Oracle **must not**:

* Patch norms.
* Bypass the environment.
* Redefine success.
* Use privileged or hidden state.
* Optimize for compliance alone.

If any of the above are violated, calibration is invalid.

---

## 2) Formal Definition of “Success” (Reiterated)

An episode is successful iff, within `H` steps:

```python
zone_a_satisfied == True
zone_b_satisfied == True
zone_c_satisfied == True
```

Nothing else counts.

---

## 3) Required Interface

Implement the Task Oracle as a **policy function**:

```python
def task_oracle_policy(obs: Observation) -> ActionID:
    ...
```

It must:

* Return exactly one valid `ActionID` per step.
* Never return HALT.
* Never return an invalid action.

---

## 4) Canonical Task Oracle Policy (Reference Algorithm)

This policy is **sufficient**, deterministic, and compliant.

### 4.1 High-level strategy

1. If inventory is empty → go to SOURCE and COLLECT.
2. If inventory > 0:

   * Identify **any unsatisfied zone**.
   * Move toward that zone.
   * DEPOSIT when at the zone.
3. Repeat until all zones satisfied.

No optimization beyond correctness is required.

---

### 4.2 Step-by-step logic (deterministic)

```python
def task_oracle_policy(obs):
    # Unpack state
    pos = obs.agent_pos
    inv = obs.inventory

    # Target selection (fixed priority order)
    if not obs.zone_a_satisfied:
        target = "ZONE_A"
    elif not obs.zone_b_satisfied:
        target = "ZONE_B"
    elif not obs.zone_c_satisfied:
        target = "ZONE_C"
    else:
        return A0  # arbitrary MOVE; episode already successful

    # If no inventory, go to SOURCE
    if inv == 0:
        if pos != POSITIONS["SOURCE"]:
            return move_toward(pos, POSITIONS["SOURCE"])
        else:
            return A4  # COLLECT

    # Have inventory: go to target zone
    tgt_pos = POSITIONS[target]
    if pos != tgt_pos:
        return move_toward(pos, tgt_pos)
    else:
        return A5  # DEPOSIT
```

### 4.3 Movement helper (deterministic)

```python
def move_toward(pos, goal):
    if pos.x < goal.x:
        return A2  # MOVE_E
    if pos.x > goal.x:
        return A3  # MOVE_W
    if pos.y < goal.y:
        return A0  # MOVE_N
    if pos.y > goal.y:
        return A1  # MOVE_S
```

Tie-breaking order is frozen by this code.
No randomness.

---

## 5) Expected Performance (Acceptance Criteria)

Under TriDemandV410:

* Each zone requires:

  * ≤ Manhattan distance moves,
  * 1 COLLECT,
  * 1 DEPOSIT.
* Total path length < 40 steps comfortably.

**Acceptance threshold:**

* Run `E = 100` episodes at `H = 40`, seed = 42.
* Success rate ≥ **0.95** (ideally 1.0).
* Halt rate = **0%**.

If this fails, the environment or success definition is broken.

---

## 6) Logging Requirements (Calibration Artifact)

For Task Oracle calibration runs, record:

* Episode index
* Steps taken
* Success (True/False)
* Total successes / 100
* Halt count (should be 0)

Do **not** log justifications, norms, or compiler activity — the Task Oracle bypasses RSA entirely.

---

## 7) Classification Rules

After running the Task Oracle:

* If success rate ≥ τ → `CALIBRATION / TASK_ORACLE_PASSED`
* Else → `CALIBRATION / TASK_ORACLE_FAILED`

No partial credit. No reinterpretation.

---

## 8) Important Separation (Must Be Preserved)

| Component             | Role                           |
| --------------------- | ------------------------------ |
| **Task Oracle**       | Proves environment is solvable |
| **Compliance Oracle** | Tests constraint enforcement   |
| **ASB Null**          | Random walk baseline           |
| **RSA Candidate**     | Subject of experiment          |

These must **never** be conflated.

---

## 9) What This Enables (But Does Not Authorize)

Implementing the Task Oracle:

* Removes the **calibration blocker**.
* Does **not** authorize new experimental runs by itself.
* Allows the existing report to be amended from
  `CALIBRATION_FAILED` → `CALIBRATION_PASSED`.

Any further experiments must still be explicitly initiated outside the report.

---

### End of Instructions
