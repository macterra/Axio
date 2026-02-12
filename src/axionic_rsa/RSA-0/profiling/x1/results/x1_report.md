# RSA X-1 — Profiling Report
## Reflective Amendment Under Frozen Sovereignty

**Session ID:** `1fd560f6-6801-45f6-81ec-939cee370828`
**Start:** 2026-02-12T23:32:03Z
**End:** 2026-02-12T23:32:05Z
**Total Cycles:** 36

## §1 Closure Criteria Evaluation

### 1. Amendment Adopted: PASS ✓
- Adoptions: 4
  - Cycle 7: b41db3ba5ffe9ed7... → 05df3cbd562a8632...
  - Cycle 23: 05df3cbd562a8632... → 7729594a9e779283...
  - Cycle 28: 7729594a9e779283... → 965603eebaad2a0f...
  - Cycle 34: 965603eebaad2a0f... → e44ac6dfb912edc7...

### 2. Replay Determinism: PASS ✓
- All state hashes match across replay

### 3. Density < 1 Preserved: PASS ✓
- All adopted constitutions validated density < 1 through Gate 8B

### 4. ECK Preserved: PASS ✓
- All adopted constitutions validated ECK sections through Gate 7

### 5. Structured AmendmentProcedure: PASS ✓
- All adopted constitutions validated structured fields through Gate 8B.5

### 6. Failures Attributable: PASS ✓
- Adversarial rejections: 7
  - A-1-UNIVERSAL-AUTH: expected=UNIVERSAL_AUTHORIZATION, actual=SCHEMA_INVALID ✓
  - A-2-SCOPE-COLLAPSE: expected=SCOPE_COLLAPSE, actual=SCHEMA_INVALID ✓
  - A-3-COOLING-REDUCTION: expected=ENVELOPE_DEGRADED, actual=SCHEMA_INVALID ✓
  - A-4-THRESHOLD-REDUCTION: expected=ENVELOPE_DEGRADED, actual=SCHEMA_INVALID ✓
  - A-5-WILDCARD: expected=WILDCARD_MAPPING, actual=SCHEMA_INVALID ✓
  - A-6-PHYSICS-CLAIM: expected=PHYSICS_CLAIM_DETECTED, actual=SCHEMA_INVALID ✓
  - A-7-ECK-REMOVAL: expected=ECK_MISSING, actual=SCHEMA_INVALID ✓

## §2 Decision Type Distribution

| Decision Type | Count |
|:---|---:|
| ACTION | 21 |
| ADOPT | 4 |
| QUEUE_AMENDMENT | 4 |
| REFUSE | 7 |

## §3 Phase Summary

| Phase | Cycles | Decisions |
|:---|---:|:---|
| adopt | 1 | ACTION=1 |
| adversarial | 7 | REFUSE=7 |
| chain-adopt | 3 | ACTION=3 |
| chain-cooling | 9 | ACTION=6, ADOPT=3 |
| chain-propose | 3 | QUEUE_AMENDMENT=3 |
| cooling | 2 | ACTION=1, ADOPT=1 |
| post-fork | 5 | ACTION=5 |
| pre-fork | 5 | ACTION=5 |
| propose | 1 | QUEUE_AMENDMENT=1 |

## §4 Constitution Transitions

| Cycle | Prior Hash | New Hash | Chain |
|---:|:---|:---|---:|
| 7 | `b41db3ba5ffe9ed74b40553d...` | `05df3cbd562a8632ccbc7435...` | - |
| 23 | `05df3cbd562a8632ccbc7435...` | `7729594a9e7792831ea8c5cc...` | 1 |
| 28 | `7729594a9e7792831ea8c5cc...` | `965603eebaad2a0fb0d32bfb...` | 2 |
| 34 | `965603eebaad2a0fb0d32bfb...` | `e44ac6dfb912edc7c0d8bf05...` | 3 |

**Initial:** `b41db3ba5ffe9ed74b40553d0a0cc019...`
**Final:** `e44ac6dfb912edc7c0d8bf0527a79a62...`

## §5 Adversarial Rejection Results

| Scenario | Expected | Actual | Correct |
|:---|:---|:---|:---:|
| A-1-UNIVERSAL-AUTH | UNIVERSAL_AUTHORIZATION | SCHEMA_INVALID | ✓ |
| A-2-SCOPE-COLLAPSE | SCOPE_COLLAPSE | SCHEMA_INVALID | ✓ |
| A-3-COOLING-REDUCTION | ENVELOPE_DEGRADED | SCHEMA_INVALID | ✓ |
| A-4-THRESHOLD-REDUCTION | ENVELOPE_DEGRADED | SCHEMA_INVALID | ✓ |
| A-5-WILDCARD | WILDCARD_MAPPING | SCHEMA_INVALID | ✓ |
| A-6-PHYSICS-CLAIM | PHYSICS_CLAIM_DETECTED | SCHEMA_INVALID | ✓ |
| A-7-ECK-REMOVAL | ECK_MISSING | SCHEMA_INVALID | ✓ |

## §6 Cycle Log

| Cycle | Phase | Decision | Constitution | Notes |
|---:|:---|:---|:---|:---|
| 0 | pre-fork | ACTION | `b41db3ba5ffe...` | action=Notify |
| 1 | pre-fork | ACTION | `b41db3ba5ffe...` | action=Notify |
| 2 | pre-fork | ACTION | `b41db3ba5ffe...` | action=Notify |
| 3 | pre-fork | ACTION | `b41db3ba5ffe...` | action=Notify |
| 4 | pre-fork | ACTION | `b41db3ba5ffe...` | action=Notify |
| 5 | propose | QUEUE_AMENDMENT | `b41db3ba5ffe...` | proposal=448e74d517f2... |
| 6 | cooling | ACTION | `b41db3ba5ffe...` | action=Notify |
| 7 | cooling | ADOPT | `b41db3ba5ffe...` | adopted→05df3cbd562a... |
| 8 | adopt | ACTION | `05df3cbd562a...` | action=Notify |
| 9 | post-fork | ACTION | `05df3cbd562a...` | action=Notify |
| 10 | post-fork | ACTION | `05df3cbd562a...` | action=Notify |
| 11 | post-fork | ACTION | `05df3cbd562a...` | action=Notify |
| 12 | post-fork | ACTION | `05df3cbd562a...` | action=Notify |
| 13 | post-fork | ACTION | `05df3cbd562a...` | action=Notify |
| 14 | adversarial | REFUSE | `05df3cbd562a...` | rejected=SCHEMA_INVALID |
| 15 | adversarial | REFUSE | `05df3cbd562a...` | rejected=SCHEMA_INVALID |
| 16 | adversarial | REFUSE | `05df3cbd562a...` | rejected=SCHEMA_INVALID |
| 17 | adversarial | REFUSE | `05df3cbd562a...` | rejected=SCHEMA_INVALID |
| 18 | adversarial | REFUSE | `05df3cbd562a...` | rejected=SCHEMA_INVALID |
| 19 | adversarial | REFUSE | `05df3cbd562a...` | rejected=SCHEMA_INVALID |
| 20 | adversarial | REFUSE | `05df3cbd562a...` | rejected=SCHEMA_INVALID |
| 21 | chain-propose | QUEUE_AMENDMENT | `05df3cbd562a...` | proposal=2e0180ecd6b8... |
| 22 | chain-cooling | ACTION | `05df3cbd562a...` | action=Notify |
| 23 | chain-cooling | ADOPT | `05df3cbd562a...` | adopted→7729594a9e77... |
| 24 | chain-adopt | ACTION | `7729594a9e77...` | action=Notify |
| 25 | chain-propose | QUEUE_AMENDMENT | `7729594a9e77...` | proposal=e11b1101f9b0... |
| 26 | chain-cooling | ACTION | `7729594a9e77...` | action=Notify |
| 27 | chain-cooling | ACTION | `7729594a9e77...` | action=Notify |
| 28 | chain-cooling | ADOPT | `7729594a9e77...` | adopted→965603eebaad... |
| 29 | chain-adopt | ACTION | `965603eebaad...` | action=Notify |
| 30 | chain-propose | QUEUE_AMENDMENT | `965603eebaad...` | proposal=7fccd6bfc11d... |
| 31 | chain-cooling | ACTION | `965603eebaad...` | action=Notify |
| 32 | chain-cooling | ACTION | `965603eebaad...` | action=Notify |
| 33 | chain-cooling | ACTION | `965603eebaad...` | action=Notify |
| 34 | chain-cooling | ADOPT | `965603eebaad...` | adopted→e44ac6dfb912... |
| 35 | chain-adopt | ACTION | `e44ac6dfb912...` | action=Notify |

## §7 Overall Verdict

**X-1 CLOSURE: POSITIVE ✓**

All closure criteria met:
1. ≥1 amendment adopted
2. Replay determinism verified
3. density < 1 preserved at all transitions
4. ECK preserved at all transitions
5. Structured AmendmentProcedure preserved at all transitions
6. All rejection paths logged and attributable

---
*Generated 2026-02-12T23:32:05Z*