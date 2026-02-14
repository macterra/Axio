# RSA X-3 — Design Questions

**Phase:** X-3 — Sovereign Succession Under Lineage
**Status:** Pre-implementation Q&A
**Source:** `docs/X-3/spec.md` (v0.1), `docs/X-3/instructions.md`

---

## A — Genesis Anchoring & Identity Model

**A1.** Spec §1.2 says the Genesis Root Key is defined in "the Frozen Constitution v0.3 (or successor)" or "a canonical Genesis artifact embedded in initial state." Constitution v0.3 has no `sovereign_public_key` field or genesis identity section. Which mechanism do we use? Options:
  (a) Add a `sovereign_identity` section to the constitution (requires v0.4 or profiling constitution extension, as in X-2D).
  (b) Embed a canonical Genesis artifact in `InternalStateX2` / `InternalStateX3` at initialization time.
  (c) Pass the genesis keypair as a session parameter (logged in `X3SessionStart`).
If (c), is the genesis keypair generated per-session (deterministic from seed), or is there one canonical genesis key across all X-3 sessions?

**A2.** Is the sovereign identity purely a profiling/harness concept (the RSA-0 kernel has no existing notion of "sovereign key"), or should the sovereign identity be wired into the kernel as a first-class concept that persists across non-X-3 usage? In X-2, the RSA's own identity is implicit — only grantees have Ed25519 keys. Clarify whether X-3 introduces an explicit sovereign keypair for the RSA itself that participates in kernel operations (e.g., signing warrants, signing cycle commits).

**A3.** The spec says "Replacement without lineage is forbidden." Does this imply the kernel must reject any attempt to set a sovereign key that does not come through the `SuccessionProposal` pipeline? Or is this a design invariant enforced by the absence of any other mechanism?

**A4.** What is the initial `identity_chain_length`? Is it 0 (no successions yet, genesis is active) or 1 (genesis counts as the first link)?

---

## B — Constitution & Enabling

**B1.** Spec §3 Gate S6 checks `SUCCESSION_DISABLED`. Where is the `succession_enabled` flag defined? Options:
  (a) Add it to the constitution (AmendmentProcedure or a new SuccessionProcedure section in v0.4).
  (b) Add it to the profiling constitution (like X-2D's `CL-PERM-DELEGATION-ACTIONS`).
  (c) Default to enabled if X-3 ordering mode is active; no constitutional flag needed.

**B2.** Does X-3 require a new constitutional authority (e.g., `AUTH_SUCCESSION`) with succession-specific permissions, or does the existing authority model suffice? The spec says "X-3 introduces no new authority semantics" — does this mean succession is authorized by an existing authority (which one?), or that it is a sovereign-only action requiring no authority citation?

**B3.** Spec §2.1 has `authority_citations` on `SuccessionProposal`. What clauses must a succession proposal cite? Is there a specific constitutional clause like `CL-SUCCESSION-PROCEDURE`, or does it cite the existing governance authority (`AUTH_GOVERNANCE`)?

---

## C — SuccessionProposal Artifact

**C1.** Spec §2.1 defines `signature` as "Ed25519 over canonical payload." What is the canonical payload? The entire artifact dict excluding the `signature` field (same pattern as `sign_action_request` in X-2), or a specific subset of fields?

**C2.** The spec says "Self-succession permitted (no-op lineage extension)." Does self-succession (prior_key == successor_key) increment `identity_chain_length`? Does it trigger treaty suspension/ratification?

**C3.** Does `SuccessionProposal` need a `justification` field that is a structured object (like `Justification` in ActionRequest with `text`, `clause_ref`), or is it a plain string as shown in the spec?

**C4.** Does the `SuccessionProposal` carry a `prior_constitution_hash` for binding (similar to AmendmentProposal), or is constitutional binding implicit through the authority citations?

**C5.** The spec field list shows `prior_sovereign_public_key` and `successor_public_key`. What format? The existing X-2 convention is `ed25519:<hex64>` for grantee identifiers. Should sovereign keys use the same format, or bare hex (since the scheme is always Ed25519)?

---

## D — Admission Pipeline Details

**D1.** Gate S2 says "Citations evaluated under constitution state as of prior cycle boundary." Does this mean the constitution in effect at the *start* of the current cycle (i.e., after any amendment adoption in the current cycle per topological ordering), or the constitution in effect at the *end* of the prior cycle (before current cycle's amendments)? Spec §4 puts amendment adoption (step 1) before succession admission (step 3), suggesting the current cycle's adopted constitution applies.

**D2.** Gate S5 (Lineage Integrity) checks for cycles and forks. How is a "cycle" detected? Is it sufficient to check `successor_public_key != prior_sovereign_public_key` across the lineage chain, or must we maintain a set of all historical sovereign keys and reject if `successor_public_key` has appeared before?

**D3.** Gate S5 mentions `LINEAGE_FORK`. How can a fork occur in a single-agent deterministic system? Is this a defense against replay manipulation where a different SuccessionProposal at the same cycle could create an alternate chain? Clarify the concrete check.

**D4.** Gate S7 (Per-Cycle Uniqueness) — if a SuccessionProposal is admitted at step 3 of topological ordering, and a second proposal arrives in the same cycle, is the second proposal rejected regardless of validity? Or does the pipeline only process the first one encountered (lexicographic ordering by artifact ID)?

**D5.** Are adversarial/invalid `SuccessionProposal` candidates generated and injected by the harness (like X-2 adversarial scenarios), or must the kernel's succession pipeline be tested purely through unit tests?

---

## E — Cycle Ordering & Topological Time

**E1.** Spec §4 defines an 11-step ordering. Instructions §7.2 defines the same 11 steps. The X-2D topological path has 9 steps (T1–T9). Should X-3 add a new ordering mode `X3_TOPOLOGICAL` to `policy_core_x2`, or should it replace/extend `X2D_TOPOLOGICAL`? If new, the kernel function will need a third ordering mode constant.

**E2.** Step 4 says "Record `pending_successor_key`" as a separate ordering step. Is this a distinct kernel action that produces a state delta, or is it an implicit consequence of step 3 (succession admission)? If step 3 admits the proposal, does `pending_successor_key` get set immediately within step 3, making step 4 redundant?

**E3.** Step 11 says "Cycle N End-State commit." In X-0E, the state hash chain is computed by the host/harness, not the kernel. In X-3, the commit must be *signed* by the sovereign key. Does signature happen inside the kernel (making the kernel impure — it needs the private key), or in the harness/host? If in the harness, how does the kernel verify the signature during replay?

**E4.** Does the X-3 topological ordering subsume X-2D's ordering? I.e., should all X-2D families also work under `X3_TOPOLOGICAL`, or are the ordering modes independent?

---

## F — Boundary Signature & Handover

**F1.** Instructions §8.2 Phase B says "Cycle N End-State commit MUST be signed by `prior_sovereign_public_key`." What exactly is signed? The state hash chain value for cycle N? A canonical dict containing state hash + pending_successor_key + cycle_id? Define the exact payload.

**F2.** Instructions §8.2 Phase C says "verify the Cycle N+1 start/header signature under `sovereign_public_key_active`." What is the "Cycle N+1 start header"? Is this a new artifact type, or is it a deterministic value derived from the cycle N commit (e.g., the state hash chain value)? Who signs it — the successor (meaning the harness/host must have the successor's private key)?

**F3.** Self-succession (no-op): If `prior_key == successor_key`, Phase B and Phase C signatures are under the same key. Are both signatures still required (for structural uniformity), or is self-succession a no-op that skips boundary verification?

**F4.** The private key must be available to produce signatures. In the deterministic profiling harness, the sovereign keypair is generated from a seed. Does the kernel ever hold private keys, or are signatures produced exclusively by the harness and verified by the kernel? (This is the purity boundary question — private keys + signing = side effect.)

**F5.** How does the boundary signature interact with the X-0E state hash chain? Is the boundary signature *included* in the state hash computation, or is it a separate verification layer on top of the state hash chain?

---

## G — Treaty Suspension & Ratification

**G1.** Spec §6 says "All active treaties enter SUSPENDED." The current `ActiveTreatySet` has `grants`, `revoked_grant_ids`, and `invalidated_grant_ids` — but no `suspended_grant_ids` or per-grant state field. Options:
  (a) Add `suspended_grant_ids: set` to `ActiveTreatySet`.
  (b) Add a `status` field to `TreatyGrant` (ACTIVE/SUSPENDED/REVOKED).
  (c) Track suspension state in `InternalStateX3` separately.
Which approach?

**G2.** Instructions §10.2 says `TreatyRatification` with `ratify=false` can either transition to REVOKED or remain SUSPENDED ("pick one rule and freeze it"). Which rule should we adopt? I recommend: `ratify=false` → REVOKED (permanent, matching existing revocation semantics). Confirm or override.

**G3.** Is `TreatyRatification` a new artifact type for the kernel, or a harness-only artifact that manipulates `ActiveTreatySet` externally? If kernel-level, does it go through the treaty admission pipeline, or does it have its own admission gate?

**G4.** Can a successor issue new `TreatyGrant`s before ratifying all suspended treaties? Or must all suspensions be resolved (ratified or revoked) before new grants are admitted?

**G5.** Ratification schedule: Instructions §3.1 defines `ratification_schedule` in `X3SessionStart`. Are ratification decisions deterministic from the session seed, or does the schedule only specify *when* ratification happens (with the decision — ratify true/false — determined by the generator)?

**G6.** Do suspended treaties count toward effective density? If yes, a near-bound session could fail to ratify because ratification would exceed the density bound. If no, density drops on suspension and rises on ratification — potentially allowing the successor to admit new grants into the freed density space before ratifying old ones.

**G7.** If self-succession does trigger treaty suspension (per A2 follow-up), does the self-successor still need to ratify all treaties? This would make self-succession operationally expensive. Or does self-succession skip suspension entirely?

---

## H — Prior Key Revocation

**H1.** Spec §5.2 says "Prior key holds zero authority" and "acts as a stranger unless granted authority by successor." In the profiling harness, how is a "post-activation attempt by prior key" injected? Is this an adversarial scenario where and invalid `SuccessionProposal` is signed by the old sovereign key after the successor is active?

**H2.** What specific actions by the prior key must be tested for `PRIOR_KEY_PRIVILEGE_LEAK`? Options:
  (a) Prior key attempts a new `SuccessionProposal` → rejected.
  (b) Prior key attempts to submit a `TreatyGrant` as grantor → rejected.
  (c) Prior key attempts to submit a `TreatyRatification` → rejected.
  (d) All of the above?

**H3.** Can the successor explicitly re-grant authority to the prior key via a `TreatyGrant` (making the old sovereign a regular grantee)? This is implied by "acts as a stranger unless granted authority by successor."

---

## I — Replay & State Hash

**I1.** Spec §8 says state hash must include `identity_chain_length`, `prior key`, `successor key`, `treaty suspension events`, and `treaty ratification events`. The current X-0E state hash chain has 4 components (artifacts, admission, selector, execution). How should the new fields be incorporated? Options:
  (a) Add a 5th component `H_lineage` = SHA256(JCS({identity fields})).
  (b) Extend existing components (e.g., succession artifacts go into `H_artifacts`).
  (c) Add multiple new components (one for lineage, one for suspension/ratification).

**I2.** Boundary signatures (Phase B commit signature, Phase C start header signature) — are these included in the state hash chain as artifacts, or are they a parallel verification layer?

**I3.** During replay, the replayer must verify boundary signatures. Does the replayer need access to the full lineage chain of public keys, or can it reconstruct them from the succession artifacts in the log?

**I4.** Can the replay harness reuse the X-2D replay module (`profiling/x2d/harness/src/replay.py`) as a base, or does X-3 require a fundamentally different replay architecture?

---

## J — Repo Layout & Module Structure

**J1.** Instructions §1 places harness code under `replay/src/` (x3_runner.py, x3_generators.py, x3_metrics.py, x3_boundary.py). Past phases placed harness code under `profiling/<phase>/harness/src/`. Should X-3 follow the existing convention (`profiling/x3/harness/src/`) or the instructions' layout (`replay/src/`)?

**J2.** Does X-3 require new kernel modules (e.g., `kernel/src/rsax3/`), or should the succession logic be added to the existing X-2 kernel extension? The spec says "no new authority semantics" and the instructions say "extend the RSA-X2 repo." If kernel extension, I recommend creating `kernel/src/rsax3/` with succession_admission.py, artifacts_x3.py, and policy_core_x3.py — consistent with X-1→X-2 pattern.

**J3.** Instructions §1 mentions `artifacts/phase-x/x3/x3_session_spec.v0.1.schema.json` and `x3_profile_defaults.v0.1.json`. Should these be created during initial setup, or are they generated artifacts? For the schema, should it follow the X-2D pattern where schemas are defined in Python code and validated programmatically?

---

## K — Profiling Families & Scenarios

**K1.** Instructions §5 defines 7 mandatory scenario buckets. Should these map to distinct profiling families (like X-2D's D-BASE, D-CHURN, etc.), or are they scenarios within a single session (like X-2's phases A–G)?

**K2.** How many cycles per scenario/family? X-2D used 50–80 cycles per family. Should X-3 use similar ranges, or does the succession boundary mechanics require longer sessions?

**K3.** Instructions §5.5 says "Multi-rotation in one session (≥2 activations)." What is the maximum number of rotations in a single session? Should the generator support arbitrary rotation counts, or cap at a practical limit?

**K4.** For the "Rotation during delegation churn" scenario, should the harness generate grants/revocations in the same cycle as the succession proposal, or in adjacent cycles? Does topological ordering guarantee stability either way?

**K5.** Are there latency or metric targets for X-3 (like X-0L's inhabitation floor), or is the closure criteria purely structural (§11)?

---

## L — TreatyRatification Artifact

**L1.** Instructions §4 schema shows `TreatyRatification` with `treaty_id`, `ratify: boolean`, `signature`. Missing from this list: `id`, `type`, `created_at`, `authority_citations`. Should TreatyRatification follow the standard artifact pattern (id + type + created_at + author)?

**L2.** Instructions §3 says "if an equivalent [TreatyRatification] exists, alias deterministically." No equivalent exists in the current codebase. Confirm this is a new artifact type.

**L3.** The `signature` on TreatyRatification — signed by the active sovereign key (successor). What payload is signed? The canonical dict excluding the signature field (standard pattern)?

**L4.** Can TreatyRatification reference multiple treaties, or is it one ratification per treaty?

**L5.** Where in the topological ordering does TreatyRatification admission occur? It's not listed in the 11-step ordering (§4/§7.2). Should it happen after treaty grants (step 5) but before RSA actions (step 8)? Or as a sub-step of step 5/6?

---

## M — Logging & Metrics

**M1.** Instructions §14 specifies three new JSONL files: `x3_sessions.jsonl`, `x3_metrics.jsonl`, `x3_boundary_events.jsonl`. In the X-2D profiling harness, session results are written as JSON to `profiling/x2d/results/`. Should X-3 follow the same pattern (harness writes results to `profiling/x3/results/`), or create log files under `logs/` as the instructions specify?

**M2.** Instructions §14 says to extend existing traces with succession admission decisions, lineage checks, suspension events, and ratification outcomes. Which existing log stream should these go into? The X-2 treaty trace, or a new succession trace?

**M3.** Should the harness produce a summary JSON (like `x2d_summary.json`) for overall closure assessment?

---

## N — Gate Instability Instrumentation

**N1.** Instructions §12 mandates gate instability detection. Is this a replay-time check (compare original run gates/codes vs replay gates/codes), or a runtime check (verify determinism by running the same input twice)?

**N2.** Should gate instability detection apply to all gates (S1–S7, session gates 6/7, boundary verification), or only to succession-specific gates?

**N3.** The instructions say "Any mismatch is an X-3 failure." Is gate instability a separate closure criterion beyond those listed in spec §11, or is it subsumed by "replay divergence = 0"?

---

## O — Interaction with Amendment (X-1)

**O1.** Topological ordering puts amendment adoption (step 1) before succession admission (step 3). Can an amendment that adds or removes `succession_enabled` take effect in the same cycle as a succession proposal? If an amendment disables succession in step 1, does the succession proposal at step 3 get rejected with `SUCCESSION_DISABLED`?

**O2.** Can an amendment be proposed in the same cycle as a succession? The spec doesn't forbid it. Under topological ordering, amendment queuing happens after succession (step 6 is not explicit — where does amendment queuing go)? Clarify.

**O3.** Does the successor inherit all pending amendments from the prior sovereign? The spec says "Amendments remain valid" (§7), implying pending amendments survive succession. Confirm.

---

## P — Edge Cases

**P1.** What happens if the sovereign key holder rotates to a key that is already a treaty grantee? Does the grantee identity collapse into the sovereign identity, or are they tracked independently (same Ed25519 key, different roles)?

**P2.** Can a succession proposal be submitted to the kernel without going through topological ordering (i.e., in the DEFAULT ordering mode)? Or is X3_TOPOLOGICAL mandatory when succession is enabled?

**P3.** What if the harness wants to test a succession at cycle 1 (the very first cycle)? Is the genesis key established before cycle 1, allowing a succession proposal at cycle 1?

**P4.** Maximum `identity_chain_length` — is there an upper bound, or can it grow indefinitely?

**P5.** Does the successor's keypair need to be pre-registered or pre-announced, or can any valid Ed25519 key appear as `successor_public_key` (subject to lineage integrity checks)?

---

## End of X-3 Questions (98 questions across 16 sections A–P)
