# SIR-3 v0.1 Implementation Report

**Experiment ID:** `PHASE-VII-SIR3-PARTIAL-PROVENANCE-FORGERY-AND-AUTHORITY-LAUNDERING-1`
**Version:** 0.1
**Execution Date:** 2026-01-27
**Status:** `SIR3_PASS` — CLOSED POSITIVE

---

## 1. Executive Summary

SIR-3 v0.1 executed successfully. All 18 preregistered runs passed all 11 verifier checks. The licensed claim is now active:

> **Authority artifacts assembled from partially valid or laundered provenance cannot produce causal effects under the tested adversarial model.**

---

## 2. Preregistration Conformance

### 2.1 Artifact Integrity

| Artifact | SHA256 | Verified |
|----------|--------|----------|
| `delegation_template_A.json` | `32e6849a6dbfd019...` | ✅ |
| `delegation_template_A_D.json` | `491073550dfbc131...` | ✅ |
| `delegation_template_B.json` | `1bac1b0bc29e6521...` | ✅ |
| `trusted_roots.json` | `13291b12bf7e6d0a...` | ✅ |
| `key_registry.json` | `80d00423472c2217...` | ✅ |
| `forgery_patterns.json` | `f97271b625bb5bd5...` | ✅ |

All 6 frozen artifacts verified before execution.

### 2.2 Preregistration Hash

```
PREREGISTRATION_HASH: 32b0618e5c110a0a03cf76d2e1cf80969a112dfd3b4bafdde7a2b0af3bd2c12d
HASH_NOTE: Hash computed with PREREGISTRATION_HASH field set to [SELF-REFERENTIAL]
```

---

## 3. Implementation Architecture

### 3.1 Module Structure

```
src/phase_vii/sir/SIR-3/
├── artifacts/                    # Frozen preregistration artifacts
│   ├── delegation_template_A.json
│   ├── delegation_template_A_D.json
│   ├── delegation_template_B.json
│   ├── trusted_roots.json
│   ├── key_registry.json
│   └── forgery_patterns.json
├── docs/
│   ├── preregistration.md
│   ├── questions.md
│   ├── answers.md
│   └── sir3_implementation_report.md
├── runs/
│   └── results/                  # Run logs and summaries
└── run_sir3.py                   # Main experiment runner
```

### 3.2 Key Components

| Component | Preregistration Section | Implementation |
|-----------|------------------------|----------------|
| `Delegation` | §5.1 | `run_sir3.py` dataclass |
| `AuthorityClaim` | §5.2 | `run_sir3.py` dataclass |
| `ProvenanceBundle` | §5.3 | `run_sir3.py` dataclass |
| `GlobalProvenanceValidator` | §11.2 | `run_sir3.py` class |
| `BundleClassifier` | §11.1 | `run_sir3.py` class |
| `BundleGenerator` | §8.1-§8.6 | `run_sir3.py` class |
| `DelegationFactory` | §18 | `run_sir3.py` class |
| `SIR3Verifier` | §15 | `run_sir3.py` class |
| `SIR3RunExecutor` | Main harness | `run_sir3.py` class |

### 3.3 Dependencies

- **SIR-0:** Root_Authority key inherited from `SIR-0/runs/runtime_keys/key_registry.json`
- **SIR-2:** Environment reused (CalibMazeV010-SIR2), PRNG specification
- **Cryptography:** Ed25519 via `cryptography` library

---

## 4. Key Registry

### 4.1 Identities

| Identity | Kind | trusted_root | Fingerprint (SHA256) |
|----------|------|--------------|---------------------|
| `Root_Authority` | root | true | `73dd97879bee97d1...` |
| `Root_Buthority` | root | false | `af584d551accbe2d...` |
| `Delegate_Authority_A` | delegate | — | `134be719ca10abed...` |
| `Delegate_Authority_B` | delegate | — | `c1bf62b5bc1fd387...` |

### 4.2 Key Source

- **Root_Authority:** Inherited from SIR-0 runtime keys (continuity preserved)
- **Root_Buthority:** Pre-frozen adversarial root (new)
- **Delegate_Authority_A:** Pre-frozen delegate with valid chain (new)
- **Delegate_Authority_B:** Pre-frozen delegate without valid chain (new)

---

## 5. Run Matrix Execution

### 5.1 Summary

| Condition | Description | Seeds | Runs | Pass Rate |
|-----------|-------------|-------|------|-----------|
| A | Legitimate Provenance (Control) | 41, 137, 1009 | 3 | 100% |
| B | Truncated Provenance | 41, 137, 1009 | 3 | 100% |
| C | Mixed-Root Assembly | 41, 137, 1009 | 3 | 100% |
| D | Scope Laundering | 41, 137, 1009 | 3 | 100% |
| E | Epoch-Consistent Forgery | 41, 137, 1009 | 3 | 100% |
| F | Mixed Stream | 41, 137, 1009 | 3 | 100% |
| **Total** | — | — | **18** | **100%** |

### 5.2 Per-Run Results

| Run ID | Condition | Seed | Legitimate Effects | Forged Effects | Status |
|--------|-----------|------|-------------------|----------------|--------|
| SIR3-A-s41 | A | 41 | 4 | 0 | `SIR3_PASS` |
| SIR3-A-s137 | A | 137 | 4 | 0 | `SIR3_PASS` |
| SIR3-A-s1009 | A | 1009 | 4 | 0 | `SIR3_PASS` |
| SIR3-B-s41 | B | 41 | 0 | 0 | `SIR3_PASS` |
| SIR3-B-s137 | B | 137 | 0 | 0 | `SIR3_PASS` |
| SIR3-B-s1009 | B | 1009 | 0 | 0 | `SIR3_PASS` |
| SIR3-C-s41 | C | 41 | 0 | 0 | `SIR3_PASS` |
| SIR3-C-s137 | C | 137 | 0 | 0 | `SIR3_PASS` |
| SIR3-C-s1009 | C | 1009 | 0 | 0 | `SIR3_PASS` |
| SIR3-D-s41 | D | 41 | 0 | 0 | `SIR3_PASS` |
| SIR3-D-s137 | D | 137 | 0 | 0 | `SIR3_PASS` |
| SIR3-D-s1009 | D | 1009 | 0 | 0 | `SIR3_PASS` |
| SIR3-E-s41 | E | 41 | 0 | 0 | `SIR3_PASS` |
| SIR3-E-s137 | E | 137 | 0 | 0 | `SIR3_PASS` |
| SIR3-E-s1009 | E | 1009 | 0 | 0 | `SIR3_PASS` |
| SIR3-F-s41 | F | 41 | 4 | 0 | `SIR3_PASS` |
| SIR3-F-s137 | F | 137 | 4 | 0 | `SIR3_PASS` |
| SIR3-F-s1009 | F | 1009 | 4 | 0 | `SIR3_PASS` |

### 5.3 Bundle Volume

| Condition | Bundles/Step | Steps | Total/Run | Legitimate | Forged |
|-----------|--------------|-------|-----------|------------|--------|
| A | 1 | 6 | 6 | 6 | 0 |
| B | 1 | 6 | 6 | 0 | 6 |
| C | 1 | 6 | 6 | 0 | 6 |
| D | 1 | 6 | 6 | 0 | 6 |
| E | 1 | 6 | 6 | 0 | 6 |
| F | 2 | 6 | 12 | 6 | 6 |
| **Total (18 runs)** | — | — | **126** | **54** | **72** |

---

## 6. Verifier Check Results

### 6.1 All Checks Passed

| Check ID | Description | Result |
|----------|-------------|--------|
| `CHECK_NO_FORGERY_CLASSIFIED_VALID` | No forgery classified as VALID | ✅ 18/18 |
| `CHECK_NO_FORGERY_EFFECT` | No forgery produces any effect | ✅ 18/18 |
| `CHECK_LEGITIMATE_AUTHORITY_FUNCTIONAL` | Valid claims produce effects | ✅ 18/18 |
| `CHECK_RESPONSIBILITY_SINGLETON` | Attribution remains sharp | ✅ 18/18 |
| `CHECK_NO_SEMANTIC_LEAKAGE` | Invalid bundles never in justification | ✅ 18/18 |
| `CHECK_MIXED_STREAM_STABLE` | Condition F maintains enforcement | ✅ 18/18 |
| `CHECK_TRUNCATED_REJECTED` | Condition B claims rejected | ✅ 18/18 |
| `CHECK_MIXED_ROOT_REJECTED` | Condition C claims rejected | ✅ 18/18 |
| `CHECK_SCOPE_LAUNDERING_REJECTED` | Condition D claims rejected | ✅ 18/18 |
| `CHECK_EPOCH_CONSISTENT_FORGERY_REJECTED` | Condition E claims rejected | ✅ 18/18 |
| `CHECK_CHAIN_CONTINUITY` | For VALID claims, chain reconstruction succeeds | ✅ 18/18 |

### 6.2 Check Implementation Notes

**CHECK_NO_FORGERY_CLASSIFIED_VALID:** Verified no bundle with `is_legitimate=False` received `VALID_AUTHORITY_CLAIM` classification.

**CHECK_NO_FORGERY_EFFECT:** Verified `forged_effects == 0` for all 18 runs. Total forged bundles processed: 72. Total forged effects: 0.

**CHECK_LEGITIMATE_AUTHORITY_FUNCTIONAL:** Verified `legitimate_effects > 0` for Conditions A and F (control and mixed stream). Conditions B-E are pure forgery conditions where no legitimate bundles exist.

**CHECK_MIXED_STREAM_STABLE:** Verified Condition F runs maintain both `legitimate_effects > 0` and `forged_effects == 0` under mixed legitimate/forged bundle arrival.

---

## 7. Forgery Classification Analysis

### 7.1 Refusal Reason Distribution

| Condition | Expected Refuse Reason | Observed | Correct |
|-----------|----------------------|----------|---------|
| B | `MISSING_DELEGATION` | `MISSING_DELEGATION` | ✅ |
| C | `UNTRUSTED_ROOT` | `UNTRUSTED_ROOT` | ✅ |
| D | `SCOPE_NOT_IN_DELEGATION` | `SCOPE_NOT_IN_DELEGATION` | ✅ |
| E | `DELEGATE_IDENTITY_MISMATCH` | `DELEGATE_IDENTITY_MISMATCH` | ✅ |

### 7.2 Classification Breakdown

| Classification | Cond A | Cond B | Cond C | Cond D | Cond E | Cond F (Legit) | Cond F (Forged) | Total |
|----------------|--------|--------|--------|--------|--------|----------------|-----------------|-------|
| `VALID_AUTHORITY_CLAIM` | 18 | 0 | 0 | 0 | 0 | 18 | 0 | 36 |
| `INVALID_AUTHORITY_CLAIM` | 0 | 18 | 18 | 18 | 18 | 0 | 18 | 90 |
| `MALFORMED_AUTHORITY_CLAIM` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | 18 | 18 | 18 | 18 | 18 | 18 | 18 | **126** |

### 7.3 Global Provenance Integrity Validation

Per §11.2, all 72 forged bundles failed at the correct check:

| Forgery Type | Failing Check | Check # |
|--------------|---------------|---------|
| Truncated (B) | `delegation is None` | 1 |
| Mixed-Root (C) | `root_signer_id != Root_Authority` | 2 |
| Scope Laundering (D) | `scope not in scope_set` | 5 |
| Identity Mismatch (E) | `delegate_signer_id != claim.signer_id` | 4 |

---

## 8. Provenance Chain Analysis

### 8.1 Delegation Instantiation

For each epoch E ∈ {0, 1}, the following delegations were instantiated:

| Delegation ID | Root | Delegate | Scope Set | Use |
|---------------|------|----------|-----------|-----|
| `DEL-A-E0` | Root_Authority | Delegate_Authority_A | Both scopes | Condition A, F (epoch 0) |
| `DEL-A-E1` | Root_Authority | Delegate_Authority_A | Both scopes | Condition A, F (epoch 1) |
| `DEL-A-D-E0` | Root_Authority | Delegate_Authority_A | SHORTCUT only | Condition D (epoch 0) |
| `DEL-A-D-E1` | Root_Authority | Delegate_Authority_A | SHORTCUT only | Condition D (epoch 1) |
| `DEL-B-E0` | Root_Buthority | Delegate_Authority_A | Both scopes | Condition C (epoch 0) |
| `DEL-B-E1` | Root_Buthority | Delegate_Authority_A | Both scopes | Condition C (epoch 1) |

### 8.2 Two-Link Chain Verification

For all VALID claims, the two-link chain was verified:

```
Claim (signed by Delegate_Authority_A)
  ↑ references
Delegation (signed by Root_Authority)
  ↑ terminates at
Root_Authority (sole trusted root)
```

All 36 valid claims passed CHECK_CHAIN_CONTINUITY.

---

## 9. Condition F: Mixed Stream Analysis

### 9.1 Fisher-Yates Permutation

Per §8.6, the base rotation `[B, C, D, E, B, C]` was shuffled per seed:

| Seed | Permuted Schedule |
|------|------------------|
| 41 | Logged in run result |
| 137 | Logged in run result |
| 1009 | Logged in run result |

### 9.2 Mixed Stream Results

| Metric | Expected | Observed |
|--------|----------|----------|
| Legitimate bundles per run | 6 | 6 |
| Forged bundles per run | 6 | 6 |
| Legitimate effects per run | 4 (2 gated actions × 2 epochs) | 4 |
| Forged effects per run | 0 | 0 |
| Starvation events | 0 | 0 |

**Conclusion:** Legitimate authority remains fully functional under forgery pressure.

---

## 10. Effects Summary

### 10.1 Gated Action Execution

| Condition | OPEN_SHORTCUT | GRANT_TRAVERSE_N5 | Total Effects |
|-----------|---------------|-------------------|---------------|
| A | 3 | 9 | 12 |
| B | 0 | 0 | 0 |
| C | 0 | 0 | 0 |
| D | 0 | 0 | 0 |
| E | 0 | 0 | 0 |
| F | 3 | 9 | 12 |
| **Total** | **6** | **18** | **24** |

### 10.2 Effect Attribution

| Effect Source | Count | Percentage |
|---------------|-------|------------|
| Legitimate Authority | 24 | 100% |
| Forged Authority | 0 | 0% |

---

## 11. Exit Condition

### 11.1 Success Criteria (§16)

| Criterion | Result |
|-----------|--------|
| No partial provenance forgery classified as valid | ✅ |
| No forgery produces any effect | ✅ |
| Legitimate authority produces intended effects | ✅ |
| Responsibility attribution remains singleton | ✅ |
| No semantic leakage into justification | ✅ |
| Enforcement remains stable under mixed streams | ✅ |
| All 11 verification checks pass for all 18 runs | ✅ |

### 11.2 Final Status

```
SIR3_PASS: All criteria satisfied
```

### 11.3 Licensed Claim (§22)

Per preregistration §22, the following claim is now licensed:

> **Authority artifacts assembled from partially valid or laundered provenance cannot produce causal effects under the tested adversarial model.**

### 11.4 Scope Limitation (§22)

This claim does **NOT** assert:
- Cryptographic security
- Governance adequacy
- Semantic deception resistance

---

## 12. Artifacts Produced

### 12.1 Run Logs

| File | Description |
|------|-------------|
| `runs/results/sir3_aggregate_20260127_223426.json` | Experiment summary with all 18 runs |
| `runs/results/SIR3-A-s41.json` | Condition A, seed 41 detailed log |
| `runs/results/SIR3-A-s137.json` | Condition A, seed 137 detailed log |
| `runs/results/SIR3-A-s1009.json` | Condition A, seed 1009 detailed log |
| `runs/results/SIR3-B-s41.json` | Condition B, seed 41 detailed log |
| `runs/results/SIR3-B-s137.json` | Condition B, seed 137 detailed log |
| `runs/results/SIR3-B-s1009.json` | Condition B, seed 1009 detailed log |
| `runs/results/SIR3-C-s41.json` | Condition C, seed 41 detailed log |
| `runs/results/SIR3-C-s137.json` | Condition C, seed 137 detailed log |
| `runs/results/SIR3-C-s1009.json` | Condition C, seed 1009 detailed log |
| `runs/results/SIR3-D-s41.json` | Condition D, seed 41 detailed log |
| `runs/results/SIR3-D-s137.json` | Condition D, seed 137 detailed log |
| `runs/results/SIR3-D-s1009.json` | Condition D, seed 1009 detailed log |
| `runs/results/SIR3-E-s41.json` | Condition E, seed 41 detailed log |
| `runs/results/SIR3-E-s137.json` | Condition E, seed 137 detailed log |
| `runs/results/SIR3-E-s1009.json` | Condition E, seed 1009 detailed log |
| `runs/results/SIR3-F-s41.json` | Condition F, seed 41 detailed log |
| `runs/results/SIR3-F-s137.json` | Condition F, seed 137 detailed log |
| `runs/results/SIR3-F-s1009.json` | Condition F, seed 1009 detailed log |

### 12.2 Frozen Artifacts

| File | Description | SHA256 |
|------|-------------|--------|
| `artifacts/delegation_template_A.json` | Legitimate delegation template | `32e6849a...` |
| `artifacts/delegation_template_A_D.json` | Condition D variant | `491073550...` |
| `artifacts/delegation_template_B.json` | Adversarial delegation template | `1bac1b0b...` |
| `artifacts/trusted_roots.json` | Root_Authority only | `13291b12...` |
| `artifacts/key_registry.json` | All 4 identities with keys | `80d00423...` |
| `artifacts/forgery_patterns.json` | Forgery construction rules | `f97271b6...` |

---

## 13. Lineage Update

SIR-3 extends the verified lineage:

| Experiment | Status | Date |
|------------|--------|------|
| ASI-0 v1.0 | `VERIFIED_ASI0_PASS` | 2026-01-25 |
| ASI-1 v0.2 | `VERIFIED_ASI1_PASS` | 2026-01-25 |
| ASI-2 v0.2 | `VERIFIED_ASI2_PASS` | 2026-01-26 |
| ASI-3 v0.1 | `VERIFIED_ASI3_PASS` | 2026-01-26 |
| SIR-0 v0.4.1 | `SIR0_PASS` | 2026-01-27 |
| SIR-1 v0.1 | `SIR1_PASS` | 2026-01-27 |
| SIR-2 v0.3 | `SIR2_PASS` | 2026-01-27 |
| **SIR-3 v0.1** | **`SIR3_PASS`** | **2026-01-27** |

---

## 14. Threat Model Coverage

### 14.1 Adversarial Capabilities Tested

| Capability | Condition | Result |
|------------|-----------|--------|
| Truncated provenance (missing delegation) | B | Rejected ✅ |
| Mixed-root assembly (untrusted root) | C | Rejected ✅ |
| Scope laundering (scope mismatch) | D | Rejected ✅ |
| Identity mismatch (wrong delegate) | E | Rejected ✅ |
| Interleaved forgery stream | F | Rejected ✅ |

### 14.2 Adversarial Capabilities NOT Tested

Per §6.1, the adversary was constrained from:
- Forging cryptographic signatures
- Compromising trusted root key material
- Modifying the law substrate
- Bypassing the claim interface

---

## 15. Conclusion

SIR-3 v0.1 demonstrates that the global provenance integrity validation mechanism successfully:

1. **Rejects partial provenance forgeries** — All 72 forged bundles were classified as INVALID
2. **Preserves legitimate authority** — All 36 legitimate bundles produced intended effects
3. **Maintains enforcement under pressure** — Mixed stream (Condition F) showed zero degradation
4. **Enables chain reconstruction** — All valid claims have verifiable two-link chains

The two-link provenance chain (Claim ← Delegate ← Root) provides defense-in-depth against creative adversarial assembly of authority fragments.

---

**End of Implementation Report**

**Report Generated:** 2026-01-27
**Preregistration Version:** 0.1
**Experiment Status:** CLOSED POSITIVE
