# Stage VIII-1 Implementation Questions

## Q1: AuthorityID Generation
The spec states AuthorityIDs must be "unique, immutable" and "not derivable from record content." In AKR-0, AuthorityIDs were computed as `A:` + SHA256(canonical_json). Should VIII-1 use a different ID generation scheme (e.g., UUID, sequential counter, or AIE-assigned IDs)?

## Q2: Scope Element Specification
The spec says both authorities bind "the same atomic scope element." What specific scope element should be used? (e.g., `["R0000", "READ"]` or a different resource/operation pair?)

## Q3: Holder IDs for the Two Authorities
What holder IDs should be assigned to the two injected authorities? (e.g., `H0001` and `H0002`?)

## Q4: Third-Party Holder ID for Condition B
Condition B requires actions "signed by an identity not present in the Authority State." What holder ID should the harness use for these third-party requests?

## Q5: Number of Action Requests per Condition
How many candidate action requests should the harness generate per condition? The spec says "requests alternate between the two authority holders" but doesn't specify a count.

## Q6: Conflict Registration Timing
Should conflict be registered:
- (a) At authority injection time (epoch 0) when both authorities are added and overlap is detected?
- (b) At first action request evaluation time?
- (c) Both?

## Q7: Anti-Ordering Implementation for Authority State
The spec requires authorities be stored such that "no stable index position" can become a priority signal. Should the kernel:
- (a) Use an unordered set/dict keyed by AuthorityID?
- (b) Shuffle authority order on each access?
- (c) Use a different mechanism?

## Q8: Conflict Record AuthorityID Set
The spec requires conflict records store AuthorityIDs as an "unordered set." For canonical JSON serialization (which requires sorted keys for determinism), how should the conflict record be represented without implying ordering? Should there be a canonical sort for serialization but explicit documentation that this is not priority?

## Q9: Gas Budget Values
Should VIII-1 use the same gas budgets as AKR-0 (ACTION_EVAL=50,000, TRANSFORM=100,000, EPOCH_ADVANCE=200,000)? Since no actions execute and no transformations/epochs occur, are these budgets even relevant?

## Q10: PRNG and Seeds
Is a PRNG required for VIII-1? The run appears fully deterministic with no random elements (fixed authorities, fixed actions). If so, should we still use PCG32 with a fixed seed for consistency?

## Q11: Epoch Semantics
The spec says "No Epoch Ticks are permitted" and temporal mechanisms are disabled. Should the kernel remain at epoch 0 throughout the entire run?

## Q12: Transformation Admissibility Check at Deadlock
The spec states "the kernel must affirmatively evaluate the admissibility of transformations" during deadlock determination. With empty PermittedTransformationSet for both authorities, is it sufficient to check that no authority has transformation permissions, or must we enumerate all possible transformation types and verify each is inadmissible?

## Q13: Condition A/B Execution Model
Are Conditions A and B:
- (a) Two separate runs with shared initial state?
- (b) Two phases of a single continuous run?
The instructions say "Conditions A then B are executed in one run" suggesting (b).

## Q14: Logging Format
Should VIII-1 use the same JSONL logging format as AKR-0 with hash chains, or is a different format required?

## Q15: Reusing AKR-0 Code
Can we reuse the AKR-0 implementation files (structures.py, canonical.py, etc.) as a base, modifying only what's necessary for VIII-1 constraints? Or should VIII-1 be a fresh implementation?

## Q16: State Hash Verification
At what points should state hashes be computed and logged? After each event? Only at run start/end?

## Q17: Definition of "Explicitly Observable"
The spec requires conflicts to be "explicitly observable in kernel state and verifier output." What constitutes explicit observability? Logging? API access? Presence in serialized state?

## Q18: Deadlock Entry vs. Declaration
The spec distinguishes between `STATE_DEADLOCK` (the state) and `DEADLOCK_DECLARED` (the observable output). Should the kernel emit DEADLOCK_DECLARED once when entering deadlock, or on every subsequent action attempt that hits the deadlock state?

---

*Questions Q1–Q18 answered in answers.md — 2025-01-31*

---

## Follow-Up Questions

*No follow-ups required.*

All 18 questions have been answered with BINDING clarity. The implementation constraints are now fully specified:

| Area | Resolution |
|------|------------|
| AuthorityID | AIE-assigned opaque (e.g., `AUTH_A`, `AUTH_B`) |
| Scope | `["R0000", "OP0"]` — single atomic element |
| Holders | `HOLDER_A`, `HOLDER_B`, `HOLDER_X` (third-party) |
| Action counts | Condition A: 4 (A,B,A,B), Condition B: 2 (X,X) |
| Conflict timing | First action evaluation, not injection |
| Storage | `dict[AuthorityID → AuthorityRecord]` — keyed, not indexed |
| Set serialization | Canonical sorted for determinism, marked as unordered |
| Gas | Reuse AKR-0 budgets unchanged |
| PRNG | Not used, but log `SEED=0` |
| Epoch | Fixed at 0 |
| Execution model | Single continuous run (A then B) |
| Logging | AKR-0 JSONL + hash chain |
| Code reuse | Encouraged from AKR-0 |
| State hashing | After every observable event |
| Observability | State + logs + verifier interface |
| Deadlock emission | Once on entry, persist as state |

**Ready for preregistration and implementation.**
