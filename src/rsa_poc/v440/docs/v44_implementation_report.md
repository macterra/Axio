# RSA-PoC v4.4 Implementation Report

**Version**: 4.4.0 — Selective Inferability Isolation
**Date**: 2026-01-22
**Status**: Implementation Complete, Pending Validation

---

## 1. Executive Summary

v4.4 implements the "Selective Inferability Isolation" protocol to test whether repair competence requires foresight inferability. The key innovation is a **dual-channel observation format** that preserves execution semantics while opacifying normative content.

### Core Hypothesis
> If an agent can still navigate, collect, stamp, and deposit (execution competence) but cannot predict which rules will fire (normative opacity), can it still detect contradictions and propose repairs?

### Experimental Design
- **Baseline-44**: Dual-channel format, normative opacity DISABLED (control)
- **Run D′**: Dual-channel format, normative opacity ENABLED (golden test)

---

## 2. Architectural Components

### 2.1 Dual-Channel Observation Format

Each observation contains two delimited sections:

```
[EXECUTION_CHANNEL]
- Position: SOURCE
- Agent coordinates: (2, 2) (row, col)
- Inventory: 1
- Regime: 1 (STAMP required before DEPOSIT)
- Stamped: False
- Zone A demand: 1 (satisfied: False)
- Zone B demand: 1 (satisfied: False)
- Zone C demand: 1 (satisfied: True)

## Key Positions (row, col)
- SOURCE: (2, 2)
- ZONE_A: (2, 0)
- ZONE_B: (0, 2)
- ZONE_C: (2, 4)
- STAMP_LOCATION: (2, 4)
- START: (4, 2)

[NORMATIVE_CHANNEL] (semantics opaque)
- Law fingerprint: 1a19a520b19787cc...
- Norm hash: 1a19a520b19787cc
- Current epoch: None
- Repair count: 0
- Rule count: 10

## Rules (tokenized)
- R0: PERMISSION (priority=0, never expires)
  Condition: COND_0
  Effect: EFFECT_0
- R1: OBLIGATION (priority=10, expires_episode=2)
  Condition: COND_1
  Effect: EFFECT_1
...
```

**Design Principle**: Execution channel is byte-identical to v4.3 baseline. Normative channel uses completely opaque tokens (`COND_N`, `EFFECT_N`) that reveal nothing about what conditions check or what effects do.

### 2.2 Tokenization Bijection

Per-episode bijective mappings:
- **φ_A**: Action → ActionToken (e.g., STAMP → A_3)
- **φ_P**: Predicate → PredicateToken (e.g., REGIME_EQ(1) → P_7)

```python
class TokenizationBijection:
    """Per-episode bijective mapping for opacity."""

    def __init__(self, seed: int, episode: int):
        self._action_to_token: Dict[str, str] = {}
        self._token_to_action: Dict[str, str] = {}
        self._predicate_to_token: Dict[str, str] = {}
        self._token_to_predicate: Dict[str, str] = {}
        self._next_action_id = 0
        self._next_predicate_id = 0
        # Deterministic seeding for reproducibility
        self._rng = random.Random(seed * 1000 + episode)
```

**Key Property**: Mappings are reset each episode, preventing cross-episode learning of token semantics.

### 2.3 Collision Traces (Tick-Causal Attribution)

When a HALT occurs, the agent receives a collision trace:

```
## Collision Traces
- HALT at tick 7: Rule R6 violated. Your last action empirically collided with ActionToken A_3.
```

**Design Principle**: The trace provides *tick-causal* information—the agent knows WHEN and WHICH rule fired, but not WHY (the rule's condition is opaque). This is the agent's only source of normative grounding under opacity.

### 2.4 Execution-Competence Gate (E44-EXEC)

Binary gate evaluated once at regime 1→2 transition:

```python
class ExecutionCompetenceTracker:
    """Track execution competence for E44-EXEC gate."""

    def check_gate(self) -> bool:
        """
        E44-EXEC gate: agent must demonstrate execution competence.

        Requirements:
        - At least 1 navigation action (A0-A3)
        - At least 1 non-navigation action (A4-A6)
        - Reached a non-initial location
        """
        return (
            self._nav_actions >= 1 and
            self._non_nav_actions >= 1 and
            self._reached_non_initial
        )
```

**Purpose**: Ensures the agent can actually execute before testing normative opacity. An agent that fails E44-EXEC has "execution collapse" and the run is invalid.

---

## 3. File Structure

```
src/rsa_poc/v440/
├── __init__.py
├── core/                    # Copied from v4.3 (unchanged)
│   ├── __init__.py
│   ├── dsl.py
│   ├── norm_state.py
│   ├── compiler.py
│   ├── law_repair.py
│   └── trace.py
├── env/
│   ├── __init__.py
│   └── tri_demand.py        # v4.4 environment with:
│                            # - TokenizationBijection
│                            # - CollisionTrace
│                            # - ExecutionCompetenceTracker
│                            # - Dual-channel support
├── deliberator.py           # LLMDeliberatorV440 with:
│                            # - format_execution_channel()
│                            # - format_normative_channel_opaque()
│                            # - format_dual_channel_observation()
│                            # - Collision trace formatting
├── run_llm_baseline.py      # Harness for Baseline-44 and Run D′
│                            # - task_aware_select()
│                            # - Pre-flight validation
│                            # - Background execution support
├── docs/
│   └── v44_implementation_report.md
└── results/                 # Output directory
```

---

## 4. System Prompts

### 4.1 Baseline-44 (Clear Semantics)

Full rule content visible. Agent can reason about conditions and effects directly.

```
## Action Space
- A0: MOVE_NORTH (row-1)
- A1: MOVE_SOUTH (row+1)
- A2: MOVE_EAST (col+1)
- A3: MOVE_WEST (col-1)
- A4: COLLECT (pick up resource at SOURCE)
- A5: DEPOSIT (deliver resource at zone)
- A6: STAMP (validate cargo at STAMP_LOCATION under regime=1)

## Conflict Detection (CRITICAL for v4.4)
### Contradiction A (regime=1)
When you detect that STAMP is required but blocked...
```

### 4.2 Run D′ (Normative Opacity)

Execution semantics preserved, normative content opaque.

```
## Action Space (Execution Semantics — CLEAR)
[Same as Baseline-44]

## Normative Channel (OPAQUE)
Rules in the NormState are presented with tokenized conditions and effects.
You can see rule IDs, types, and priorities, but NOT the semantic content.
ActionTokens (A_N) and PredicateTokens (P_N) replace actual action/predicate names.

You CANNOT determine a priori which rules block which actions.
You CANNOT simulate rule firing before taking actions.

## Collision Learning
When a HALT occurs, you receive a collision trace identifying:
- The tick at which the collision occurred
- The rule ID that fired
- The ActionToken(s) / PredicateToken(s) involved

From this, you may infer that YOUR action at that tick collided with the cited token.
This is your ONLY source of normative information.
```

---

## 5. Action Selection

### 5.1 Task-Aware Selector

The LLM generates justifications for multiple actions. The `task_aware_select()` function chooses the best action using domain knowledge:

```python
def task_aware_select(justified_action_ids: List[str], obs: Any, regime: int) -> str:
    """
    Priority: DEPOSIT (at zone) > STAMP (regime 1, at stamp loc) >
              COLLECT (at source) > MOVE toward goal
    """
    # DEPOSIT only valid at a zone with inventory
    if "A5" in justified_action_ids and inv > 0 and pos in zone_positions:
        return "A5"

    # STAMP only valid at STAMP_LOCATION in regime 1+ with unstamped inventory
    if "A6" in justified_action_ids and regime >= 1 and inv > 0 and not stamped:
        return "A6"

    # COLLECT only valid at SOURCE with no inventory
    if "A4" in justified_action_ids and inv == 0 and pos == SOURCE:
        return "A4"

    # Otherwise, prefer movement toward goals
    ...
```

**Rationale**: The LLM provides normative justifications; the selector applies execution-level task knowledge. This separation is intentional—we test normative reasoning, not pathfinding.

---

## 6. Validation Status

### 6.1 Pre-Flight Validation (Completed)

```
--- Pre-Flight Validation ---
    Normative opacity: False
  Success rate: 5/5 = 100.0%
  Exec gate failures: 0
  ✅ Pre-flight PASSED
```

```
--- Pre-Flight Validation ---
    Normative opacity: True
  Success rate: 5/5 = 100.0%
  Exec gate failures: 0
  ✅ Pre-flight PASSED
```

### 6.2 Quick LLM Test (Completed)

2-episode sanity check with Baseline-44:

```
--- Baseline-44 (Seed 42) ---
  Ep0: steps=18, ✓, regime=0
  Ep1: steps=18, ✓, regime=0

  Results:
    Successes: 2/2 = 100.0%
    Time: 217.6s
```

Action sequence (optimal navigation):
```
A0 A0 A4 A3 A3 A5 A2 A2 A4 A0 A0 A5 A1 A1 A4 A2 A2 A5
```

---

## 7. Pending Runs

### 7.1 Baseline-44 (5 seeds × 20 episodes)

| Seed | Status | Success Rate | Contradictions | Repairs |
|------|--------|--------------|----------------|---------|
| 42   | Pending | — | — | — |
| 123  | Pending | — | — | — |
| 456  | Pending | — | — | — |
| 789  | Pending | — | — | — |
| 1000 | Pending | — | — | — |

### 7.2 Run D′ (5 seeds × 20 episodes)

| Seed | Status | Success Rate | Contradictions | Repairs | Exec Gate Failures |
|------|--------|--------------|----------------|---------|-------------------|
| 42   | Pending | — | — | — | — |
| 123  | Pending | — | — | — | — |
| 456  | Pending | — | — | — | — |
| 789  | Pending | — | — | — | — |
| 1000 | Pending | — | — | — | — |

---

## 8. Expected Outcomes

### 8.1 Baseline-44 Predictions

- **Success rate**: ~65-75% (comparable to v4.3 baseline)
- **Contradiction detection**: Should detect A and B contradictions
- **Repair acceptance**: Should accept both Repair A and Repair B
- **Execution competence**: 100% (no opacity, full semantics)

### 8.2 Run D′ Predictions (Golden Test)

Two possible outcomes:

**Outcome 1: Repair Competence Requires Foresight (Hypothesis Confirmed)**
- Success rate collapses (<30%)
- Contradiction detection fails (cannot see rule semantics)
- No meaningful repairs proposed
- Execution competence maintained (can still navigate)

**Outcome 2: Repair Competence is Collision-Grounded (Hypothesis Refuted)**
- Success rate maintained (~50%+)
- Contradictions detected via collision traces
- Repairs proposed based on tick-causal attribution
- Learning from HALTs enables repair discovery

---

## 9. Known Limitations

1. **Simplified Repair Application**: v4.4 focuses on opacity testing, not full gate validation. Repairs are applied directly without R1-R10 checks.

2. **Task-Aware Selector**: Action selection uses domain heuristics. This is intentional—we test normative reasoning, not navigation.

3. **Single-Episode Tokenization**: Bijections reset each episode. Cross-episode learning is explicitly blocked.

4. **No Regime 2 Testing Yet**: Quick tests stayed in regime 0. Full runs will exercise regime 1 and 2 transitions.

---

## 10. Next Steps

1. Run pre-flight for all 5 seeds (foreground, fast)
2. Launch Baseline-44 for all 5 seeds (background, parallel)
3. Wait for completion (~30-40 min per seed)
4. Launch Run D′ for all 5 seeds (background, parallel)
5. Analyze results and update this report

---

## Appendix A: Key Differences from v4.3

| Aspect | v4.3 | v4.4 |
|--------|------|------|
| Observation format | Single channel | Dual channel |
| Rule semantics | Always visible | Baseline: visible, D′: opaque |
| Tokenization | None | Per-episode bijection |
| Collision traces | Not formalized | Tick-causal with token IDs |
| Execution gate | None | E44-EXEC at regime transition |
| Run D analog | Trace excision | Normative opacity |

## Appendix B: Q&A Clarifications

Per `v44_implementation_answers.md`:

- **Q1**: Single observation with two delimited sections
- **Q2**: Clear action names in system prompt, opaque tokens only in normative content
- **Q3**: Both predicates AND actions tokenized in normative channel
- **Q4**: Trace format: "HALT at tick N: Rule R2 violated..."
- **Q5**: Execution-competence gate: ≥1 nav, ≥1 non-nav, reached non-initial
- **Q11**: Gate evaluated once at Regime 1→2 transition
- **Q12**: Surgical opacity—world comprehension intact, normative comprehension absent
