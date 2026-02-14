# A — Genesis Anchoring & Identity Model

**A1. Which genesis mechanism?**
Use **(b) canonical Genesis artifact embedded in initial state**, because Constitution v0.3 has no genesis identity section and we are not bumping it to v0.4 for X-3.

* Add `artifacts/phase-x/x3/genesis.v0.1.json` containing:

  * `type="GenesisIdentity"`
  * `genesis_sovereign_public_key`
  * `genesis_artifact_hash`
* Kernel loads this at initialization and sets:

  * `sovereign_public_key_active = genesis_sovereign_public_key`
  * `identity_chain_length = 1`
  * `identity_chain_tip_public_key = genesis_sovereign_public_key`

**Genesis keypair provenance (private key):** harness-only, derived deterministically from a **pinned constant seed** (e.g. `X3_GENESIS_SEED`) so it’s reproducible across runs and never logged as a secret. Only the **public key** is in the Genesis artifact.

**A2. Is sovereign identity harness-only or kernel-first-class?**
Kernel-first-class. X-3 requires the kernel to have an explicit notion of:

* `sovereign_public_key_active`
* `pending_successor_key`
* lineage counters/tip

because boundary verification and “prior key zeroing” must be enforced inside the kernel’s admissibility/verification logic (still pure; verification only).

**A3. “Replacement without lineage is forbidden” — what enforces it?**
Enforced by **absence of any other state setter** and an explicit invariant:

* the only write path to `sovereign_public_key_active` is the **boundary activation step** that consumes `pending_successor_key`, which itself can only be set by an **admitted** `SuccessionProposal`.

Any attempt to set sovereign key by any other mechanism is a kernel error / hard failure (panic) in dev, and an invariant violation in profiling.

**A4. Initial `identity_chain_length`?**
**1.** Genesis counts as the first link (root). Each *non-noop* succession increments by 1.

---

# B — Constitution & Enabling

**B1. Where is `succession_enabled` defined?**
Use **(b) profiling constitution overlay**, not Constitution v0.3. X-3 sessions load an overlay file (frozen per session profile; hash logged before cycle 1) containing:

* `succession_enabled: bool`

Gate S6 reads **overlay first**, then defaults:

* If `cycle_ordering_mode == X3_TOPOLOGICAL`, default `succession_enabled = true` unless overlay explicitly disables it.

This keeps Constitution v0.3 frozen and still permits same-cycle amendment experiments later without redefining the constitution file itself.

**B2. Does X-3 require new constitutional authority like `AUTH_SUCCESSION`?**
No. Succession is a **sovereign-only operation** gated by:

* signature under active sovereign key,
* sovereign match,
* lineage integrity,
* `succession_enabled`.

This is consistent with “no new authority semantics.” Succession does not become a delegated permission.

**B3. What do `authority_citations` cite?**
They cite a **profiling overlay clause** (not Constitution v0.3) such as:

* `CL-SUCCESSION-ENABLED`
* `CL-SUCCESSION-SINGLETON-LINEAGE`
* `CL-SUCCESSION-RATIFICATION-REQUIRED`

Gate S2 resolves citations against the **effective constitutional frame = Constitution v0.3 + profiling overlay** (overlay treated as a frozen addendum for profiling only, hash-anchored in logs and replay).

---

# C — SuccessionProposal Artifact

**C1. What is the canonical payload to sign?**
Standard pattern: **JCS-canonicalized artifact dict excluding the `signature` field**. (Exactly like X-2 ActionRequest signing pattern.)

**C2. Self-succession behavior?**
Define self-succession as a **no-op rotation**:

* `prior == successor` **does not increment** `identity_chain_length`
* **does not trigger** treaty suspension/ratification
* still must pass admission gates (including per-cycle uniqueness)
* boundary zipper signatures still apply (they verify under the same key)

This preserves structural uniformity while avoiding operational cost.

**C3. `justification` structured or string?**
Keep it a **plain string** in v0.1. (Structured justification is a semantic expansion you do not need for X-3’s claim.)

**C4. Should SuccessionProposal carry `prior_constitution_hash`?**
No. Binding is via:

* Gate S2 snapshot of effective constitution frame (v0.3 + overlay) at the specified boundary
* logged `constitution_hash_tip_at_start` in session logs

Adding an explicit hash field is redundant and creates another binding surface.

**C5. Key format?**
Use the existing convention consistently:

* `ed25519:<hex64>`

for both `prior_sovereign_public_key` and `successor_public_key`.

---

# D — Admission Pipeline Details

**D1. Gate S2 “prior cycle boundary” — which constitution applies?**
Use the **end of prior cycle** (Cycle N−1 commit) as the snapshot, **not** the constitution after same-cycle amendment adoption.

This is deliberate: it prevents “amend then succeed” in the same cycle from retroactively changing the authorization basis of the proposal that appears in that cycle’s input buffer.

(You can later design an explicit “same-cycle constitutionalization” phase if you want it; X-3 v0.1 should remain conservative.)

**D2. Cycle detection rule?**
Maintain a set of **all historical sovereign public keys** in lineage. Reject if:

* `successor_public_key` already appeared anywhere in lineage (unless self-succession no-op case).

That is the simplest, strongest, and deterministic.

**D3. How can `LINEAGE_FORK` occur?**
In a deterministic single-run it typically won’t. It’s a **replay/manipulation defense**: if logs are tampered such that two different admitted succession events claim the same lineage position, you detect mismatch between:

* derived `identity_chain_tip_hash` / chain length
* and the sequence of admitted proposals

Concrete check: for each cycle boundary, ensure there is **at most one** lineage tip transition, and that it consumes the unique `pending_successor_key` set in the prior committed cycle. Any alternate admissible transition path is `LINEAGE_FORK`.

**D4. Multiple SuccessionProposals same cycle — how handled?**
Deterministic rule:

* evaluate in canonical order (e.g., lexicographic by `artifact_id` after canonicalization)
* admit at most one
* all others rejected with `MULTIPLE_SUCCESSIONS_IN_CYCLE`

**D5. Are invalid proposals generated by harness?**
Yes. Harness injects adversarial candidates deterministically (like X-2D invalid request fractions). Unit tests alone are insufficient; you need session-level replay evidence.

---

# E — Cycle Ordering & Topological Time

**E1. New ordering mode or extend X-2D?**
Add a **new constant** `X3_TOPOLOGICAL`. Do not overload `X2D_TOPOLOGICAL`; X-3 adds boundary mechanics and ratification ordering.

**E2. Is “record pending_successor_key” a real step?**
It is a **state delta produced by step 3** (succession admission). Step 4 is logically redundant but acceptable as a spec clarity marker. Implementation: set `pending_successor_key` inside the admission handler; no second pass.

**E3. Commit signing inside kernel or harness?**
Harness. Kernel remains pure.

* Harness constructs Cycle N commit payload
* Harness signs with the active sovereign private key
* Kernel verifies the signature as part of the “commit acceptance / replay verification” layer

If you currently don’t have a kernel-visible “commit object,” introduce a **harness-level log record** (see F) that replay uses identically.

**E4. Does X-3 ordering subsume X-2D?**
X-3 ordering **can subsume** X-2D ordering (it’s a refinement). For simplicity, define:

* If `X3_TOPOLOGICAL` active, X-2D sessions (if run under it) must still satisfy X-2D ordering constraints.

But do **not** claim equivalence; treat them as separate modes with one being a superset.

---

# F — Boundary Signature & Handover

**F1. What exactly is signed for Cycle N commit?**
Define a canonical commit payload:

```
CycleCommitPayload = JCS({
  "type": "CycleCommit",
  "cycle_id": N,
  "kernel_version_id": ...,
  "state_hash_end": ...,
  "state_hash_prev": ...,
  "constitution_hash_tip": ...,
  "pending_successor_key": <ed25519:... or null>,
  "identity_chain_length": ...,
  "identity_chain_tip_public_key": ...
})
```

Signature = Ed25519 over `CycleCommitPayload`.

**F2. What is “Cycle N+1 start header”? artifact or derived?**
Make it a **harness-level record** parallel to CycleCommit:

```
CycleStartPayload = JCS({
  "type": "CycleStart",
  "cycle_id": N+1,
  "kernel_version_id": ...,
  "state_hash_prev": <Cycle N state_hash_end>,
  "sovereign_public_key_active": <expected active key at start>,
  "identity_chain_length": ...
})
```

Signed by the **start-cycle sovereign key** (successor if activation occurs; otherwise same as prior).

Kernel/replay verifies it under the derived `sovereign_public_key_active`.

**F3. Self-succession: are both signatures still required?**
Yes. Both records still exist and verify under the same key. Self-succession remains structurally uniform.

**F4. Does kernel ever hold private keys?**
No. Private keys are harness-only. Kernel verifies signatures only.

**F5. Are boundary signatures included in the state hash chain?**
No. They are a **parallel verification layer** over the hash chain.

Reason: including signatures in the state hash chain creates a “signature-of-hash-of-signature” entanglement and complicates purity and replay. Keep them in append-only logs and verify them deterministically during replay.

---

# G — Treaty Suspension & Ratification

**G1. Where to represent suspension state?**
Use **(c) separate X-3 suspension state** in `InternalStateX3`, minimally invasive:

* `suspended_grant_ids: set[grant_id]`

No need to mutate existing `ActiveTreatySet` structure in v0.1.

**G2. `ratify=false` behavior?**
Adopt: `ratify=false → REVOKED (permanent)`.

**G3. Is TreatyRatification kernel-level?**
Kernel-level artifact type. It has its own admission gate and produces a deterministic state delta (moving a treaty from SUSPENDED to ACTIVE or REVOKED).

**G4. Can successor issue new TreatyGrants before resolving suspension?**
No. Binding rule:

* While `suspended_grant_ids` non-empty, reject new TreatyGrants with `SUSPENSION_UNRESOLVED`.

This prevents “freeing density space via suspension and spending it before taking ownership.”

**G5. Ratification schedule semantics?**
`ratification_schedule` specifies **when** ratifications are injected. The generator determines **which** treaties are ratified or revoked deterministically from the session seed and current suspended set.

**G6. Do suspended treaties count toward effective density?**
No (they are non-authorizing). Density accounting uses **ACTIVE** only. Ratification reactivates and must pass density enforcement; if reactivation would breach bound, ratification is rejected:

* `DENSITY_BOUND_EXCEEDED` (or your existing density failure code)

**G7. Self-succession and suspension?**
Self-succession **does not trigger** suspension/ratification (no-op).

---

# H — Prior Key Revocation

**H1. How to inject “post-activation attempt by prior key”?**
Harness injects artifacts signed by the prior key **after** activation in Cycle N+1+, such as:

* a new SuccessionProposal signed by prior key
* a TreatyGrant attempt signed/attributed as sovereign by prior key
* a TreatyRatification signed by prior key

All must deterministically fail.

**H2. Which actions must be tested?**
All of (a), (b), (c). That’s the whole point of “acts as a stranger.”

**H3. Can successor re-grant authority to prior key as delegate?**
Yes. The prior key can become a normal grantee under TreatyGrant, with no sovereign privileges.

---

# I — Replay & State Hash

**I1. How incorporate identity/suspension fields into state hash?**
Use **(b) extend existing components** by ensuring:

* SuccessionProposal artifacts appear in `H_artifacts`
* admission decisions in `H_admission`
* suspension/ratification events appear as executed state transitions (so they affect `H_execution` deterministically)
* lineage counters/tip are included in the canonical internal state that is hashed at cycle end (so they affect the existing end-state hash)

Do **not** add new hash components in v0.1 unless your hash chain architecture already supports extensible components cleanly.

**I2. Are boundary signatures included in state hash?**
No. They are verified from logs (parallel layer), not hashed into state.

**I3. Does replayer need full lineage chain of public keys?**
It reconstructs them from:

* genesis artifact (start)
* admitted SuccessionProposal sequence (log)

No external lineage store required.

**I4. Can X-3 replay reuse X-2D replay harness?**
Yes as a base. X-3 adds:

* boundary record verification
* pending_successor_key and activation logic
* suspension/ratification transitions

Architecture does not need a rewrite.

---

# J — Repo Layout & Module Structure

**J1. Where should harness code live?**
Follow existing convention: `profiling/x3/harness/src/` (align with prior phases).
The earlier “replay/src/” placement was a layout suggestion; align with repo norms to reduce integration friction.

**J2. New kernel modules or extend existing X-2 extension?**
Create `kernel/src/rsax3/` (or equivalent namespace) with:

* `artifacts_x3.py`
* `succession_admission.py`
* `policy_core_x3.py`
* `treaty_ratification.py`
* `state_x3.py`

Keep X-2 code untouched except for a small integration hook where ordering mode dispatches.

**J3. Are schema/profile files created manually or generated?**
Create them as **hand-authored frozen artifacts** (json + schema) like X-2D, then validate programmatically. Do not generate them at runtime.

---

# K — Profiling Families & Scenarios

**K1. Buckets map to families or scenarios?**
Map to **families** (like X-2D), because you need frozen parameterization per class:

* X3-BASE
* X3-NEAR_BOUND
* X3-CHURN
* X3-RAT_DELAY
* X3-MULTI_ROT
* X3-INVALID_SIG
* X3-DUP_CYCLE

**K2. Cycles per family?**
Default 50–80 cycles, but require:

* enough cycles to include rotation(s),
* at least one suspension window,
* at least one ratification window,
* replay verification across boundaries.

**K3. Max rotations per session?**
Cap at a practical deterministic limit, e.g. **max 5**. X-3’s claim needs ≥2, not unbounded churn.

**K4. Rotation during churn — same cycle or adjacent?**
Allow both. Topological ordering makes same-cycle stable, and adjacent-cycle covers boundary sequencing.

**K5. Latency/metrics targets?**
No. X-3 closure is structural (determinism + invariants). Performance profiling is secondary and non-gating unless it threatens determinism.

---

# L — TreatyRatification Artifact

**L1. Should TreatyRatification follow standard artifact pattern?**
Yes. Include:

* `id`, `type="TreatyRatification"`, `created_at`, `author`, `treaty_id`, `ratify`, `signature`, `authority_citations` (optional; if present, resolved in overlay frame)

**L2. Is it a new artifact type?**
Yes.

**L3. What payload is signed?**
JCS-canonicalized dict excluding `signature`.

**L4. One ratification per treaty or many?**
One per treaty (simpler determinism and audit).

**L5. Where in topological ordering?**
Insert after revocations and before density repair:

1 Amendments
2 Const revalidate
3 SuccessionProposal
4 pending_successor_key record
5 Treaty grants
6 Treaty revocations
7 **Treaty ratifications**
8 Density repair
9 RSA actions
10 Delegated actions
11 Warrant issuance
12 Commit

(If you must keep “11 steps,” you can fold warrant issuance into commit, but don’t move ratification after density.)

---

# M — Logging & Metrics

**M1. Results under `profiling/x3/results/` or `logs/`?**
Use `logs/` as the canonical append-only source of truth (consistent with X-0E “self-contained artifact” posture). Harness can also emit a derived summary under `profiling/x3/results/`, but logs are authoritative.

**M2. Where do extended events go?**
Create a dedicated succession trace (recommended) to avoid contaminating X-2 treaty traces:

* `x3_succession_trace.jsonl`
* `x3_ratification_trace.jsonl`

**M3. Summary JSON?**
Yes. Produce `x3_summary.json` as derived output for closure assessment, but never as an input to replay.

---

# N — Gate Instability Instrumentation

**N1. Replay-time or runtime double-run?**
Replay-time comparison is mandatory. Runtime double-run is optional but useful. The binding requirement is: original run vs replay must match gate/code byte-for-byte.

**N2. Apply to which gates?**
All X-3-relevant gates:

* session gates (preconditions/schema)
* S1–S7 succession gates
* ratification gates
* boundary verification

**N3. Separate criterion or subsumed by replay divergence?**
Treat it as **explicit**. Replay divergence can occur without surfacing which gate differed; gate-instability logs are required for attribution and are a hard failure.

---

# O — Interaction with Amendment (X-1)

**O1. Can same-cycle amendment toggle `succession_enabled`?**
Given D1’s choice (S2 snapshot uses prior boundary), **no same-cycle toggling effect** for an already-buffered proposal. Amendments affect succession eligibility starting next cycle.

**O2. Can an amendment be proposed in same cycle as succession?**
Yes. It’s an ordinary ActionRequest path (if that’s how amendments queue). Ordering is already defined: amendment adoption is evaluated before succession admission, but S2 uses prior boundary snapshot for citations.

**O3. Pending amendments across succession?**
Yes. Pending/queued amendments remain in state history and continue to be processed under the same deterministic ordering. Succession does not erase them.

---

# P — Edge Cases

**P1. Successor key equals an existing grantee key?**
Allowed. Roles are tracked independently:

* same Ed25519 key may appear as a grantee identifier and as sovereign identity.
  No collapse; it simply means the sovereign is also a grantee in some treaty graph.

**P2. Can succession occur under DEFAULT ordering?**
No. Succession requires `X3_TOPOLOGICAL` (or an ordering mode that is proven equivalent). If ordering mode is not X-3, reject SuccessionProposal admission with `ORDERING_MODE_INVALID`.

**P3. Succession at cycle 1?**
Allowed. Genesis identity is established before cycle 1 begins (initialization), so a proposal buffered for cycle 1 can be signed by genesis sovereign.

**P4. Max identity_chain_length?**
No hard bound in v0.1. It’s an integer counter; practical caps belong in profiling session limits.

**P5. Must successor key be pre-registered?**
No. Any valid Ed25519 public key is allowed subject to:

* signature gates
* lineage integrity (no reuse unless no-op self)
* constitutional/overlay enablement

---

## Implementation takeaway

The key decisions that matter for coding correctness:

1. **Genesis is a frozen artifact** (not a session param, not a constitution edit).
2. **Kernel never signs**; harness signs commit/start records; kernel verifies.
3. **S2 uses prior-boundary constitutional frame** (v0.3 + frozen overlay).
4. **Suspension blocks new grants until resolved** (`SUSPENSION_UNRESOLVED`).
5. **Suspended treaties do not count toward density**; ratification must pass density.
6. **Self-succession is a no-op** (no suspension, no chain increment).
