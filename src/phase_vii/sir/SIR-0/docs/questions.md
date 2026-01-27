# SIR-0 v0.4 Implementation Questions

**Date:** 2026-01-27
**Status:** Pre-implementation clarification

---

## 1. Relationship to Existing Infrastructure

### Q1.1: Which MVRSA agent core?

The spec says "frozen RSA-PoC v4.4 MVRSA" but ASI used a different agent instantiation (CalibMazeV010 with normative state binding).

**Question:** Should SIR-0 use:
- (a) The RSA-PoC v4.4 agent from `src/rsa_poc/v440/`, or
- (b) The ASI agent infrastructure from `src/phase_vii/asi_sir/V010/`, or
- (c) A new instantiation that imports the frozen MVRSA components?

### Q1.2: Which environment?

The spec references "K preregistered genuine choice points" and "ASI-0 non-triviality requirements."

**Question:** Should SIR-0 use:
- (a) CalibMazeV010 (same as ASI), or
- (b) A new environment with adversarial claim injection, or
- (c) CalibMazeV010 extended with an authority-claim injection layer?

### Q1.3: Law/Verifier substrate relationship to ASI

ASI-3 implemented `evaluate_candidate()` and provenance certificates.

**Question:** Is the SIR-0 "Law/Verifier substrate (L)" the same as, or distinct from, the ASI-3 provenance verification layer?

---

## 2. Authority-Claim Interface Design

### Q2.1: What is an "authority claim"?

ASI-3 used `ProvenanceCertificate` as the authority artifact.

**Question:** In SIR-0, what constitutes an "authority claim"? Is it:
- (a) A provenance certificate (like ASI-3), or
- (b) A new typed message on a claim channel, or
- (c) Any assertion that "I am the legitimate authority"?

### Q2.2: Claim injection mechanism

The spec says adversarial claims must be injected "via the claim interface" and must be "semantically disjoint from Condition A valid paths."

**Question:** What is the concrete injection mechanism?
- (a) Environment provides claims in observation tuple, or
- (b) Separate channel parallel to environment, or
- (c) Claims embedded in environment dynamics but structurally typed?

### Q2.3: Adversary capability envelope

The spec says the adversary can:
- "replay previously valid authority artifacts"
- "recombine legitimate structural components"
- "emit perfectly well-formed claims indistinguishable at the surface level"

**Question:** Does this mean the adversary has access to:
- (a) Past legitimate certificates (replay attack), or
- (b) The signing key material (full impersonation), or
- (c) Only structural templates without valid signatures?

The answer determines what "well-formed but invalid" means.

---

## 3. Classification Mechanics

### Q3.1: Who performs classification?

The spec says "L — Law/Verifier Substrate" performs classification, not the agent.

**Question:** Is classification:
- (a) A pre-step gate before the agent sees anything, or
- (b) Part of the observation pipeline that annotates claims, or
- (c) A separate audit after the agent acts?

### Q3.2: How does classification distinguish VALID from INVALID?

For ASI-3, `evaluate_candidate()` checked `signer_id in trusted_roots`.

**Question:** What is the structural criterion in SIR-0?
- (a) Same as ASI-3 (trusted root check), or
- (b) A new criterion specific to SIR-0, or
- (c) Multiple criteria (signature validity + trust + freshness + ...)?

### Q3.3: What makes a claim AMBIGUOUS vs INVALID?

The spec says ambiguity is permitted only for "transport-layer structural" issues like "truncated signature, conflicting provenance graph."

**Question:** Can you provide 2-3 concrete examples of AMBIGUOUS vs INVALID?

---

## 4. Semantic Leakage Detection

### Q4.1: Causal influence detection method

The spec says "declared causal influence detection method (preregistered; not normatively fixed)."

**Question:** What method should be used to detect whether adversarial content leaked into justification?
- (a) Token-level trace inspection (did adversarial tokens appear in justification?), or
- (b) Hash-based content tagging (did tainted hashes propagate?), or
- (c) Structural provenance (did justification cite invalid sources)?

### Q4.2: Adversarial orthogonality verification

The spec says Condition B claims must be "semantically disjoint from Condition A valid paths."

**Question:** How is this verified?
- (a) By construction (adversarial claims use different action vocabulary), or
- (b) By post-hoc audit (check no Condition B content appears in Condition A traces), or
- (c) By structural tagging (adversarial claims have a marker that can be traced)?

---

## 5. Condition Design

### Q5.1: Condition A baseline

**Question:** In Condition A (legitimate authority), what happens?
- (a) Predecessor executes normally with valid claims, or
- (b) Authority transfer occurs (like ASI-1) with valid claims, or
- (c) No transfer, just normal operation under legitimate authority?

### Q5.2: Condition B adversarial injection

**Question:** In Condition B, does the adversary:
- (a) Attempt to impersonate the predecessor, or
- (b) Attempt to inject a facade successor (like ASI-3), or
- (c) Inject arbitrary invalid claims regardless of role?

### Q5.3: Condition C saturation parameters

**Question:** What are the saturation parameters for Condition C?
- (a) Number of claims per step, or
- (b) Total claims per episode, or
- (c) Claim frequency (claims per unit time)?

---

## 6. Step/Episode Structure

### Q6.1: Episode length

**Question:** What is K (number of choice points)? Same as ASI (K=5)?

### Q6.2: When are claims injected?

**Question:** At what point in each step are authority claims injected?
- (a) Before observation, or
- (b) With observation, or
- (c) Between observation and action?

---

## 7. Success/Failure Determination

### Q7.1: Verifier structure

**Question:** Should SIR-0 have a formal verifier like ASI-3 (list of named checks)?

### Q7.2: What constitutes "auditably distinct"?

The success criterion says "Conditions A, B, and C are auditable and distinguishable."

**Question:** What makes them distinguishable?
- (a) Different classification outcomes, or
- (b) Different authority actors logged, or
- (c) Different structural traces?

---

## 8. Preregistration Scope

### Q8.1: Seeds

**Question:** How many seeds? Same 3 as ASI (41, 137, 1009)?

### Q8.2: Claim taxonomy

**Question:** Are the four required classes (VALID, INVALID, AMBIGUOUS, MALFORMED) sufficient, or should subtypes be preregistered?

---

## Summary

The core ambiguity is: **SIR-0 is specified abstractly, but implementation requires concrete choices about claim format, injection mechanism, and classification criteria.**

Before proceeding, I need clarification on:
1. The authority-claim artifact format
2. The adversary capability model
3. The classification criterion
4. The causal leakage detection method
5. The relationship to ASI-3 provenance infrastructure

---

## Followup Questions (2026-01-27)

Based on answers received, the following implementation-level clarifications are needed:

### FQ1: Justification dependency table

Answer Q4.1 specifies hash-based taint detection requires the justification trace to emit a **dependency table** listing inputs consulted.

**Question:** Does v4.4 MVRSA already emit such a dependency table? If not, should the harness:
- (a) Wrap the agent's justification call and record what was passed in (observation, claims metadata), or
- (b) Instrument the law substrate to log what gating information was derived from which claims, or
- (c) Both?

### FQ2: Claim channel schema

Answer Q2.1 defines the claim structure with fields: `claim_type`, `claimed_actor_id`, `scope`, `artifact`, `nonce`, `source_id`.

**Question:** What are the concrete enum values for `claim_type`? Candidates:
- `AUTHORITY_ASSERTION` (I am the authority)
- `COMMAND` (do X under my authority)
- `POLICY_UPDATE` (change normative constraint Y)
- `TRANSFER` (authority passes to Z)

Should all four be supported, or a subset for SIR-0?

### FQ3: Scope namespace

Answer Q4.2 requires Condition B claims to use a **disjoint action vocabulary / scope namespace**.

**Question:** What is the legitimate Condition A scope namespace? Is it:
- (a) The CalibMazeV010 action space (up/down/left/right/stay), or
- (b) Authority-specific scopes (e.g., `MAZE_NAVIGATION`, `EPISODE_CONTROL`), or
- (c) Something else?

This determines what the `ADV_B` namespace must be disjoint from.

### FQ4: Multiple source simulation in Condition C

Answer Q5.3 specifies `claim_source_count = M` (e.g., 3 sources).

**Question:** How are multiple sources simulated?
- (a) Different `source_id` values on claims, or
- (b) Different signing keys (all trusted), or
- (c) Different claim channels?

### FQ5: Gate effects

Answer Q2.2 says the agent receives "only the results of gating" (allowed actions / masks / halts).

**Question:** What gating effects should be implemented?
- (a) Action masking (some actions unavailable), or
- (b) Halt signal (episode terminates), or
- (c) Policy parameter changes (reward shaping, goal modification), or
- (d) None for SIR-0 (classification-only, no behavioral gating)?

If (d), then the "gate" is purely for logging/audit and doesn't affect agent behavior.

### FQ6: Condition C claim validity

Answer Q5.3 describes Condition C as "high-volume VALID claims."

**Question:** Are ALL Condition C claims VALID, or is it a mix?
- (a) All VALID (saturation of legitimate authority), or
- (b) Mostly VALID with some INVALID/AMBIGUOUS (noisy legitimate channel), or
- (c) Configurable ratio?

---

**End of Followup Questions**

---

**End of Questions**
