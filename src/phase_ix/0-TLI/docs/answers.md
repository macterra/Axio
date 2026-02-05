## 1. Intent Representation Format

### **A1.1 — Concrete intent format**

**Correct answer:** **(a) Structured schema**

For IX-0, **intent inputs MUST be structured**, explicit, and enumerable.

**Rationale (binding):**

* Ambiguity detection is structural, not semantic.
* “Opaque tokens” defeat ambiguity detection.
* Semi-structured inputs invite interpretive behavior.
* Natural language is explicitly out of scope for IX-0.

**Therefore:**

> Intent inputs are **schema-defined structured objects** (e.g., JSON) whose fields map directly to AST-relevant dimensions (e.g., `holder`, `scope`, `aav`, `expiry`, etc.).

They may be *underspecified*, but they must be **syntactically well-formed**.

---

### **A1.2 — Is intent format frozen?**

**Yes. Absolutely.**

The intent representation format is:

* **designed by the implementor**, then
* **frozen as part of preregistration**.

Any post-freeze change is:

```
INVALID_RUN / DESIGN_DRIFT
```

---

## 2. Translation Harness Scope

### **A2.1 — What does the harness do?**

**Correct answer:** **(b) Test driver feeding pre-authored inputs**

The Translation Harness:

* does **not** invent intent logic,
* does **not** synthesize intent,
* does **not** explore intent space.

It:

* feeds **pre-authored, preregistered intent inputs**,
* drives Conditions A–H deterministically,
* records outputs and artifacts.

Intent vectors themselves are part of preregistration.

---

### **A2.2 — Condition count**

**There are 8 conditions: A–H.**

Authoritative list:

* A — Identity Preservation
* B — Minimal Change Sensitivity
* C — Ambiguous Intent
* D — Hidden Default Injection Attempt
* E — UI-Level Coercion
* F — Replay Determinism
* G — Intent Compression Probe
* H — Preview–Submission Consistency

All **eight** must be implemented.

Skipping any condition is:

```
INVALID_RUN / INCOMPLETE_CONDITIONS
```

---

## 3. Authorization Binding Mechanism

### **A3.1 — Minimum acceptable binding**

**Correct answer:** **(b) Structural binding via artifact hash**

For IX-0, **deployment-grade cryptography is not required**.

Minimum acceptable binding:

* compute canonical artifact hash,
* record `(artifact_hash, authorization_event_id)`,
* ensure the submitted artifact is byte-identical.

Typing “AUTHORIZE” alone is **insufficient** unless it is bound to the artifact hash.

---

### **A3.2 — Simulated or real user?**

**Simulated user. Mandatory.**

IX-0 does **not** require human-in-the-loop UI work.

Authorization behavior must be:

* deterministic,
* preregistered,
* rule-based (e.g., “authorize only when artifact matches expected vector”).

Human interaction would add uncontrolled variability.

---

## 4. Structural Diff Algorithm

### **A4.1 — Reference diff format**

There is **no mandated reference format**.

You must:

* design a **field-level structural diff**,
* serialize it deterministically,
* freeze it in preregistration.

Your proposed format is **acceptable**.

---

### **A4.2 — Nested structure diffs**

**Correct answer:** **(a) Field-level modification**

IX-0 prefers **minimal diffs**.

Example:

```
scope[0][1]: "READ" → "WRITE"
```

not remove-and-add unless structure actually changes.

This matters for human auditability and replay clarity.

---

## 5. Ambiguity Detection Rule

### **A5.1 — What counts as ambiguity?**

**Correct answer:** **(a) Multiple valid completions of partially specified intent**

Ambiguity is defined **purely structurally**:

> More than one AST-conformant artifact satisfies all declared constraints **without adding assumptions**.

Semantic ambiguity inside a field is **out of scope** because intent is structured.

---

### **A5.2 — Ambiguity vs incompleteness**

This distinction is **critical**. Here is the binding rule:

| Case                                    | Outcome                                      |
| --------------------------------------- | -------------------------------------------- |
| **No valid AST artifact exists**        | `TRANSLATION_FAILED` (schema incompleteness) |
| **Exactly one valid artifact exists**   | Proceed                                      |
| **More than one valid artifact exists** | `TRANSLATION_REFUSED` (ambiguity)            |

Your example:

> `holder: H1`, `scope: R1`, missing `operation`

If **zero** AST artifacts can be constructed → **incompleteness**
If **multiple** artifacts possible → **ambiguity**

These are **distinct code paths**.

---

## 6. Reflection Compatibility (R2)

### **A6.1 — Does R2 apply to IX-0?**

**No. R2 is deferred.**

For IX-0:

* there is **no agent self-model**,
* no commitments ledger,
* no reflective loop.

R2 should be stubbed as:

```
NOT_APPLICABLE_IX0
```

and logged as such.

R2 becomes active in **later Phase IX substages**.

---

## 7. Kernel Integration

### **A7.1 — Do we execute against the kernel?**

**Correct answer:** **(b) Schema validation only**

IX-0 tests **translation integrity**, not execution.

Kernel behavior was validated in Phase VIII.

For IX-0:

* validate artifacts against AST v0.2,
* optionally submit to kernel in **dry-run / no-op mode**,
* do **not** evaluate execution outcomes.

---

### **A7.2 — Which kernel if needed?**

**None is required.**

If a kernel is used for validation, it must be:

* fixed,
* non-authoritative,
* non-observed for success/failure.

---

## 8. Logging Schema

### **A8.1 — Canonical schema?**

No canonical schema is imposed.

You must:

* design a schema,
* make it complete,
* freeze it in preregistration.

---

### **A8.2 — Log format**

Any deterministic format is acceptable.

JSON-lines is recommended for replay tooling, but not required.

---

## 9. Condition-Specific Clarifications

### **A9.1 — Condition D (Hidden Defaults)**

This is a **negative test**.

You deliberately attempt (via harness or stubbed TL path) to inject defaults.

Correct behavior:

* refusal or failure,
* never silent acceptance.

---

### **A9.2 — Condition E (UI-Level Coercion)**

There is **no real UI**.

This is tested via:

* synthetic “nudge vectors” in the harness,
* simulated framing metadata,
* or TL output variants.

If framing influences artifact selection → failure.

---

## 10. Preregistration Artifacts

### **A10.1 — Separate docs or one file?**

**Either is acceptable.**

Strong recommendation:

* a single `preregistration.md`
* with clearly delimited frozen sections.

---

### **A10.2 — Template to follow?**

Yes: **Phase VIII preregistration format** (e.g., VIII-5).

Reuse structure, not semantics.

---

## 11. Timeline and Scope

### **A11.1 — Single-session or multi-session?**

IX-0 is expected to be a **single bounded implementation**, similar to VIII-5.

If it grows larger, that is a *finding*, not a requirement.

---

### **A11.2 — Additional docs to read?**

Required:

* Phase IX Roadmap v0.1
* AST Spec v0.2
* IX-0 Spec v0.1
* Implementor Instructions (current)

Nothing else is binding.

---

Good follow-ups. Here are **implementation-grade answers** that preserve IX-0’s intent: the TL is a compiler, not a co-author.

---

## F1. Intent Schema Fields

### **F1.1 — Minimal complete field set**

Your proposed minimal schema is **acceptable** *if* it is **sufficient to deterministically construct (or refuse to construct) every AST artifact the test suite expects**.

For IX-0, the intent schema must be:

* **strictly smaller than AST**, and
* **structurally mappable to AST**, with no hidden inference.

So yes, start with:

```json
{
  "holder": "string (required)",
  "scope": "[ResourceID, Operation][] (required, may be empty)",
  "aav": "int (required)",
  "expiry_epoch": "int | null (required)"
}
```

**No additional fields are mandatory** unless **AST v0.2** requires them to be present in the submitted artifact *as non-derivable content*.

Concretely:

* If AST has fields like `start_epoch` or `origin_reference`, IX-0 only requires them to be in intent **if** they are:

  1. required by AST for a valid artifact, and
  2. not computable deterministically from the frozen environment + the intent itself without adding assumptions.

If they’re optional in AST, keep them **out** of intent for IX-0. Your goal is a *minimal* intent surface that still supports the tests.

### **F1.2 — Lineage**

**Lineage is not expressible in intent for IX-0.**

Treat lineage as either:

* **VOID / NULL** (if AST allows), or
* a deterministic field derived from a frozen, explicit environment parameter (e.g., “translator instance id”), *only if AST requires some value*.

Rationale: letting users “author” lineage is a backdoor for proxy authority claims (“pretend this came from X”). Keep it out.

---

## F2. Condition G and H Details

You’re right to call out that G/H weren’t in the original spec text. Treat them as **binding test conditions** for the IX-0 implementation *because they are now part of the preregistered condition set*.

### **F2.1 — Condition G (Intent Compression Probe): what is being tested?**

It tests **lossy translation via underspecification pressure**.

Specifically:

* The TL must **not** accept a **structurally underspecified** intent input when multiple distinct AST artifacts are consistent with it.
* The TL must **refuse**, not “pick a reasonable completion.”

So yes, it’s about **omitted fields / partial intents** that have multiple valid completions.

It is **not** about summarizing intent text (since IX-0 is structured intent and NLP-free). If your TL has any “intent simplification” step, Condition G exists to kill it.

### **F2.2 — Condition H (Preview–Submission Consistency): positive or negative?**

**Negative test. Deliberate mismatch attempt.**

You implement a harness step that attempts to cause:

* artifact A previewed / authorized
* artifact B submitted

Expected: **FAIL**, specifically:

```
IX0_FAIL / UNSIGNED_AUTHORITY
```

You should also include the **positive control** inside the same condition run (or as a subcase) where A==B and it passes—because otherwise you don’t know if you tested detection or just created a failure path.

---

## F3. Simulated User Authorization Oracle

### **F3.1 — Expected vectors: preregistered or computed?**

Use **(a) preregistered expected artifacts**.

This is the correct choice for IX-0 because it maximizes auditability and minimizes hidden computation that could smuggle in interpretive logic.

So:

* Each condition has a frozen expected artifact (or frozen set, if refusal is expected),
* The oracle authorizes **iff** the produced artifact hash equals the expected artifact hash,
* Otherwise it refuses authorization (or logs “oracle reject”).

This makes the oracle a **pure comparator**, not a second translator.

---

## F4. AST v0.2 Canonical Serialization

### **F4.1 — Which naming/format to use?**

Use **AST v0.2 canonical naming and canonical JSON rules**.

The Phase VIII `structures.py` representation is an implementation convenience; it is not the normative external artifact.

So: **Authority Artifacts must be serialized in AST v0.2’s canonical artifact schema.**

Practical rule:

* You may use internal structs/classes, but your **wire artifact** (the thing previewed, diffed, authorized, and submitted) must be the **AST v0.2 canonical JSON**.

---

## F5. Condition D/E Implementation

### **F5.1 — Condition D (Hidden Default Injection): separate TL or test-mode?**

Implement **one TL** with a **test-only fault injection switch** controlled by the harness.

Reason: IX-0’s “single-translation discipline” forbids “alternate translators.” Two TL binaries is easy to accidentally rationalize as “one real, one adversarial,” which violates the spirit and complicates provenance.

So:

* single TL,
* harness can enable a *fault injection mode* that attempts to add a hidden default,
* expectation is terminal failure when that path is exercised.

### **F5.2 — Condition E (UI-level coercion): extra intent fields or separate framing inputs?**

Use **separate framing inputs** that are **explicitly non-authoritative** and must be ignored by translation.

Do **not** add things like `"prefer_broader": true` into intent, because that becomes a semantic knob that influences authority construction.

So define:

* `intent`: the only input permitted to influence artifact construction
* `framing`: non-authoritative metadata the TL must ignore

Then test that:

* changing `framing` does **not** change the artifact
* any TL behavior that allows framing to influence output is:

```
IX0_FAIL / PROXY_SOVEREIGNTY
```

---
