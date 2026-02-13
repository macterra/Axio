## A — Constitution Version & Freeze Scope

**Q1. v0.1.1 only vs any frozen constitution? Kernel snapshot?**
**Answer:** X-0E is **constitution-version-agnostic** *in principle*, but **the closure run for X-0E v0.1** is pinned to **Frozen Constitution v0.1.1** as the required test vector.
So: support any frozen constitution file + sidecar **mechanically**, but certify closure against **v0.1.1**.

**Q1(a/b/c):** Choose **(c)** plus a **required closure target**: v0.1.1.

**Q2. Strip X-1/X-2 extensions or leave dormant?**
**Answer:** **Do not strip**. Keep current kernel code; the constitution determines which paths are exercised. X-0E is an *embodiment freeze*, not a historical rollback. Your determinism constraints are about behavior under the chosen constitution + inputs.

**Q3. Copy constitution+sidecar under x-0e/ or reference shared directory?**
**Answer:** **Reference the shared canonical location. Do not duplicate.** Duplication creates drift risk. X-0E should take a `--constitution` path and hash-verify it in place.

---

## B — Repo Layout & File Organization

**Q4. Refactor layout vs parallel tree vs build output?**
**Answer:** **(b) Wrapper/imports + minimal re-org.** X-0E should be a CLI surface and packaging profile that composes existing `host/` + `replay/` with targeted edits. No big refactor during a freeze milestone.

**Q5. Canonicalization/state hashing duplication vs shared module?**
**Answer:** **(a)+(c):** Promote canonicalization + hashing into a shared module (single source of truth) and have replay import it from there. No duplicate implementations.

**Q6. net_guard mechanism?**
**Answer:** For X-0E, **process-level refusal is sufficient**:

* no network-enabled action types exist;
* replay/run must not perform network calls;
  Implement a **best-effort Python guard** (monkeypatch `socket` to raise) behind a flag, but treat it as defense-in-depth, not part of determinism.

---

## C — Warrant Determinism & ID Derivation

**Q7. Spec formula vs existing code hashing full warrant dict? Separator?**
**Answer:** Bind to **one canonical rule**:

> `warrant_id = SHA256(JCS(warrant_payload_without_warrant_id))`

This is the only sane cross-language rule and aligns with your broader JCS mandate. Your four-field concatenation is underspecified (separators, encoding, typing). Replace it operationally with “hash canonical warrant payload”.

**Q8. selector_rank type?**
**Answer:** Treat as **integer** in the warrant payload, serialized via JCS (so it becomes unambiguous).

**Q9. cycle_id type?**
**Answer:** Treat as **integer**. If you ever migrate to a hash, do it in a new phase. X-0E wants minimalism.

---

## D — State Hash Chain

**Q10. Chain inputs, concatenation, ordering, multiple artifacts?**
**Answer:** Use a **hash-of-hashes chain**, with per-cycle component hashes computed via JCS.

Define per cycle:

* `H_artifacts[n] = SHA256(JCS(list_of_artifact_log_records_for_cycle_n_in_append_order))`
* similarly for admission/selector/execution traces **restricted to that cycle**

Then:

```
state_hash[n] = SHA256(
  state_hash[n-1] ||
  H_observations[n] ||
  H_artifacts[n] ||
  H_admission[n] ||
  H_selector[n] ||
  H_execution[n]
)
```

Ordering rule: **append order within each log file** for that cycle. No selector-rank re-sorting. The log is the ground truth.

**Q11. kernel_version_id definition?**
**Answer:** For X-0E, make it **a manually maintained semantic string** in code (e.g., `"rsa-kernel-x0e-v0.1"`), plus optionally emit the git commit in logs as non-binding metadata. Do **not** define it as “hash of source tree” (non-portable, build-dependent).

---

## E — Canonicalization (JCS Compliance)

**Q12. Current canonical_json vs proper JCS?**
**Answer:** **(b)**: use a real JCS library and treat it as a pinned dependency. Your current method is “close” but not a spec. X-0E is exactly where you stop hand-waving.

If you want a binding choice: pick **one** library and pin it. If none are acceptable, implement JCS fully yourself, but that’s more surface area and more bug risk.

**Q13. YAML→JSON canonical conversion concerns?**
**Answer:** The canonical bytes for hashing must be:

1. `yaml.safe_load()` into Python primitives
2. Convert to JSON value tree (dict/list/str/int/bool/null) with **no floats allowed** (assert)
3. Apply **JCS** to that JSON tree

Dict ordering is irrelevant because JCS canonicalizes it. Different YAML parsers producing different value trees is the real risk; constrain the constitution to a subset that parses identically (no anchors, no tags, no floats). Enforce with validation.

---

## F — Observation Stream & Test Vector

**Q14. Observation format without LLM?**
**Answer:** X-0E uses **pre-baked observation payloads** that already contain the complete candidate material needed for admission (e.g., an `ActionRequest` artifact plus required companion artifacts). No generation step.

So choose **(a)**: observations are JSONL records whose payload includes **fully formed artifacts**.

**Q15. “Independent machines” minimum bar?**
**Answer:** Minimum bar: **same OS family, clean environment, pinned deps** (two separate runs on two separate hosts or containers with empty state).
Stretch goal: different OS/platforms. Don’t require it for X-0E closure or you’ll turn freeze into portability engineering.

**Q16. Observation vs CandidateBundle mismatch?**
**Answer:** Observation envelope must carry a **CandidateBundle-equivalent payload** (ActionRequest + ScopeClaim + authority_citations + justification) as artifacts. X-0E does not introduce a new simplified path; it supplies the existing pipeline with deterministic inputs.

---

## G — Outbox & Idempotency

**Q17. timestamp source?**
**Answer:** Extend observation envelope to include explicit `timestamp`. Do not “extract by convention” from payload.

**Q18. Synthetic reconciliation entry affects state hash?**
**Answer:** Yes. Reconciliation changes the effective execution trace; therefore it must be reflected in the hash chain **via the execution_trace entries it appends**. The separate reconciliation_trace is advisory.

**Q19. Is reconciliation_trace included in hash chain?**
**Answer:** No. Keep the chain anchored to the five primary logs. Reconciliation_trace exists to explain why an execution_trace entry was synthesized. The authoritative state is still execution_trace.

---

## H — Execution & Host Boundary

**Q20. Strip other actions or keep?**
**Answer:** **(a)** Refuse everything except Notify in X-0E packaging. This reduces attack surface and prevents accidental “helpful” execution.

**Q21. Notify writes where?**
**Answer:** Implement Notify to write to **outbox.jsonl** exactly. If current Notify appends elsewhere, redirect or replace it.

**Q22. Host loading constitution: allowed?**
**Answer:** Host may load constitution **only for integrity verification** and to pass bytes into kernel. “Interpret” means “make decisions from it.” Host must not branch on constitutional semantics.

---

## I — Replay Architecture

**Q23. Upgrade existing replay.py or new replayer?**
**Answer:** **(a)** Upgrade existing replay harness to include chain verification and reconciliation simulation. Avoid parallel implementations.

**Q24. How verify execution outcomes in replay?**
**Answer:** **(b)** Replay verifies structural consistency:

* every SUCCESS execution has a valid recomputed warrant
* no execution exists without warrant
* if an execution is logged FAILURE, outbox must not contain that warrant_id
  Replay does not “predict” disk-full; it checks coherence between logs and destination ledger (outbox).

**Q25. Reconciliation during replay?**
**Answer:** Replay recomputes what reconciliation *should have done* from the log state and verifies:

* execution_trace contains the synthesized entries where required
* reconciliation_trace (if present) matches the computed set
  So: **simulate + verify**, not “skip.”

---

## J — Packaging & Pinning

**Q26. Pinning mechanism?**
**Answer:** Use **(d)** pragmatically:

* `pyproject.toml` + lock (or requirements.txt pinned)
* plus an optional Dockerfile for reproducible runs
  For freeze, the binding requirement is: **a lockfile-equivalent artifact exists and is used in CI**.

**Q27. Kernel version mismatch detection?**
**Answer:** Use the **manual semantic kernel_version_id string** embedded in code and logged at run start. Replay refuses if it differs from the logged value. Optionally add git commit as non-binding metadata.

**Q28. x-0e_profile.v0.1.json content?**
**Answer:** Minimal packaging manifest:

* kernel_version_id
* constitution_path
* constitution_hash
* dependency lock hash (hash of lockfile)
* action surface list (Notify only)
* log schema versions
* JCS library + version
* CLI commands + expected log files

It’s not a profiler. It’s a **freeze manifest**.

---

## K — Test Suite Scope

**Q29. Minimum vs complete set?**
**Answer:** The list is **minimum**. Yes, add:

* constitution integrity edge cases
* log schema validation failures
* multi-cycle runs
* restart determinism and warrant determinism across restarts

**Q30. Cross-machine replay in CI?**
**Answer:** Use **two clean containers** in CI as the minimum “independent machine” proxy:

1. container A runs `rsa run` producing logs
2. container B runs `rsa replay` on copied logs
   No need for physical hardware separation at this phase.

---

## L — Relation to Existing Profiling Harnesses

**Q31. profiling/x0e/ needed?**
**Answer:** **(b)** The CLI is the harness for X-0E closure. You may add a thin test wrapper, but don’t create a new profiling subsystem.

**Q32. No model calls: same as test vector or more?**
**Answer:** Same mechanism as test vectors, expanded scenario set. X-0E’s “profiling” is just running longer deterministic pre-baked sequences.

---

## M — Scope Boundaries & Edge Cases

**Q33. “No new invariants” vs new behaviors (outbox, reconciliation, hash chain)?**
**Answer:** Classify them as **host-layer embodiment constraints**, not new kernel invariants. The kernel’s authority physics is unchanged; you are freezing packaging and audit guarantees.

Also: §17.7 “kernel byte-for-byte identical to X-0” is now misleading in a repo that has moved on. Update interpretation: it means **no semantic changes to the kernel’s authority rules**, not literally the historical file snapshot. If you want literal byte identity, you need a tagged artifact. Otherwise it’s unenforceable.

**Q34. Is reconciliation log write a “side effect” requiring warrant?**
**Answer:** No. Reconciliation is **host infrastructure journaling**, not an externally meaningful action. Treat it like log append, not like an RSA “act.”

**Q35. Crash mid-cycle recovery behavior?**
**Answer:** For X-0E, enforce **cycle atomicity at the boundary**:

* On restart, re-run the cycle deterministically from logs.
* Any partially admitted artifacts are already in logs; if not logged, they did not happen.
* Execution idempotency prevents duplication.
  So: **re-run from last completed logged cycle**, not “resume mid-cycle” with hidden state.

---

# One Meta-Fix You Should Make (Binding)

Your spec and instructions still contain one landmine: the *old four-field warrant_id formula* vs “hash canonical warrant payload.”

Pick one and freeze it.

My recommendation (and binding choice for implementation instructions) is:

> `warrant_id = SHA256(JCS(warrant_payload_without_warrant_id))`

It eliminates Q7–Q9 ambiguity and aligns with RFC 8785 everywhere.

---

Answering Q36–Q47 with **binding implementation decisions**. Where this forces a choice, I’ll pick the one that preserves X-0E’s core properties: **deterministic replay from logs**, **minimal refactor**, **freeze-grade clarity**.

---

## Q36 — Guarding dormant X-1/X-2 code paths under v0.1.1

**Binding answer:** X-0E requires **graceful degradation** when optional constitution sections are absent.

Implementation rule:

* Constitution parsing must produce an internal config object with **explicit optionals**:

  * `amendment_procedure: Optional[...]`
  * `treaty_system: Optional[...]`
  * etc.
* Any X-1/X-2 gate/code path must begin with a deterministic guard:

  * `if section is None: REFUSE / NOT_APPLICABLE` (depending on context)
* No missing-key exceptions may occur when running v0.1.1.

So: if you don’t already degrade gracefully, **this is a required code change before X-0E closes**.

---

## Q37 — Where the shared canonicalization + hashing module lives

**Binding answer:** Put it in **kernel namespace** and import from there everywhere.

Choose **(a)**:

* `kernel/src/canonical.py` (JCS encode + SHA primitives + helpers)
* `kernel/src/hashing.py` (artifact_hash, warrant_id_hash, per-cycle component hash, chain hash)

Rationale: replay and host importing kernel utilities is acceptable in X-0E because the kernel is the single source of truth for determinism rules. Creating a new top-level `shared/` invites drift.

---

## Q38 — Does X-0E mandate JCS everywhere hashing occurs (retroactive change)?

**Binding answer:** **Yes, for all hash computations that participate in X-0E determinism and replay.** That means:

* `artifact_hash()` must use JCS.
* `ExecutionWarrant._compute_id()` must use JCS.
* Any other IDs/hashes used in:

  * logs,
  * warrant derivation,
  * state hash chain,
  * replay verification,
    must use JCS.

However: you are **not retroactively changing the meaning of old logs**. Old logs remain replayable only under the old hashing rules **if and only if** they carry their own “hashing regime” marker (see Q40). If they don’t, then changing hashing breaks replay for older artifacts. That’s acceptable only if X-0E is treated as a new freeze boundary (it is).

So: implement JCS universally going forward in the X-0E packaging path; don’t promise old log compatibility unless you add explicit regime tagging.

---

## Q39 — Observations in the state hash chain or not?

**Binding answer:** Follow the spec text unless amended: **do not include observations** in the chain *for v0.1*.

So: implement §11 exactly as written:

```
state_hash[n] = SHA256(
  state_hash[n-1] ||
  artifacts[n] ||
  admission_trace[n] ||
  selector_trace[n] ||
  execution_trace[n]
)
```

But: **require that the artifacts/admission/selector traces already commit to observation identity** (e.g., `cycle_id`, deterministic timestamp, observation_id) so observations are indirectly committed. If they aren’t, add those fields to the trace entries (you already require them).

If you want observations explicitly in the chain, that is a **spec revision**, not an implementation choice.

---

## Q40 — What is kernel_version_id tied to?

**Binding answer:** It is tied to the **replay semantics regime**, not “the repo” and not “the constitution”.

Choose **(a)** with a sharper definition:

* `kernel_version_id` changes only when:

  * hashing/canonicalization rules change,
  * warrant derivation rules change,
  * state hash chain rules change,
  * admission/selector determinism semantics change,
  * log schema meaningfully changes in a way that affects replay.

It does **not** change for:

* adding dormant modules,
* adding new phases that are not exercised under the chosen constitution,
* code refactors that preserve semantics.

Old logs must remain replayable under the same `kernel_version_id` regime.

This is exactly why `kernel_version_id` must be defined as a **semantic protocol ID**, not “git commit”.

---

## Q41 — Which specific Python JCS library is approved?

**Binding answer:** Use **`canonicaljson`** (Matrix) **only if** it is RFC 8785 compliant for your data types; otherwise use a direct RFC 8785 implementation or implement JCS yourself.

But you asked for a single approved choice. So here’s the binding path:

1. **Adopt `canonicaljson`** as the dependency **if** it produces RFC 8785-compliant canonical bytes for your JSON value subset (strings, ints, bool, null, arrays, objects; and ideally floats too).
2. If it does not, then adopt a direct RFC 8785 library (`jcs`) **or** implement JCS yourself.

Given X-0E’s freeze intent, you should **constrain your value subset** (see Q42) so `canonicaljson` is sufficient.

So: **approved default = `canonicaljson`**, pinned, plus a conformance test vector.

---

## Q42 — Floats in constitution: forbid or support?

**Binding answer:** **Support floats correctly** if they appear. Choose **(b)**.

Reason: you explicitly want constitution-version-agnostic mechanical support. A blanket float prohibition will fail future constitutions for no sovereignty reason.

So:

* YAML→Python primitives may include floats.
* JCS implementation must handle floats per RFC 8785.
* Add a validation rule that forbids NaN/Inf and forbids non-finite floats.
* Prefer authoring numeric thresholds as rationals/decimals only if you want extra rigor, but do not make it a load-time refusal unless you freeze that as a constitutional authoring constraint.

---

## Q43 — Reconciliation appends execution_trace after crash: hash chain differs vs clean run?

**Binding answer:** This is acceptable and correct.

X-0E does **not** require the hash chain to be invariant across “idealized crash-free” and “crash occurred” histories.

It requires:

> Replay reproduces the **actual** execution history represented by the logs.

A crash is part of history. Reconciliation produces extra log entries. Therefore the canonical state chain for that run includes them.

So:

* A crash-free run and a crash-then-reconcile run are **different executions**, yielding different state hash sequences.
* Replay must reproduce whichever one actually happened (i.e., whichever logs exist).

That’s consistent with your determinism claim: determinism is conditioned on log stream.

---

## Q44 — “Notify only” vs LogAppend used by host to write logs

**Binding answer:** `LogAppend` is **host infrastructure**, not an RSA action type in X-0E.

So:

* The RSA action surface (warranted actions) is Notify-only.
* Logging is not performed via a warrantable `LogAppend` action at all.
* The host writes logs directly as part of the runtime substrate, append-only.

If your current architecture routes logging through an action type, refactor it for X-0E: logging must be outside the warranted action set, or you’ll conflate “doing a sovereign act” with “keeping a journal”.

---

## Q45 — How is the freeze manifest produced?

**Binding answer:** Choose **(c)**: generated by a **separate `rsa freeze` / build step**, not by `rsa run`.

Why:

* `rsa run` must not mutate artifacts/ (spec rule).
* The manifest is an artifact, not a runtime byproduct.
* Freeze should be deliberate and reproducible.

So:

* `rsa freeze --constitution ... --out artifacts/phase-x/x-0e/x-0e_profile.v0.1.json`
* The manifest is checked in (or at least shipped) as part of the distribution.

`rsa run` may *print* the manifest fields or log them, but not write artifacts.

---

## Q46 — Deliverables include Dockerfile / CI workflow?

**Binding answer:** **(c) Both**, in minimal form.

Because X-0E’s closure criteria include cross-machine parity; without containers/CI, you will not actually enforce it.

Deliver:

* Dockerfile that pins Python + deps lock.
* GitHub Actions workflow that:

  1. builds container,
  2. runs `rsa run` on test vector in container A,
  3. copies logs to container B,
  4. runs `rsa replay`,
  5. compares hash sequences.

Keep it minimal. The point is reproducible certification.

---

## Q47 — §17.7 “kernel byte-for-byte identical to X-0” reinterpretation vs amendment

**Binding answer:** **Amend the spec text before implementation.**

Proceeding with a “relaxed interpretation” while leaving literal contradictory text is how specs rot.

Minimal amendment:

Replace §17.7:

> “Kernel byte-for-byte identical to X-0.”

With:

> “Kernel authority semantics identical to X-0 under the X-0E closure constitution and test vector; no authority-rule changes are permitted in X-0E.”

If you truly need byte identity, then you must define the byte target (tagged commit hash, artifact digest). Otherwise it’s not enforceable.

Given you’re already beyond X-0, semantic identity is the only coherent requirement.

---

# One additional binding note (not asked, but implied)

You now have *two* “version IDs”:

* `constitution_hash` (frozen input)
* `kernel_version_id` (replay semantics regime)

Do **not** mix them. The constitution is data; the kernel version is protocol. Keep both recorded in logs and in the freeze manifest.

---

Answering Q48–Q59. Two constraints matter here:

* I **cannot see your repo** (no tool access to it in this thread), so I cannot assert what `kernel/src/constitution.py` currently does. I’ll give **binding decisions + concrete implementation patterns** you can apply regardless of current state.
* X-0E is a **freeze milestone**. Anything that threatens scope creep gets pushed into **a preparatory refactor PR**.

---

## Q48 — Does constitution parser already degrade gracefully? How extensive are guards?

I can’t verify current behavior without the code. Treat it as unknown.

**Binding requirement:** Constitution parsing must return a typed object where absent sections map to `None`, and no downstream code may assume presence.

**Where to add guards:**
Add them at **phase entry points and gate dispatch**, not scattered everywhere.

Concretely:

* In `constitution.py`: parse into `Constitution` with `Optional` fields defaulting to `None`.
* In `policy_core` / gate router: when a feature is requested (amendment, treaties), enforce:

  * if constitution section missing → deterministic refusal (`NOT_APPLICABLE` or `MISSING_CONSTITUTION_SECTION`)
  * do *not* allow deeper functions to be called with missing config.

This localizes the changes to:

* constitution parser
* the X-1/X-2 gate dispatch / feature activation checks

If you find missing-section assumptions scattered throughout, that is an architectural smell; fix by moving those checks up, not sprinkling try/except.

---

## Q49 — Move canonicalization/hashing module: preparatory refactor vs part of X-0E?

**Binding answer:** Do it as a **preparatory PR**, before X-0E implementation proper.

Reason: X-0E already changes canonicalization semantics (JCS) and adds hash-chain rules. If you mix “move files” with “change meaning”, code review becomes un-auditable.

So:

* PR0: mechanical refactor (move functions, update imports), **no semantic change** (still the old canonicalization).
* PR1: semantic change to JCS + warrant ID + hash chain + X-0E CLI/package.

---

## Q50 — JCS migration breaks fixtures: how to migrate tests?

**Binding answer:** **(c)** plus a small carve-out.

* Stop hardcoding hashes in fixtures wherever feasible.
* Compute expected hashes via the canonical functions in the shared module.

Carve-out: for **freeze-grade conformance tests** (e.g., “this artifact hashes to this hex under JCS”), keep a **small number** of hardcoded known-answer vectors. Those become your portability anchors.

So: mostly dynamic expectations; a few “golden vectors” explicitly pinned.

Do this migration in the **same PR as the JCS semantic change** (PR1), not before. Otherwise you’ll be updating tests for a behavior you haven’t landed.

---

## Q51 — Confirm state hash chain formula excludes observations

**Yes. Binding formula for X-0E v0.1:**

```
state_hash[n] = SHA256(
  state_hash[n-1] ||
  H_artifacts[n] ||
  H_admission[n] ||
  H_selector[n] ||
  H_execution[n]
)
```

Observations excluded from the chain **explicitly**, per §11.

But ensure each trace record includes `cycle_id` and deterministic timestamp derived from observation so the chain is still cycle-grounded.

---

## Q52 — kernel_version_id vs pre-X-0E logs

**Binding answer:** Pre-X-0E logs are **outside the X-0E replay regime** unless they already contain enough metadata to interpret them under an older regime.

Given your description, assume they do not.

So:

* Define `kernel_version_id = "rsa-replay-regime-x0e-v0.1"` (or similar).
* X-0E replay refuses logs that do not declare this regime (or that declare a different one).
* Do not attempt retroactive compatibility unless you explicitly add regime tagging to old logs and preserve the old hashing semantics in code.

This is consistent with “freeze boundary”: X-0E is the moment where replay becomes audit-grade and formally versioned.

---

## Q53 — canonicaljson returns bytes: what should shared module expose?

**Binding answer:** **(a)** expose both, bytes-first.

Provide:

* `canonical_bytes(value) -> bytes`  (primary)
* `canonical_str(value) -> str` (thin wrapper `bytes.decode("utf-8")`)

Hashing functions must take bytes and return bytes/hex deterministically.

This minimizes churn while making the canonical substrate unambiguous.

---

## Q54 — Float normalization (1.0 vs 1) and YAML parsing

**Binding answer:** Do **not** normalize numeric types during YAML→Python loading. Accept that `1` and `1.0` are distinct inputs and may canonicalize differently.

That is correct: the constitution bytes (post-parse) define the law. If you normalize, you create hidden semantics (“these are the same”) which is exactly what you are trying to avoid.

**Additional binding constraint:**

* Forbid NaN/Inf and non-finite values at load time.
* If you want to discourage floats in constitutions, do it as an authoring guideline, not a semantic rewrite.

---

## Q55 — Clean run determinism vs crash determinism tests

**Binding answer:** Yes: the §15 cross-machine determinism test vector is a **clean run**.

Crash recovery gets its own test category:

* Unit/integration tests that simulate crash points and assert:

  * reconciliation entries are generated deterministically
  * replay matches the post-crash log history

Optionally, define a **separate “crash test vector”** with its own expected hash sequence, but don’t require it for the “two independent machines” bar unless you want to expand closure scope.

So: clean vector for closure; crash scenarios as integration tests.

---

## Q56 — Refactor LogAppend out of warrant path: which approach? kernel changes?

**Binding answer:** **(c)** move log-writing to host infrastructure, not routed through executor-as-action.

Consequences:

* `LogAppend` should not be in the warranted `ActionType` set for X-0E.
* Whether you remove it from the enum depends on blast radius:

  * If removal touches many phases, keep it in the enum but make it **unreachable** in X-0E (refuse if requested).
  * If you can remove cleanly, remove it.

**Kernel changes:** ideally **none**. The kernel should never need to “authorize logging”. Logging is the substrate’s journaling, not an agent action.

So in X-0E packaging:

* kernel emits log records to host logger interface
* host appends them append-only
* no warrants involved

---

## Q57 — `rsa freeze` command vs spec defining only run/replay

**Binding answer:** Choose **(c)**: it’s part of the **build/packaging process**, not a runtime command.

So:

* Don’t add `rsa freeze` to the CLI unless you update the spec.
* Implement manifest generation as:

  * `scripts/generate_x0e_manifest.py` or a `make freeze-x0e` target, run during packaging.
* `rsa run` and `rsa replay` remain the only required commands.

(If you later want an official CLI command, amend spec §4.1 and bump version. Not now.)

---

## Q58 — Scope of GitHub Actions workflow

**Binding answer:** **(a)** plus minimal sanity.

X-0E’s CI must guarantee the property you’re freezing:

* build pinned env/container
* run the X-0E deterministic test vector
* replay in a second clean container and compare hash sequence

Also run a *minimal* pytest subset necessary for X-0E (smoke tests). Do not take responsibility for “all 478 tests” unless you already have that stable; you’ll turn X-0E into CI archaeology.

So: cross-machine replay is mandatory; full suite is optional later.

---

## Q59 — Who amends the spec, and does it block coding?

**Binding answer:** The implementation agent should propose the amendment as a **separate doc PR** editing the spec source (`docs/.../X-0E.md` or wherever it lives). This amendment **must be merged before you declare implementation “X-0E compliant.”**

Can coding proceed in parallel? Yes, but only for mechanical scaffolding (repo layout, CLI plumbing). Any work that depends on §17.7 interpretation (kernel identity) should wait until the spec text is corrected, because that’s exactly where disagreements become expensive.

So:

* PR-SPEC: amend §17.7 (and any other clarified points you want baked in).
* PR-IMPL: implement against amended spec.

---

# One consolidated recommendation

You’re converging on an implementation plan that should be split into three PRs:

1. **PR0 (mechanical refactor):** relocate canonicalization/hashing helpers; no semantic change.
2. **PR-SPEC (text fix):** amend §17.7 and any other binding clarifications you’ve adopted.
3. **PR1 (X-0E semantics):** JCS, warrant_id rule, state hash chain, reconciliation, Notify-only, CLI run/replay, two-container CI.

That sequencing prevents you from mixing refactors with semantic freezes.

Answering Q60–Q72 with binding decisions. I’ll keep it implementation-grade and bias toward **single-source determinism** + **minimal blast radius**.

---

## Q60 — Where refusal happens for “unsupported capability” actions

**Binding answer: (c) both, but with clear responsibility.**

* **Primary enforcement:** admission gate level (closed action set + constitutional prohibitions).
* **Secondary enforcement:** a **capability pre-dispatch** check only for *feature families* whose absence would otherwise cause missing-section errors.

Why:

* For `AmendConstitution` specifically, the v0.1.1 constitution already forbids it, so the normal compliance gates should refuse it. That’s the correct place.
* The explicit “missing section” guards are for cases where **code would otherwise dereference absent config** (e.g., treaty resolver assumes `treaty_system` exists). Those should be blocked *before* deeper logic.

So: don’t add a global “capabilities router” for everything. Add a **small set of pre-dispatch guards** only at the entry to X-1/X-2-specific evaluators.

---

## Q61 — PR0 refactor: add shim or clean cut?

**Binding answer:** Add a **compatibility shim** for one release cycle.

In PR0:

* Move implementation to `kernel/src/canonical.py` (and hashing to `kernel/src/hashing.py`).
* Keep `kernel/src/artifacts.py` exporting:

  * `canonical_json`, `canonical_json_bytes`, `artifact_hash`

as thin wrappers calling the new module.

This avoids a “15+ file import change” PR that obscures the semantic freeze PR. Then, once PR1 lands and stabilizes, you can remove the shim in a later cleanup PR.

---

## Q62 — How many golden vectors?

**Binding set:**

1. **One JCS conformance suite** (subset)

   * Use a handful of edge cases relevant to your data: unicode, nested objects, arrays, ints, floats, escaping.
2. **One per hash primitive**

   * Artifact hash golden vector for at least: `ActionRequest`, `ExecutionWarrant`.
3. **One end-to-end X-0E closure vector**

   * The §15 minimal run including the **state hash chain**.

So: **(b) yes**, plus **targeted (a)** and a small **(c)** subset. You don’t need one per every artifact type if they all share the same canonicalization/hashing path, but you *do* want coverage of distinct serialization shapes (string-heavy vs numeric-heavy).

---

## Q63 — `||` concatenation: hex strings or raw bytes?

**Binding answer:** **raw bytes**.

* Each component hash is 32 raw bytes.
* Concatenate the bytes (5 × 32 = 160 bytes per cycle input block).
* SHA-256 over that 160-byte block.

Never concatenate hex strings. Hex introduces encoding ambiguity and doubles length for no benefit.

So: `state_hash[n] = SHA256(prev_bytes || H_artifacts_bytes || H_admission_bytes || H_selector_bytes || H_execution_bytes)`.

---

## Q64 — Backward compatibility for replay with pre-X-0E logs

**Binding answer:** **(b)** freeze legacy replay and build X-0E replay mode explicitly.

Do not contort X-0E replay to support unversioned logs. That creates implicit regime detection, which is an anti-audit pattern.

Implementation:

* `replay_legacy.py` (unchanged, for X-0P/X-0L historical runs)
* `replay_x0e.py` (versioned, regime-enforcing, hash-chain verifying)

If you want one CLI entrypoint, it can dispatch based on the presence of `kernel_version_id` in the log header, but the code paths remain separated.

---

## Q65 — Rename `artifact_hash()` to reflect JCS?

**Binding answer:** Keep the name **for continuity**, but tighten the docstring and ensure it is defined as:

> `artifact_hash := SHA256(JCS(artifact_json_value))`

If you rename, you’ll create unnecessary churn across phases and harnesses. The *meaning* is what matters; pin it in documentation and tests.

---

## Q66 — If JCS canonicalizes 1.0 to 1, does “distinct inputs” matter?

Correct: **the distinction is lost at the canonical byte layer** for those representations. Under RFC 8785, certain floats serialize as integers if they are mathematically integral. If `canonicaljson` does that, then `{"x":1}` and `{"x":1.0}` hash identically.

**Binding stance:** This is acceptable.

Reason: Your security property is determinism and auditability, not preserving syntactic authoring distinctions. If two inputs canonicalize to the same JCS, they are definitionally the same canonical object for hashing purposes.

So revise the mental model:

* Inputs may differ pre-canonicalization.
* The freeze substrate is the **canonicalized value**. That’s what is committed.

Do still forbid NaN/Inf.

---

## Q67 — How to implement crash simulation tests?

**Binding answer:** Use **(c)** plus one targeted (a). Avoid (b) for now.

* Primary: construct log/outbox files manually to represent crash states and run reconciliation + replay.

  * This is deterministic, fast, CI-friendly.
* Secondary: mock file I/O for the “partial write” edge (e.g., outbox contains warrant_id, execution_trace missing).

  * Do not rely on OS-level kill timing.

Subprocess killing is flaky and turns tests into probabilistic timing games, which violates the spirit of X-0E.

---

## Q68 — Host log-writing interface: where should it live?

**Binding answer:** **(c)** a simple `append_jsonl(path, record)` utility, used by the host loop directly.

Put it in `host/log_io.py` or similar.

Do **not** put it on the executor as a privileged bypass. That reintroduces “hidden authority channel” ambiguity. Logging is substrate I/O, not an action.

---

## Q69 — Scripts vs Makefile

**Binding answer:** **(a)** standalone Python scripts in a new `scripts/` directory.

A Makefile is optional. Introduce it only if you already have strong convention for it. For X-0E, you need:

* `scripts/generate_x0e_manifest.py`
* optionally `scripts/run_x0e_vector.py` (just calls CLI)

CI will call Python directly anyway.

---

## Q70 — Minimal pytest subset for CI

**Binding answer:** **(a)** only X-0E-specific tests, plus one smoke test that imports and initializes the kernel.

Rationale: CI scope creep kills freeze schedules and produces brittle pipelines. X-0E is certifying a specific property; test what you freeze.

So CI stages:

1. `pytest -k x0e` (or tests under `tests/x0e/`)
2. cross-container run/replay determinism check

If you want broader coverage later, expand CI after freeze.

---

## Q71 — Amend spec minimally or roll all clarifications into v0.2?

**Binding answer:** Keep it **minimal** for v0.1: amend §17.7 only.

Do not roll the whole Q&A into a v0.2 spec unless you are willing to bump version and treat it as a new freeze candidate.

Operationally:

* The Q&A answers act as the binding supplement for implementation.
* The spec stays v0.1 with the one text correction that prevents contradiction.

If you later want a consolidated spec, do it as v0.2 after X-0E closes.

---

## Q72 — PR dependency ordering

**Binding answer:** **(c)** PR0 and PR-SPEC can run in parallel; both must merge before PR1.

* PR0 (refactor shims) must land before PR1 (semantic changes) to avoid noisy diffs.
* PR-SPEC (text fix) must land before PR1 is declared compliant, but it can merge independently of PR0.

So: PR0 + PR-SPEC → PR1.

---

Answering Q73–Q80 with binding decisions. I’ll resolve the contradictions explicitly and lock down the encoding/IO details so cross-implementation parity is not left to convention.

---

## Q73 — Single replay vs split legacy/new replay

**Binding answer: (b)** two separate implementations with a thin dispatcher.

* `replay_legacy.py` remains frozen for pre-X-0E logs.
* `replay_x0e.py` implements the X-0E regime (versioned, JCS, hash chain, reconciliation).
* A thin CLI entrypoint (`rsa replay`) dispatches based on log metadata (presence/value of `kernel_version_id`).

This resolves the A23/A64 conflict: A23’s “upgrade existing replay” is superseded by the later, more audit-stable choice. The split avoids “dual semantics in one file” entropy.

---

## Q74 — Naming conventions: canonical_bytes/str vs canonical_json(_bytes)

**Binding answer:** Keep the old names as a compatibility surface **indefinitely**, and standardize new code on the new names.

Concretely:

* `kernel/src/canonical.py` exports:

  * `canonical_bytes(value) -> bytes`
  * `canonical_str(value) -> str`
* `kernel/src/artifacts.py` keeps:

  * `canonical_json(value) -> str`   (calls `canonical_str`)
  * `canonical_json_bytes(value) -> bytes` (calls `canonical_bytes`)

Do **not** rename the shim exports in PR1. Renaming is pure churn with no determinism benefit.

Rule: new code uses `canonical_bytes`; legacy call sites can stay untouched.

---

## Q75 — Initial state hash concatenation: constitution_hash (32 bytes) + kernel_version_id (string)

**Binding answer:** Hash the string to 32 bytes first.

Define:

* `constitution_hash_bytes`: 32 bytes
* `kernel_version_id_bytes = UTF8(kernel_version_id)`
* `kernel_version_hash = SHA256(kernel_version_id_bytes)` (32 bytes)

Then:

```
state_hash[0] = SHA256(constitution_hash_bytes || kernel_version_hash)
```

This keeps the “hash-of-fixed-width-blocks” discipline and prevents encoding ambiguity. Do not concatenate variable-length UTF-8 directly.

---

## Q76 — Where golden vectors live

**Binding answer: (b)** store as JSON fixtures under `tests/fixtures/`.

Structure:

```
tests/fixtures/jcs_vectors/
  action_request_01.json
  action_request_01.sha256
  execution_warrant_01.json
  execution_warrant_01.sha256
  x0e_end_to_end_vector/
    observation_stream.jsonl
    expected_state_hashes.jsonl
```

Tests load JSON, canonicalize, hash, compare to expected hex.

Reason: fixtures are reviewable, stable, and usable across languages later.

Do not put golden vectors under `artifacts/` (those are “law”, not tests).

---

## Q77 — append_jsonl enforcement (fsync/locking/append-only) + replay readers

**Binding answer: (d) all of the above**, with one nuance: file locking is required only if you allow concurrency.

### `append_jsonl()` must enforce

1. **Append-only open**

   * open with `"ab"` (binary append) or `"a"` with explicit encoding; prefer binary append with UTF-8 bytes.
   * never `"w"`.

2. **Atomic append discipline**

   * write exactly one line: `canonical_bytes(record)` (or normal JSON, but deterministically encoded) + `b"\n"`.

3. **fsync for crash safety**

   * `flush()` + `os.fsync(fd)` after each entry for the core logs involved in replay guarantees (`execution_trace`, `outbox`, and optionally the main traces).
   * If performance becomes an issue later, introduce batching as a new phase; X-0E prioritizes correctness.

4. **Locking**

   * If the host is single-process single-writer (likely), locking can be omitted.
   * If there is any chance of concurrent writers, require an advisory lock (platform-specific). For X-0E, you should enforce “single writer” as a runtime assumption and assert it.

**Replay reading:** replay should **not** reuse `log_io.py` for writes (obviously), but can reuse a shared **reader** utility for JSONL parsing. Keep write primitives isolated; reads can be shared.

---

## Q78 — dependency_lock_hash without a lockfile

**Binding answer:** X-0E deliverables must include a lockfile. Add it in **PR1** (semantic freeze), not PR0.

Choose one:

* `requirements-lock.txt` generated via `pip-compile` (or equivalent), pinned versions.
* Or `poetry.lock` if you’re using Poetry.

Given you want minimal infrastructure change, the simplest is:

* `requirements.txt` (top-level direct deps, minimal)
* `requirements-lock.txt` (fully pinned transitive resolution)

Pin at minimum:

* the JCS library (`canonicaljson` or chosen alternative),
* `PyYAML` (constitution parsing),
* anything used by CLI/testing that affects serialization.

The manifest’s `dependency_lock_hash` is `SHA256(bytes_of_lockfile)`.

If your repo currently has loose specs, that is exactly what X-0E is meant to end.

---

## Q79 — CI should run only X-0E tests vs add smoke acceptance test

**Binding answer:** Add one smoke test: **run `test_acceptance.py` (or equivalent minimal kernel acceptance)** if it completes in ~30 seconds.

So: X-0E CI = (a) + a small (b):

1. X-0E-specific tests
2. one shared-kernel smoke acceptance suite
3. cross-container run/replay determinism

This addresses the “shared code regression” concern without exploding CI scope.

---

## Q80 — Who reviews/merges PR-SPEC?

I can’t control your repo permissions, but I can set a process requirement.

**Binding requirement:** PR-SPEC requires **explicit human approval** before merge.

Reason: it changes the normative spec. Even if the implementation agent authors it, treat it as governance.

So:

* implementation agent drafts PR-SPEC
* a designated maintainer (you, or whomever holds authority in your process) approves/merges
* PR1 claims compliance only after PR-SPEC is merged

Parallel work is fine, but “frozen spec changed” must be explicitly signed off.

---
Final round. Locking these down so there’s no ambiguity left in the replay regime.

---

## Q81 — Dispatcher behavior when `kernel_version_id` absent

**Binding answer: (a)** implicit legacy mode.

Rule:

* If `kernel_version_id` present → dispatch to `replay_x0e.py`.
* If absent → dispatch to `replay_legacy.py`.

No warning required. No flag required.

Rationale:

* Pre-X-0E logs are unversioned by design.
* Requiring a flag adds friction without improving safety.
* Silent misrouting risk is low because legacy logs won’t contain the new chain/hash structures.

If in future you want stricter hygiene, you can add a `--strict` mode. Not in X-0E v0.1.

---

## Q82 — kernel_version_id typo risk & hash anchoring

This is subtle and important.

Your current rule:

```
kernel_version_hash = SHA256(UTF8(kernel_version_id))
state_hash[0] = SHA256(constitution_hash || kernel_version_hash)
```

If you later change the literal string (even correcting a typo), replay breaks.

**Binding answer: (a)** freeze the string permanently once logs exist.

Why not (b) or (c)?

* (b) indirection defeats the audit simplicity: replay must not depend on external lookup tables.
* (c) adding a precomputed hash in manifest splits authority between string and hash.

The clean rule is:

> The kernel_version_id string is part of the replay protocol identity. Once used in production logs, it is immutable.

If you typo it, that typo becomes canonical. That is acceptable; it is a protocol identifier, not user-facing text.

If you ever truly need to change it, that is a new replay regime → new version string → old logs remain tied to the old one.

This is exactly how protocol versions should behave.

---

## Q83 — fsync per entry vs throughput concerns

**Binding answer:** correctness-first; performance irrelevant for v0.1.

X-0E is:

* single-agent
* CLI-driven
* deterministic freeze artifact

There is no throughput SLA. If `fsync` costs 1–5ms per write, that is acceptable.

So:

* Yes, `fsync` after each write to:

  * `execution_trace`
  * `outbox`
  * and ideally the other core logs participating in replay.

If in a future phase you optimize batching, that is a new performance-focused milestone with its own invariants.

For X-0E: correctness > speed.

---

## Q84 — Lockfile pinning scope

**Binding answer: (b) full transitive closure + Python version constraint.**

Specifically:

* Pin **every resolved dependency** (transitive included).
* Record:

  * `python_version`
  * `platform tag` if necessary
* `dependency_lock_hash = SHA256(bytes_of_lockfile)`

Reason:

* Replay determinism is sensitive to:

  * JSON canonicalization behavior
  * YAML parsing behavior
  * Any serialization quirk in dependencies
* Partial pinning undermines the freeze guarantee.

So your lockfile must represent the **entire environment state** required to reproduce hashing behavior.

In practice:

* `requirements-lock.txt` generated in a clean venv.
* CI builds container using exact Python version (e.g., `python:3.11.x`).
* Manifest records:

  * `python_version`
  * `dependency_lock_hash`

That is sufficient for X-0E-grade reproducibility.

---

# Final Observations

You’ve now closed all structural ambiguities:

* Replay regime versioned and frozen.
* Canonicalization standardized.
* Hash concatenation defined at byte level.
* Log append semantics crash-safe.
* Legacy compatibility explicitly bounded.
* Lockfile and CI included in deliverable.

At this point, the only remaining risk surface is implementation drift — not specification ambiguity.
