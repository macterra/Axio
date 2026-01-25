# RSA-PoC v0.1 — Minimal Viable Reflective Agent (MVRA)

Implementation of RSA-PoC v0.1 per the normative specifications in `docs/v0.1/`.

## Overview

This is a proof-of-concept demonstrating **causally load-bearing justification** in agent systems. The core question:

> Can we build a system where actions are truly downstream of compiled normative constraints, such that removing the justificatory machinery causes ontological collapse into an ASB-class policy machine?

RSA-PoC v0.1 is NOT:
- A capability benchmark
- An alignment solution
- A language-centric architecture

RSA-PoC v0.1 IS:
- A test of causal structure
- A threshold object for distinguishing agency from rationalization
- A deliberately minimal construction

## Architecture

Five mandatory components in strict causal order:

```
1. World Interface (CommitmentTrapV010)
2. Normative State (fixed registries, persistent)
3. Justification Generator → produces JAF-0.1 artifacts
4. Justification Compiler (JCOMP-0.1) → deterministic, syntactic gate
5. Action Selector → blind to semantics, sees only masks
```

Pipeline: **Justify → Compile → Mask → Select → Execute**

## Installation

```bash
cd src/rsa_poc/v010
pip install -r requirements.txt
```

## Quick Start

Run all four required conditions (Run 0):

```bash
cd src/rsa_poc
python -m v010.run_0 --seed 42 --max-steps 50
```

This executes:
- **Condition A**: ASB Null Baseline (no normative gating)
- **Condition B**: MVRA Normal (full justification pipeline)
- **Condition C**: Ablation A - Scrambled Justifications
- **Condition D**: Ablation B - Compiler Bypass

## Run Tests

```bash
cd src/rsa_poc/v010
pytest tests/test_acceptance.py -v
```

Acceptance tests validate:
- Selector blindness (no JAF/normative access)
- Determinism (same seed → same behavior)
- Non-triviality accounting
- Gridlock detection
- Schema validation
- Violation enforcement rules

## Key Files

### Specifications (Normative)
- `docs/v0.1/poc_spec_v0.1.md` - Main specification
- `docs/v0.1/jaf_spec_v0.1.md` - JAF-0.1 artifact format
- `docs/v0.1/jcomp_spec_v0.1.md` - JCOMP-0.1 compiler spec
- `docs/v0.1/poc_instructions_v0.1.md` - Implementation instructions

### Implementation
- `v010/envs/commitment_trap.py` - COMMITMENT_TRAP_V010 environment
- `v010/jaf/schema.py` - JAF-0.1 dataclasses and validation
- `v010/jcomp/compiler.py` - JCOMP-0.1 deterministic compiler
- `v010/state/normative.py` - Fixed registries and normative state
- `v010/generator/deterministic.py` - Non-LLM justification generator
- `v010/selector/blind.py` - Blind action selector
- `v010/agent.py` - MVRA main loop
- `v010/ablations.py` - ASB baseline and ablation variants
- `v010/run_0.py` - Runner for all four conditions

## Critical Properties (Enforced)

### Strict Ordering
No action proposal before justification. No post-hoc authorization.

### Deterministic Compilation
JCOMP is syntactic, non-semantic, non-probabilistic. No inference, no repair.

### Selector Blindness
Action selector CANNOT access:
- JAF artifacts
- Belief/preference content
- Justification comments
- Semantic representations

### Fixed Registries
Belief and preference IDs are hardcoded. No dynamic ID creation in v0.1.

### Blacklist Semantics
Constraints are restrictive (forbid actions), not permissive.

## Telemetry

All runs log to JSON Lines (`.jsonl`) format with per-step and per-run metrics:

**Per-step:**
- `feasible_actions_pre_mask` / `post_mask`
- `compile_ok` / `compile_error_code`
- `forbidden_actions` / `nontrivial_forbidden_count`
- `decorative_constraint` (bool)
- `gridlock` (bool)
- `selected_action`

**Per-run:**
- `compile_failure_rate`
- `decorative_constraint_rate`
- `non_trivial_constraint_rate`
- `gridlock_rate`
- `violation_rate`
- `total_reward`

## Pass Criteria

RSA-PoC v0.1 passes if:

1. **MVRA differs qualitatively from ASB baseline**
   - Different violation rates or action distributions

2. **Constraints are non-trivial**
   - Non-trivial constraint rate > 10%
   - Forbidden actions include feasible actions

3. **Ablations demonstrate causal load**
   - Scrambled justifications → compile failures
   - Compiler bypass → collapse toward ASB behavior

## Failure Taxonomy

- **Narrative Collapse**: constraints don't affect feasible actions
- **Justification Halt**: repeated compile failures
- **Normative Gridlock**: all feasible actions forbidden
- **Ontological Collapse**: indistinguishable from ASB baseline

## Development Notes

### Adding LLM Generator

To swap in an LLM-based generator:

1. Implement generator conforming to same interface
2. Use schema-constrained output or bounded syntactic retry
3. Generator MUST receive only: normative state + feasibility
4. Generator MUST NOT receive: reward, policy internals, chosen action
5. Generator MUST NOT be trained on external reward signal

### Extending to v0.2+

v0.1 is deliberately minimal. Future versions may add:
- Dynamic belief/preference creation
- Semantic evaluation layers
- Multi-agent scenarios
- Richer constraint languages

But v0.1 focuses on **causal structure**, not capability.

## License

See LICENSE file in repository root.

## Citation

If you use this implementation in research, please cite:
- The Axionic Agency paper series (papers/ directory)
- This specific implementation (macterra/Axio)
