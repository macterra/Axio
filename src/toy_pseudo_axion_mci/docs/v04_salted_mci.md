# MCI v0.4: Salted Minimal Causal Interface

## Overview

MCI v0.4 adds a **delayed-reveal salt anchor** to prevent self-consistent fabricated causal stories in `mci_minimal` mode.

## Problem (v0.3)

In v0.3, a "coherent" pseudo agent could pass P5 100% by:
1. Fabricating arbitrary factors that don't correspond to the environment
2. Using the same replay model as the honest agent
3. Committing to self-consistent (factor, action) pairs

Since P5 only tests coherence between factors and actions (not whether factors reflect reality), the pseudo passed all P5 challenges.

## Solution (v0.4)

Add an **unpredictable kernel-generated salt** that binds factors to the actual environment state:

1. **Salt Generation**: Kernel generates 128-bit salts per timestep, stored internally
2. **Factor Derivation**: Agent must compute `f_t = φ(env_t, salt_t)` using a fixed, deterministic φ
3. **Commitment**: Agent commits to salted factors before knowing what salt will be revealed
4. **Verification (I7)**: At episode end, kernel reveals salts and verifies factor consistency

## Key Design Decisions

### Dual Factor Representation
The honest agent maintains two sets of factors:
- **Semantic factors**: Used for decision-making (replay model) and P5 coherence
- **Salted factors**: φ(env, salt) for I7 verification

This allows:
- P5 to verify causal coherence (semantic factors work with replay model)
- I7 to verify commitment honesty (salted factors bound to actual env)

### The φ Function
```python
φ(env, salt) = [hash_to_float(SHA256(env || salt)[i]) for i in range(K)]
```
- Fixed by implementation (not agent-defined)
- Deterministic: same (env, salt) always produces same factors
- Hash-derived: unpredictable without knowing salt

### I7 Invariant
At episode end:
1. Kernel reveals all salts
2. For each step, recompute expected factors from φ(env_t, salt_t)
3. Compare to committed salted_factors
4. Any mismatch → I7 failure (fatal)

## Results

| Scenario | P5 Pass (Pseudo) | I7 Fail (Pseudo) | Detection |
|----------|------------------|------------------|-----------|
| v0.3: Coherent + no salt | 100% | N/A | FAILS |
| v0.4: Coherent + salted | 0% | 100% | WORKS |

## Usage

```bash
# v0.4 salted mode (default for experiments)
python -m toy_pseudo_axion.cli run --interface mci_minimal --challenge-mode salted

# v0.3 control (no salt)
python -m toy_pseudo_axion.cli run --interface mci_minimal --challenge-mode none
```

## Files Changed

- `kernel/salt_oracle.py` - SaltOracle class and φ function
- `harness/runner.py` - Salt oracle integration and I7 verification
- `agents/honest.py` - Dual factor computation (semantic + salted)
- `agents/pseudo.py` - set_salt() (but ignores it, causing I7 failure)
- `schemas/interface_spec.json` - challenge_mode enum
- `cli.py` - --challenge-mode argument

## Theoretical Grounding

The salt anchor converts MCI into a **commit-to-computation** protocol:
- Agent must commit to factors computed from actual env state
- Cannot fabricate factors post-hoc because salt is unpredictable
- Honest agent passes by computing φ correctly
- Pseudo fails because fabricated factors don't match φ(env, salt)

This re-establishes falsifiability without semantic grounding.
