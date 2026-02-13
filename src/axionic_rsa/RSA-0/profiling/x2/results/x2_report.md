# RSA X-2 — Profiling Report
## Treaty-Constrained Delegation

**Session ID:** `46b0e5fd-9462-462d-b5e8-32d55e4803a3`
**Start:** 2026-02-13T16:26:56Z
**End:** 2026-02-13T16:26:57Z
**Total Cycles:** 26
**Constitution Hash:** `43f57f0abd7fd3a1cc335df9bc4267aa...`

## §1 Closure Criteria Evaluation

### 1. Delegated Warrant Issued: PASS ✓
- Total delegated warrants: 3

### 2. Grant Rejections Correct: PASS ✓
- Adversarial grant scenarios: 11
  - A-1-FAKE-GRANTOR: expected=GRANTOR_NOT_CONSTITUTIONAL, actual=GRANTOR_NOT_CONSTITUTIONAL ✓
  - A-2-NO-TREATY-PERM: expected=TREATY_PERMISSION_MISSING, actual=TREATY_PERMISSION_MISSING ✓
  - A-3-BAD-GRANTEE-FORMAT: expected=INVALID_FIELD, actual=INVALID_FIELD ✓
  - A-4-SCOPE-NOT-MAP: expected=INVALID_FIELD, actual=INVALID_FIELD ✓
  - A-5-INVALID-SCOPE-TYPE: expected=INVALID_FIELD, actual=INVALID_FIELD ✓
  - A-6-WILDCARD-ACTION: expected=INVALID_FIELD, actual=INVALID_FIELD ✓
  - A-7-UNKNOWN-ACTION: expected=INVALID_FIELD, actual=INVALID_FIELD ✓
  - A-8-GRANTOR-LACKS-ACTION: expected=GRANTOR_LACKS_PERMISSION, actual=GRANTOR_LACKS_PERMISSION ✓
  - A-9-SCOPE-ZONE-INVALID: expected=GRANTOR_LACKS_PERMISSION, actual=GRANTOR_LACKS_PERMISSION ✓
  - A-10-DURATION-EXCEEDED: expected=GRANTOR_LACKS_PERMISSION, actual=GRANTOR_LACKS_PERMISSION ✓
  - A-11-NONREVOCABLE: expected=NONREVOCABLE_GRANT, actual=NONREVOCABLE_GRANT ✓

### 3. Delegation Rejections Correct: PASS ✓
- Adversarial delegation scenarios: 4
  - A-12-UNSIGNED-DAR: expected=SIGNATURE_MISSING, actual=SIGNATURE_MISSING ✓
  - A-13-WRONG-KEY: expected=SIGNATURE_INVALID, actual=SIGNATURE_INVALID ✓
  - A-14-NO-TREATY-CITATION: expected=AUTHORITY_CITATION_INVALID, actual=AUTHORITY_CITATION_INVALID ✓
  - A-15-SCOPE-OUTSIDE-GRANT: expected=AUTHORITY_CITATION_INVALID, actual=AUTHORITY_CITATION_INVALID ✓

### 4. Revocation Lifecycle: PASS ✓
- Revocations admitted: 1
- Revocations rejected: 1

### 5. Expiry Lifecycle: PASS ✓
- Grant expiry confirmed: True

### 6. Replay Determinism: PASS ✓
- All state hashes match across replay

### 7. Density < 1 Preserved: PASS ✓
- Constitution validated density < 1 through Gate 8B at startup

### 8. Ed25519 Verification: PASS ✓
- Signature-related adversarial scenarios: 2

## §2 Treaty Event Summary

| Metric | Count |
|:---|---:|
| Grants Admitted | 0 |
| Grants Rejected | 10 |
| Revocations Admitted | 1 |
| Revocations Rejected | 1 |
| Delegated Warrants | 3 |
| Delegated Rejections | 5 |

## §3 Decision Type Distribution

| Decision Type | Count |
|:---|---:|
| ACTION | 26 |

## §4 Phase Summary

| Phase | Cycles | Decisions | Treaty Events |
|:---|---:|:---|:---|
| adversarial-delegation | 4 | ACTION=4 | delegated_rejections=4, delegated_warrants=0 |
| adversarial-grant | 11 | ACTION=11 | grants_admitted=0, grants_rejected=10 |
| expiry-active | 1 | ACTION=1 | delegated_rejections=0, delegated_warrants=1 |
| expiry-advance | 3 | ACTION=3 |  |
| expiry-expired | 1 | ACTION=1 | delegated_rejections=1, delegated_warrants=0 |
| lawful-delegation | 2 | ACTION=2 | delegated_rejections=0, delegated_warrants=2 |
| lawful-revocation | 1 | ACTION=1 |  |
| pre-delegation | 3 | ACTION=3 |  |

## §5 Adversarial Grant Rejection Details

| Scenario | Expected Gate | Actual Code | Correct |
|:---|:---|:---|:---:|
| A-1-FAKE-GRANTOR | GRANTOR_NOT_CONSTITUTIONAL | GRANTOR_NOT_CONSTITUTIONAL | ✓ |
| A-2-NO-TREATY-PERM | TREATY_PERMISSION_MISSING | TREATY_PERMISSION_MISSING | ✓ |
| A-3-BAD-GRANTEE-FORMAT | INVALID_FIELD | INVALID_FIELD | ✓ |
| A-4-SCOPE-NOT-MAP | INVALID_FIELD | INVALID_FIELD | ✓ |
| A-5-INVALID-SCOPE-TYPE | INVALID_FIELD | INVALID_FIELD | ✓ |
| A-6-WILDCARD-ACTION | INVALID_FIELD | INVALID_FIELD | ✓ |
| A-7-UNKNOWN-ACTION | INVALID_FIELD | INVALID_FIELD | ✓ |
| A-8-GRANTOR-LACKS-ACTION | GRANTOR_LACKS_PERMISSION | GRANTOR_LACKS_PERMISSION | ✓ |
| A-9-SCOPE-ZONE-INVALID | GRANTOR_LACKS_PERMISSION | GRANTOR_LACKS_PERMISSION | ✓ |
| A-10-DURATION-EXCEEDED | GRANTOR_LACKS_PERMISSION | GRANTOR_LACKS_PERMISSION | ✓ |
| A-11-NONREVOCABLE | NONREVOCABLE_GRANT | NONREVOCABLE_GRANT | ✓ |

## §6 Adversarial Delegation Rejection Details

| Scenario | Expected Code | Actual Code | Correct |
|:---|:---|:---|:---:|
| A-12-UNSIGNED-DAR | SIGNATURE_MISSING | SIGNATURE_MISSING | ✓ |
| A-13-WRONG-KEY | SIGNATURE_INVALID | SIGNATURE_INVALID | ✓ |
| A-14-NO-TREATY-CITATION | AUTHORITY_CITATION_INVALID | AUTHORITY_CITATION_INVALID | ✓ |
| A-15-SCOPE-OUTSIDE-GRANT | AUTHORITY_CITATION_INVALID | AUTHORITY_CITATION_INVALID | ✓ |

## §7 Cycle Log

| Cycle | Phase | Decision | Grants A/R | Deleg W/R | Notes |
|---:|:---|:---|---:|---:|:---|
| 0 | pre-delegation | ACTION | 0/0 | 0/0 | action=Notify |
| 1 | pre-delegation | ACTION | 0/0 | 0/0 | action=Notify |
| 2 | pre-delegation | ACTION | 0/0 | 0/0 | action=Notify |
| 3 | lawful-delegation | ACTION | 0/0 | 1/0 | warrants=1; action=Notify |
| 4 | lawful-delegation | ACTION | 0/0 | 1/0 | warrants=1; action=Notify |
| 5 | lawful-revocation | ACTION | 0/0 | 0/0 | revoked=1; action=Notify |
| 6 | adversarial-grant | ACTION | 0/1 | 0/0 | grant_rej=GRANTOR_NOT_CONSTITUTIONAL; action=Notify |
| 7 | adversarial-grant | ACTION | 0/1 | 0/0 | grant_rej=TREATY_PERMISSION_MISSING; action=Notify |
| 8 | adversarial-grant | ACTION | 0/1 | 0/0 | grant_rej=INVALID_FIELD; action=Notify |
| 9 | adversarial-grant | ACTION | 0/1 | 0/0 | grant_rej=INVALID_FIELD; action=Notify |
| 10 | adversarial-grant | ACTION | 0/1 | 0/0 | grant_rej=INVALID_FIELD; action=Notify |
| 11 | adversarial-grant | ACTION | 0/1 | 0/0 | grant_rej=INVALID_FIELD; action=Notify |
| 12 | adversarial-grant | ACTION | 0/1 | 0/0 | grant_rej=INVALID_FIELD; action=Notify |
| 13 | adversarial-grant | ACTION | 0/1 | 0/0 | grant_rej=GRANTOR_LACKS_PERMISSION; action=Notify |
| 14 | adversarial-grant | ACTION | 0/1 | 0/0 | grant_rej=GRANTOR_LACKS_PERMISSION; action=Notify |
| 15 | adversarial-grant | ACTION | 0/1 | 0/0 | grant_rej=GRANTOR_LACKS_PERMISSION; action=Notify |
| 16 | adversarial-grant | ACTION | 0/0 | 0/0 | action=Notify |
| 17 | adversarial-delegation | ACTION | 0/0 | 0/1 | deleg_rej=SIGNATURE_MISSING; action=Notify |
| 18 | adversarial-delegation | ACTION | 0/0 | 0/1 | deleg_rej=SIGNATURE_INVALID; action=Notify |
| 19 | adversarial-delegation | ACTION | 0/0 | 0/1 | deleg_rej=AUTHORITY_CITATION_INVALID; action=Notify |
| 20 | adversarial-delegation | ACTION | 0/0 | 0/1 | deleg_rej=AUTHORITY_CITATION_INVALID; action=Notify |
| 21 | expiry-active | ACTION | 0/0 | 1/0 | warrants=1; action=Notify |
| 22 | expiry-advance | ACTION | 0/0 | 0/0 | action=Notify |
| 23 | expiry-advance | ACTION | 0/0 | 0/0 | action=Notify |
| 24 | expiry-advance | ACTION | 0/0 | 0/0 | action=Notify |
| 25 | expiry-expired | ACTION | 0/0 | 0/1 | deleg_rej=AUTHORITY_CITATION_INVALID; action=Notify |

## §8 Overall Verdict

**X-2 CLOSURE: POSITIVE ✓**

All closure criteria met:
1. ≥1 delegated warrant issued
2. All adversarial grant rejections at correct gates
3. All adversarial delegation rejections at correct gates
4. Revocation lifecycle verified
5. Expiry lifecycle verified
6. Replay determinism verified
7. density < 1 preserved
8. Ed25519 signature verification operational

---
*Generated 2026-02-13T16:26:57Z*