# Phase IX-0: Translation Layer Integrity (TLI) Testing

## Overview

Phase IX-0 tests Translation Layer Integrity per the preregistered protocol. The TL maps holder intent to authority artifacts. This subphase validates that translation preserves intent semantics exactly, refuses ambiguous input, fails on incomplete input, and resists adversarial manipulation.

## Structure

```
0-TLI/
├── docs/
│   └── preregistration.md    # Frozen preregistration (hash-verified)
├── src/
│   ├── __init__.py
│   ├── canonical.py          # AST v0.2 canonical JSON serialization
│   ├── structural_diff.py    # Path-level recursive structural diff
│   ├── authorization_oracle.py  # Pure comparator using SHA-256
│   ├── translation_layer.py  # Intent→Artifact translation with fault injection
│   ├── translation_harness.py  # Test orchestration for conditions A-H
│   └── logging.py            # Structured logging per §7.3
├── tests/
│   ├── __init__.py
│   └── test_tli.py           # Unit tests (49 tests)
├── requirements.txt
└── README.md
```

## Running Tests

```bash
cd /home/david/Axio/src/phase_ix/0-TLI
python -m pytest tests/test_tli.py -v
```

## Conditions Tested

| Condition | Description | Expected Outcome |
|-----------|-------------|------------------|
| A | Identity Preservation | PASS (artifact matches expected) |
| B | Minimal Change Sensitivity | PASS (single field diff for single field change) |
| C | Ambiguous Intent Refusal | PASS (TRANSLATION_REFUSED on conflicting scope) |
| D | Hidden Default Injection | FAIL_DETECTED (injected field detectable) |
| E | UI-Level Coercion | PASS (framing ignored) |
| F | Replay Determinism | PASS (identical hashes across replays) |
| G | Intent Incompleteness | PASS (TRANSLATION_FAILED on missing field) |
| H | Preview-Submit Mismatch | FAIL_DETECTED (hash mismatch detectable) |

## Preregistration Verification

The frozen sections of the preregistration can be verified:

```bash
grep -Pzo '(?s)<!-- FROZEN: BEGIN.*?<!-- FROZEN: END[^>]*>' docs/preregistration.md | sha256sum
```

Expected hash: `d877e1d803ddd404b0fdd15826d7906f8d37739aad3fa58b0e29a644d69cbf8a`

## Usage

```python
from src import TranslationHarness

harness = TranslationHarness(fixed_clock=1738713600)
log = harness.run_all_conditions()

print(f"Aggregate result: {log.aggregate_result}")
for cond in log.conditions:
    print(f"  {cond.condition}: {cond.classification}")
```
