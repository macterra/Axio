# RSA X-3 — Follow-Up Questions (Round 3)

**Phase:** X-3 — Sovereign Succession Under Lineage
**Status:** Pre-implementation Q&A — Round 3
**Source:** Answers from Round 2 (`docs/X-3/answers-round2.md`)

---

## X — Final Binding Ordering

**X1.** T3 revised the ordering to put ratifications before grants, but the fragment is incomplete (starts and ends with `…`). Please confirm the full binding ordering for `X3_TOPOLOGICAL`. Proposed consolidated list:

1. Amendment adoption
2. Constitutional revalidation
3. SuccessionProposal admission (sets `pending_successor_key` if non-self)
4. Treaty revocations
5. Treaty ratifications
6. Density repair (post-ratification checkpoint)
7. Treaty grants (only if `suspended_grant_ids` is empty)
8. Density repair (post-grant checkpoint)
9. RSA actions (warrants issued inline)
10. Delegated actions (warrants issued inline)
11. Cycle commit (end-state hash + CycleCommit signature)

Is this correct? Should the two density repair steps be merged into one after step 7, or are separate checkpoints needed?

**X2.** Where does **expiry** of treaty grants fit? In X-2D, expiry is implicit in `active_grants(current_cycle)` filtering. Does X-3 handle it the same way (implicit filtering at each step that queries active grants), or does it need an explicit expiry step?

---

## Y — Composition Mechanics

**Y1.** V1 says `policy_core_x3` wraps the X-2 engine. But `_x2d_topological_path` in `policy_core_x2.py` is a single monolithic function (lines 709–955). X-3 needs to insert succession admission between revalidation and grants, plus ratification between revocations and grants. Options:
  (a) Refactor `_x2d_topological_path` into sub-step functions that X-3 can call individually and interleave with succession/ratification steps.
  (b) Duplicate the full path in `policy_core_x3.py`, inserting X-3 steps.
  (c) Add hook points (callbacks/extension points) to the X-2 function.
Recommend (a) — extract sub-step functions from X-2, then compose in X-3. This avoids duplication while keeping X-2 code stable (it just calls the same sub-steps internally). Confirm or override.

**Y2.** V3 says define `X3_TOPOLOGICAL` in `policy_core_x3.py` with a "thin dispatch boundary" in X-2. The current dispatch is in `policy_core_x2` line 336: `if cycle_ordering_mode == CYCLE_ORDERING_X2D_TOPOLOGICAL`. Adding X-3 dispatch here requires X-2 to import from X-3, creating a dependency from lower layer to higher. Options:
  (a) Add a generic dispatch registry in X-2 that X-3 registers into at import time.
  (b) Move the top-level dispatch out of `policy_core_x2` into a shared `policy_dispatch.py`.
  (c) Have `policy_core_x3.py` export its own `policy_core_x3()` entry point; callers (harness) call x3 directly when X-3 mode is active, never routing through x2.
Recommend (c) — simplest, no circular deps, follows X-1→X-2 pattern where the harness calls `policy_core_x2` directly. Confirm.

---

## Z — Self-Succession vs. Boundary Records

**Z1.** U1 says self-succession does not set `pending_successor_key`. U3 says it's logged as an admitted artifact. S4 says every cycle has CycleCommit/CycleStart signed records. In a self-succession cycle, the CycleCommit payload has `pending_successor_key: null` (same as a non-succession cycle). How does replay distinguish "self-succession admitted, no-op" from "no succession proposed at all"? Is the distinction only visible in the admission trace (not in boundary records)?

**Z2.** Since self-succession is admitted (consumes the per-cycle slot per U2) but produces no state change, should the `CycleCommit` payload include a `succession_admitted: bool` flag for replay audit? Or is the admission trace in the artifact log sufficient?

---

## AA — Genesis & Session Initialization

**AA1.** Q1 says `genesis_artifact_hash = SHA256(JCS(artifact_without_hash_field))`. Is the `genesis_artifact_hash` stored *inside* the artifact file (as a field the verifier can check), or is it stored as a sidecar file (like `rsa_constitution.v0.3.yaml.sha256`)? If inside the artifact, the verifier loads the file, strips the hash field, re-computes, and compares.

**AA2.** S3 says cycle 1's `state_hash_prev` is the X-0E initial state hash. The X-0E initial hash is `SHA256(constitution_hash_bytes ‖ SHA256(UTF8(kernel_version_id)))`. X-3 adds new kernel modules and a new ordering mode. Does `kernel_version_id` need to be updated for X-3 (e.g., `rsa-replay-regime-x3-v0.1`), or does it remain `rsa-replay-regime-x0e-v0.1`?

**AA3.** At session initialization, the harness must establish the genesis sovereign key before cycle 1 and produce a CycleStart record for cycle 1. Who signs the cycle 1 CycleStart? The genesis sovereign (since no succession has occurred yet). Confirm.

**AA4.** The genesis artifact includes `genesis_sovereign_public_key`. Does the harness also need to log the genesis public key in `X3SessionStart`, or is the reference to the genesis artifact (by hash) sufficient?

---

## AB — Ratification Edge Cases

**AB1.** T4 says `DENSITY_BOUND_EXCEEDED` if `ratify=true` would breach the bound. If ratification is rejected for density, does the treaty remain SUSPENDED (allowing retry next cycle after other density-reducing events like revocations or grant expiry)?

**AB2.** Can multiple `TreatyRatification` artifacts be admitted in the same cycle (for different treaties)? The per-cycle uniqueness constraint applies only to `SuccessionProposal`, not ratifications. Confirm multiple ratifications per cycle are allowed.

**AB3.** If a treaty expires while SUSPENDED (its `duration_cycles` elapses), does it remain in `suspended_grant_ids` (blocking new grants via `SUSPENSION_UNRESOLVED`), or does expiry automatically remove it from the suspended set?

---

## AC — Overlay & ConstitutionX3

**AC1.** Q5 says merge overlay into an `EffectiveConstitutionFrame` at runtime. Should this be implemented as a new `ConstitutionX3` class extending `ConstitutionX2` (adding overlay resolution methods), or as a separate `EffectiveFrame` wrapper that holds both a `ConstitutionX2` and the overlay dict?

**AC2.** The overlay contains clauses like `CL-SUCCESSION-ENABLED`. Are these clauses structured (with `id`, `text`, `type` fields like constitutional clauses), or are they simple key-value entries? Proposed: structured, matching the constitution's clause schema for indexing uniformity.

**AC3.** Can the overlay be amended via X-1 amendment machinery? Or is it frozen for the entire session (no amendment can touch overlay clauses)?

---

## End of X-3 Follow-Up Questions Round 3 (18 questions across 6 sections X–AC)
