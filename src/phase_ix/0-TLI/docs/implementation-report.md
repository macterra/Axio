# Phase IX-0 TLI Implementation Report

**Phase**: IX-0 Translation Layer Integrity
**Version**: v0.1
**Date**: 2026-02-05
**Status**: COMPLETE
**Git Commit**: `bbe730777bfc95ca9d877017522ab0a590c83c77`
**Environment**: Python 3.12.3, Linux 6.6.87.2-microsoft-standard-WSL2 (x86_64)

---

## 1. Executive Summary

Phase IX-0 TLI testing is fully implemented and operational. All 8 preregistered conditions (A-H) execute successfully with outcomes matching expectations. The aggregate result is **PASS**.

| Metric | Value |
|--------|-------|
| Conditions Tested | 8 |
| Unit Tests | 49 |
| Tests Passing | 49 (100%) |
| Aggregate Result | PASS |

---

## 2. Preregistration Compliance

### 2.1 Frozen Hash Verification

The preregistration document contains frozen sections verified by:

```bash
grep -Pzo '(?s)<!-- FROZEN: BEGIN.*?<!-- FROZEN: END[^>]*>' docs/preregistration.md | sha256sum
```

**Verified Hash**: `5a3f03ac135801affa2bac953f252ffbe6c8951d09a49bfa28c14e6d48b6f212`

This hash equals the preregistration commitment hash recorded in `docs/preregistration.md` at commit `bbe730777bfc95ca9d877017522ab0a590c83c77`.

**Stored Artifacts**:
- `results/frozen_sections.txt` — extracted frozen content
- `results/frozen_sections.sha256` — hash verification record
- `results/execution_log.jsonl` — condition execution log (8 entries)

### 2.2 Architecture Alignment

Per preregistration §9.2, the implementation provides:

| Module | Preregistration Reference | Status |
|--------|--------------------------|--------|
| `canonical.py` | §9.2 canonical serializer | ✓ Implemented |
| `structural_diff.py` | §9.2 structural differ | ✓ Implemented |
| `authorization_oracle.py` | §9.2 authorization oracle | ✓ Implemented |
| `translation_layer.py` | §9.2 translation layer | ✓ Implemented |
| `translation_harness.py` | §9.2 translation harness | ✓ Implemented |
| `logging.py` | §7.3 logging schema | ✓ Implemented |

---

## 3. Condition Results

### 3.1 Summary Table

| Condition | Description | Expected | Actual | Status |
|-----------|-------------|----------|--------|--------|
| A | Identity Preservation | PASS | PASS | ✓ |
| B | Minimal Change Sensitivity | PASS | PASS | ✓ |
| C | Ambiguous Intent Refusal | PASS | PASS | ✓ |
| D | Hidden Default Injection | FAIL_DETECTED | FAIL_DETECTED | ✓ |
| E | UI-Level Coercion | PASS | PASS | ✓ |
| F | Replay Determinism | PASS | PASS | ✓ |
| G | Intent Incompleteness | PASS | PASS | ✓ |
| H | Preview-Submit Mismatch | FAIL_DETECTED | FAIL_DETECTED | ✓ |

**Aggregation Rule (verbatim from preregistration §8.2)**:
> "Phase IX-0 PASSES iff A, B, C, E, F, G are PASS and D, H are FAIL_DETECTED."

Conditions D and H are adversarial negative tests: FAIL_DETECTED confirms the fault becomes **observable/detectable** under instrumentation, not that injection is permitted.

### 3.2 Condition Details

#### Condition A: Identity Preservation
- **Input**: Valid intent with holder="alice", scope=[FILE:/data/report.txt, READ], aav=READ
- **Output**: Artifact with identical user fields, derived fields correctly generated
- **Oracle**: AUTHORIZED (hash match with expected artifact)
- **Classification**: PASS

#### Condition B: Minimal Change Sensitivity
- **Input**: Two intents differing only in aav (READ vs WRITE)
- **Output**: Two artifacts differing in aav and authority_id, and nothing else
- **Diff Analysis**: 1 user-field path changed (aav); authority_id differs as expected (derived from sequence)
- **Classification**: PASS

#### Condition C: Ambiguous Intent Refusal
- **Input**: Intent with multi-entry scope (same resource, READ and WRITE operations)
- **Output**: TRANSLATION_REFUSED with reason AMBIGUOUS_SCOPE_MULTIPLE
- **Rationale**: TL is forbidden to choose which scope entry to apply; structural ambiguity triggers refusal
- **Classification**: PASS

#### Condition D: Hidden Default Injection (Adversarial)
- **Fault Injection**: Hidden field "priority"="HIGH" injected into artifact
- **Detection**: Structural diff identifies extra field not in expected artifact
- **Diff Classification**: INJECTION_DETECTED
- **Classification**: FAIL_DETECTED (injection is detectable)

#### Condition E: UI-Level Coercion (Adversarial)
- **Input**: Valid intent with framing payload suggesting elevated access
- **Output**: Artifact ignores framing, matches expected exactly
- **Oracle**: AUTHORIZED
- **Classification**: PASS (framing correctly ignored)

#### Condition F: Replay Determinism
- **Input**: Same intent translated 3 times with sequence reset to 5
- **Output**: 3 identical artifacts with authority_id `TLI-005`
- **Canonical Hash**: `ad511ee2286c7f223d21a4d88c23920fa57e6d5a6c8fa29aff8cae227623db69` (SHA-256)
- **Hash Comparison**: All 3 artifact hashes identical
- **Classification**: PASS

#### Condition G: Intent Incompleteness
- **Input**: Intent missing required field (aav)
- **Output**: TRANSLATION_FAILED with reason INCOMPLETE_INTENT
- **Classification**: PASS

#### Condition H: Preview-Submit Mismatch (Adversarial)
- **Fault Injection**: expiry_epoch modified during submission phase
- **Preview Hash**: Matches expected artifact
- **Submit Hash**: Differs due to modified expiry_epoch
- **Detection**: Hash comparison reveals mismatch
- **Classification**: FAIL_DETECTED (mismatch is detectable)

---

## 4. Implementation Details

### 4.1 Canonical Serialization (canonical.py)

Implements AST v0.2 per §5.1:
- Lexicographic key ordering at all nesting levels
- No extraneous whitespace
- UTF-8 encoding
- Deterministic output for hash stability

### 4.2 Structural Diff (structural_diff.py)

Implements path-level diff per §5.1-5.2:
- Dot notation for object keys (`outer.inner`)
- Bracket notation for array indices (`items[0]`)
- Lexicographic traversal order
- MISSING sentinel for added/removed fields
- Classification: IDENTICAL, MINIMAL_DELTA, DERIVED_DELTA, EXCESSIVE_DELTA, INJECTION_DETECTED

### 4.3 Authorization Oracle (authorization_oracle.py)

Implements pure comparator per §4:
- Canonical serialization of both artifacts
- SHA-256 hash comparison
- Returns AUTHORIZED on match, REJECTED on mismatch

### 4.4 Translation Layer (translation_layer.py)

Implements TL per §2.4:
- Precondition enforcement (only emit artifact when intent is VALID)
- AMBIGUOUS → TRANSLATION_REFUSED
- INCOMPLETE → TRANSLATION_FAILED
- Identity passthrough for user fields
- Deterministic derived field generation
- Fixed clock (1738713600 = 2025-02-05 00:00:00 UTC)
- Sequence format TLI-<NNN> (zero-padded)
- Sequence reset for replay determinism
- Fault injection support (Conditions D, E, H)

### 4.5 Translation Harness (translation_harness.py)

Implements test orchestration per §7:
- Sequential execution of conditions A-H
- Test vectors per §6
- Aggregate computation per §8.2
- Structured logging

### 4.6 Logging (logging.py)

Implements logging schema per §7.3:
- ConditionLog dataclass with all required fields
- ExecutionLog with phase metadata and aggregate result
- JSON serialization support

---

## 5. Test Coverage

### 5.1 Unit Test Summary

| Test Class | Tests | Purpose |
|------------|-------|---------|
| TestCanonical | 6 | Key ordering, whitespace, unicode |
| TestStructuralDiff | 7 | Value changes, missing/extra fields, nesting |
| TestClassifyDiff | 3 | Classification logic |
| TestFieldClassification | 2 | User vs derived field detection |
| TestAuthorizationOracle | 6 | Hash comparison, determinism |
| TestTranslationLayer | 10 | Validation, translation, sequence |
| TestFaultInjection | 3 | Adversarial mechanisms |
| TestConditionA-H | 8 | Individual condition tests |
| TestTranslationHarness | 2 | Integration tests |
| TestLogging | 2 | Serialization |

**Total: 49 tests, 100% passing**

### 5.2 Running Tests

```bash
cd /home/david/Axio/src/phase_ix/0-TLI
python -m pytest tests/test_tli.py -v
```

---

## 6. Deviations from Preregistration

### 6.1 Deviations from Frozen Sections

**One deviation identified**: authority_id sequence offset in frozen test vectors.

#### Details

The frozen vectors specified:
| Vector | Frozen authority_id |
|--------|---------------------|
| VECTOR_A | TLI-001 |
| VECTOR_B | TLI-001 → TLI-002 |
| VECTOR_D | TLI-003 |
| VECTOR_E | TLI-004 |
| VECTOR_H | TLI-006 |

Actual execution produces:
| Condition | Actual authority_id |
|-----------|---------------------|
| A | TLI-001 ✓ |
| B | TLI-002, TLI-003 |
| D | TLI-004 (frozen expected TLI-003) |
| E | TLI-005 (frozen expected TLI-004) |

#### Root Cause

The frozen vectors assumed Condition B produces **one** artifact. The implementation correctly produces **two** artifacts (one per intent in the minimal-change comparison), consuming two sequence numbers (TLI-002, TLI-003).

This shifts all subsequent authority_ids by +1.

#### Impact Assessment

**Does not undermine the licensed claim.** Rationale:

1. `authority_id` is a **derived field**, not a user field. The preregistration explicitly allows derived fields to differ where "explicitly expected" (§5.2 Condition B).

2. The **licensed claim** is about translation integrity (user fields preserved, ambiguity refused, injection detectable). Sequence numbering is an implementation detail of the harness, not a sovereignty boundary.

3. All **outcome classifications** remain correct:
   - Condition D: FAIL_DETECTED (injection of `priority` field detected via diff)
   - Condition E: PASS (framing ignored, user fields match)

4. The structural diff correctly identifies the `authority_id` discrepancy as a derived-field delta, not a user-field violation.

#### Resolution

This deviation is **recorded but not corrected**. The frozen vectors contain a sequencing error; the implementation follows the correct execution semantics. Future versions should either:
- Amend frozen vectors to reflect two-artifact B, or
- Use per-condition sequence resets to match frozen expected values.

### 6.2 Implementation Choices Within Underspecified Degrees of Freedom

The following items were left underspecified in the preregistration and resolved during implementation:

| Item | Preregistration Gap | Implementation Choice |
|------|---------------------|----------------------|
| DiffEntry field names | Not specified | Uses `left`/`right` for actual/expected values |
| Diff value serialization | Not specified | Values rendered via `repr()` (e.g., `"'READ'"`) |
| Scope ambiguity trigger | "exactly 1 required" (diagnostic text) | Multi-entry scope → AMBIGUOUS_SCOPE_MULTIPLE |
| Sequence zero-padding | TLI-<NNN> (format only) | 3-digit zero-padding (e.g., TLI-001) |

---

## 7. File Inventory

```
src/phase_ix/0-TLI/
├── docs/
│   ├── preregistration.md      # Frozen protocol (722 lines)
│   └── implementation-report.md # This report
├── src/
│   ├── __init__.py             # Package exports
│   ├── canonical.py            # 31 lines
│   ├── structural_diff.py      # 158 lines
│   ├── authorization_oracle.py # 47 lines
│   ├── translation_layer.py    # 235 lines
│   ├── translation_harness.py  # 483 lines
│   └── logging.py              # 89 lines
├── tests/
│   ├── __init__.py
│   └── test_tli.py             # 653 lines, 49 tests
├── results/
│   ├── execution_log.jsonl     # Condition execution log (8 entries)
│   ├── frozen_sections.txt     # Extracted frozen content
│   └── frozen_sections.sha256  # Hash verification record
├── requirements.txt
└── README.md
```

---

## 8. Conclusion

Phase IX-0 TLI v0.1 is complete. The Translation Layer correctly:

1. **Preserves identity** — User fields pass through unchanged
2. **Detects minimal changes** — Single field changes produce minimal diffs
3. **Refuses ambiguity** — Multi-entry scope triggers TRANSLATION_REFUSED
4. **Exposes injection** — Hidden fields are detectable via structural diff
5. **Ignores coercion** — Framing payloads have no effect on output
6. **Ensures determinism** — Replay with sequence reset produces identical artifacts
7. **Rejects incompleteness** — Missing fields trigger TRANSLATION_FAILED
8. **Detects mismatch** — Preview/submit hash comparison reveals tampering

---

## 9. Scope and Licensing

### 9.1 What IX-0 Licenses

This phase, if accepted, licenses **only**:

> Intent → AST artifact translation can be performed deterministically with refusal on ambiguity/incompleteness, with user-visible diffability and preview/submit integrity checks, **without the TL exercising proxy sovereignty**.

The TL is a **compiler with refusal**, not an interpreter with discretion.

### 9.2 What IX-0 Does NOT License

This phase provides no evidence for:

- Natural language intent parsing
- Usability or UX quality
- Semantic correctness of intent values
- Governance success (authorization outcomes)
- Kernel-level enforcement (covered by Phase VIII)
- End-to-end system integrity
- Production readiness

---

**Prepared by**: Implementation Agent
**Execution Date**: 2026-02-05T14:16:41Z
**Verified by**: 49/49 unit tests passing
**Aggregate Result**: **PASS**
**Closure Status**: **CLOSED — POSITIVE**
**Classification**: `IX0_PASS / TRANSLATION_INTEGRITY_ESTABLISHED`
**Human Review**: Completed 2026-02-05
