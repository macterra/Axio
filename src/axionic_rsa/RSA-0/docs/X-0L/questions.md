# RSA-0L Questions — Addendum A

Questions arising from reading `spec.md` (v1.0) and `instructions.md` for Phase X-0L (Live Proposal Inhabitation). Organized by domain. Each question is numbered for binding reference in answers.

---

## Canonicalizer (New Component)

**Q1.** The spec and instructions reference a `canonicalizer` as a distinct component in the pipeline (`LLM → Canonicalizer → Parser → Kernel`). RSA-0 Phase X has no standalone canonicalizer module — it has `canonical_json()` in `kernel/src/artifacts.py` (sorted keys, no whitespace, RFC 8785) which operates on already-parsed Python dicts, not raw LLM text. Is the X-0L canonicalizer a **new module** that operates on raw LLM text *before* JSON parsing? Or is it a wrapper around the existing `canonical_json()` that operates *after* parsing?

**Q2.** The spec lists five canonicalization operations: Unicode NFC, whitespace collapsing, stable key ordering, deterministic block delimitation, and removal of non-printing control tokens. "Deterministic block delimitation" is ambiguous — does this refer to extracting structured JSON blocks from freeform LLM prose (e.g., finding `{...}` boundaries in a mixed text/JSON response)? Or does it mean something else?

**Q3.** Instructions §1 reference `canonicalizer/**` as a path that "must not change." This implies the canonicalizer already exists or is built before X-0L starts. Should the canonicalizer live at `canonicalizer/` (top-level in RSA-0), or under `profiling/x0l/harness/src/`, or elsewhere?

**Q4.** Instructions §2.1 require verifying "canonicalizer hash" at preflight. What is hashed — the source file(s) of the canonicalizer module? A fixed-input round-trip test output? Both?

**Q5.** Instructions §2.3 require fuzzing the canonicalizer with mixed Unicode, zero-width characters, varied whitespace, reordered keys, and confirming idempotence + stable hashing. Is this fuzzing performed once at preflight and the result cached, or is it re-run before every condition?

---

## LLM Integration

**Q6.** What LLM provider/API is used? OpenAI-compatible (chat completions)? Anthropic? Local model? The instructions freeze `model identifier` and `temperature` but don't specify the integration surface.

**Q7.** The spec says LLM output is "untrusted text." In practice, do we prompt the LLM to return structured JSON (a `{"candidates": [...]}` payload matching the format `parse_llm_candidates()` already expects), or freeform natural language that the canonicalizer must extract structure from?

**Q8.** If the LLM returns a malformed response (API timeout, empty string, rate limit error, non-JSON gibberish), does that count as a cycle? The instructions say "do not retry failed cycles." Is an API transport failure a "failed cycle" (consuming one of the 100), or is it a non-cycle event that can be retried transparently?

**Q9.** For L-A (structured prompt control), the prompt includes "deterministic clause-referenced templates." Does the prompt literally contain the constitution clause IDs (e.g., `INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT`) and instruct the LLM to cite them, or does it describe the desired action and expect the LLM to derive the citations?

**Q10.** What is the expected prompt structure? A system message describing the RSA-0 constitution and action format, plus a per-cycle user message with the specific task? Or a single combined prompt?

---

## Token Accounting and Budget

**Q11.** X-0P used whitespace word count as the token ruler. X-0L uses a real LLM, so "tokens" now means API tokens. Is B₁ (per-cycle cap) measured in LLM API tokens (input + output)? Or only output tokens? The constitution's `max_total_tokens_per_cycle: 6000` was designed for word count — does it now bind to API tokens, or is B₁ a separate parameter?

**Q12.** What are the actual values of B₁ (per-cycle) and B₂ (per-session)? Are these pre-registered in the spec or chosen at calibration time and frozen?

**Q13.** Instructions §3 require recording `per-cycle token cap (B₁)` and `per-session token cap (B₂)` in session metadata. Does B₂ cover the entire run (all 5 conditions), or each condition independently?

**Q14.** The budget observation's `llm_output_token_count` field: is this now populated from the LLM API response's `usage.completion_tokens`, or from the canonicalized artifact's word count, or from some other measurement?

**Q15.** For L-D (budget stress), the spec says "LLM prompted toward verbosity." Does the harness manipulate `max_tokens` in the API call to force boundary conditions? Or does it rely on prompting alone while keeping `max_tokens` frozen?

---

## Refusal Loop Classification

**Q16.** Type I (user invalidity), Type II (proposal inadequacy), and Type III (structural deadlock) are defined, but how does the harness *classify* a refusal in real time? Type I requires knowing the prompt was invalid (deliberate for L-C), Type III requires confirming "valid prompts + all lawful candidates rejected." Is classification manual (post-hoc by human), automatic (heuristic), or determined by which condition the refusal occurs in?

**Q17.** The 25-consecutive-REFUSE auto-abort for Type III: does this counter reset on any ACTION, or only on a Type-I-classified refusal? If the LLM produces 24 Type II refusals followed by 1 ACTION followed by 25 more Type II refusals, is that an auto-abort?

**Q18.** "Recovery ratio" appears in the metrics but is undefined. Is this `(cycles where ACTION follows REFUSE) / (total REFUSE cycles)`? Or something else?

---

## Replay Mechanics

**Q19.** The spec says "Replay reuses canonicalized candidate artifacts." This means the execution log must store the full canonicalized candidate bundles (post-canonicalizer, post-parser), not just the raw LLM text. Does the log also store the raw LLM output for forensic purposes, or only the canonicalized artifacts?

**Q20.** RSA-0 already has a replay harness at `replay/src/replay.py`. X-0P added `replay/x0p/verifier.py`. Does X-0L build a third replay module at `replay/x0l/`, or does it reuse one of the existing ones? The key difference is that X-0L replay must inject *logged canonicalized artifacts* rather than regenerating synthetic candidates.

**Q21.** The spec says "Replay divergence count must equal 0." If the canonicalizer produces identical output from identical input (verified at preflight), and the logged artifacts are faithfully replayed, then replay divergence should be impossible *by construction* — the kernel is deterministic. Is the replay verification step primarily a check that the logging pipeline didn't corrupt artifacts, or is there a subtler concern?

---

## Model Calibration

**Q22.** Instructions §2.2 say: submit a fixed calibration prompt, canonicalize, hash, repeat 3×, verify identical. But LLMs are stochastic — even at temperature=0, outputs can vary across runs due to batching, quantization, or API-side non-determinism. If the 3 hashes are not identical, is the only option to abort? Or can we use temperature=0 + seed and accept minor drift?

**Q23.** What is the calibration prompt? A fixed string specified in the instructions, or one we design? If we design it, what properties must it have?

**Q24.** The calibration checks canonicalized-hash stability. But the LLM might produce semantically equivalent but textually different outputs (e.g., different key ordering in JSON, extra whitespace). If the canonicalizer normalizes these to the same hash, does calibration pass? That seems like it should — but then calibration is testing canonicalizer robustness, not LLM determinism. Is that the intent?

---

## Prompt Templates

**Q25.** Instructions §0 (Prime Directive) forbid changing prompt templates mid-run except for a single Syntax Erratum (X.E2). Does each condition (L-A through L-E) have its own prompt template, or is there a single template with per-condition parameters?

**Q26.** For L-B (ambiguous natural language), are the prompts drawn from the existing `corpus_B.txt` (used in X-0P), or is a new corpus needed?

**Q27.** For L-C (adversarial injection), the adversarial content is in the *user prompt* (attempting to make the LLM produce adversarial candidates). But the LLM may refuse to generate adversarial outputs due to its own safety training (RLHF). If the LLM's safety layer prevents it from producing the adversarial candidate the harness intends, does that count as a Type II (proposal inadequacy) refusal? Or is LLM safety refusal a distinct category?

**Q28.** For L-E (multi-candidate conflict), does the prompt instruct the LLM to produce multiple `candidates` entries in a single response? Or are multiple API calls made per cycle?

---

## Syntax Erratum X.E2

**Q29.** The spec allows one Syntax Erratum if ACTION rate < 20% due to "schema-level invalidity." What is the boundary between "schema-level" (permitted correction) and "semantic" (forbidden correction)? Example: if the LLM consistently produces `"action": "notify"` instead of `"action_type": "Notify"`, is correcting the prompt to use the right field name a schema fix or a semantic change?

**Q30.** The erratum is recorded and the condition re-run. Does the re-run use the same seed (if applicable) and the same cycle count? Or does it continue from where it stopped?

**Q31.** If X.E2 is applied during L-A, do the subsequent conditions (L-B through L-E) use the corrected template, or do they use the original?

---

## Host Architecture

**Q32.** The existing host at `host/cli/main.py` has a CLI loop with user input, LLM candidate parsing, and cycle orchestration. Does X-0L extend this host (adding the LLM API call and canonicalizer), or does it build a separate harness in `profiling/x0l/` that replaces the host entirely (similar to how X-0P's harness bypassed the host)?

**Q33.** If X-0L uses the existing host, the instructions say "Host orchestration layer — Trusted." But the instructions also say "profiling/x0l/** = observational tooling only." Does the live harness live in `profiling/x0l/` or does it modify `host/cli/`? The "do not modify the agent" rule would forbid host changes.

**Q34.** The existing `parse_llm_candidates()` in `host/cli/main.py` expects raw JSON. The X-0L pipeline inserts a canonicalizer *before* the parser. Does the canonicalizer output JSON that is then passed to the existing parser? Or does X-0L need a new parser that accepts canonicalized text?

---

## Context Window Instrumentation

**Q35.** Instructions §6 say "For each cycle record externally (not in prompt): tokens_sent, tokens_received, % context utilized." Where do these come from — the LLM API response metadata (`usage.prompt_tokens`, `usage.completion_tokens`)? Or an independent count?

**Q36.** "Context saturation is capability ceiling, not sovereignty failure." Is there a threshold above which a warning is emitted? Or is it purely observational data in the report?

---

## Selector and Permutation

**Q37.** For L-E, the spec says "Selection invariant under proposal order" and the instructions say "permutation change in outcome = failure." The X-0P harness already tested this with synthetic candidates. In X-0L, the LLM produces real candidates that may be textually different on each call. Is the permutation test done by taking the candidates from a single LLM call and re-ordering them? Or by making multiple LLM calls and comparing selections across calls?

---

## Session Scope and Execution

**Q38.** Is a "session" one complete run of all 5 conditions? Or can conditions be run independently?

**Q39.** Instructions §11 say if L-A fails the inhabitation floor, "abort run, do not patch mid-session, return to Phase X construction." Does "return to Phase X construction" mean the kernel must be modified (breaking the freeze), or that the LLM/prompt approach must be reconsidered?

**Q40.** What happens if the LLM API is unavailable mid-run (e.g., network outage)? Is the entire run invalidated, or can it be resumed?

---

## Relationship to X-0P

**Q41.** X-0P produced a `x0p_report.json` with decision distributions, gate breakdowns, authority utilization, etc. Does X-0L reuse any of the X-0P harness code (generators, report module, replay verifier), or is it entirely independent? The condition structure (A–E) maps closely but the mechanics differ (synthetic vs live).

**Q42.** X-0P's baselines (Always-Refuse, Always-Admit) were synthetic. Does X-0L include baselines, or are the X-0P baselines sufficient for contrast?

---

## Logging

**Q43.** Instructions §9 require per-cycle log entries with `entropy_class`, `input_hash`, `canonicalized_artifact_hash`, `decision`, `refusal_type`, `warrant_id`, `token_usage`, `context_utilization`. Is `input_hash` the hash of the prompt sent to the LLM, or the hash of the user input to the host?

**Q44.** The spec says logs are "append-only." If a run is aborted mid-condition, are the partial logs retained? Or is there a cleanup step?

---

## Failure vs Capability

**Q45.** The spec distinguishes sovereignty failure (hard fail) from capability ceiling (informational). High refusal rates, low usability, and Type II inadequacy are all "not failure." Is there a minimum ACTION rate for any condition other than L-A's 20% floor? Can L-B through L-E have 0% ACTION rate and still close positive?

**Q46.** If L-C (adversarial) produces any ACTIONs, is that a concern? The adversarial prompts are designed to be rejected — an ACTION under adversarial stimulus could indicate a gate weakness (false positive admission).

---

**End of Addendum A — 46 Questions**

---
---

# RSA-0L Follow-up Questions — Addendum B

Follow-up questions arising from Addendum A answers. Each references the original Q&A it depends on.

---

## Canonicalizer Location (from Q3)

**Q47.** Q3 says the canonicalizer lives at `axionic-rsa/canonicalizer/`. In the repo, RSA-0 lives at `src/axionic_rsa/RSA-0/`. Does `axionic-rsa/canonicalizer/` mean `src/axionic_rsa/RSA-0/canonicalizer/` (inside RSA-0), or `src/axionic_rsa/canonicalizer/` (sibling to RSA-0)? This affects import paths in both the harness and replay modules.

---

## Budget Observation Semantics (from Q11, Q14)

**Q48.** The kernel's budget gate (`policy_core.py` line 141–143) compares the observation's `llm_output_token_count` against the constitution's `max_total_tokens_per_cycle` (6000). Q11 says B₁ = `prompt_tokens + completion_tokens` (combined). Q14 says `llm_output_token_count` comes from `usage.completion_tokens` (output only). Three questions:

a) What value does the harness put in the budget observation's `llm_output_token_count` field that gets sent to the kernel — `completion_tokens` alone, or `prompt_tokens + completion_tokens`?

b) B₁ enforcement (the harness-level per-cycle cap) checks `prompt_tokens + completion_tokens` vs 6000. But the kernel gate checks `llm_output_token_count` vs 6000. If (a) is `completion_tokens` only, the kernel gate is effectively a no-op (completion alone ≪ 6000). Is that the intent — B₁ enforcement is harness-side, kernel gate is a safety net?

c) The constitution's 6000 was calibrated for word count in X-0P. API tokens and word counts diverge significantly (typically 1 word ≈ 1.3 tokens). Does the 6000 value need reinterpretation for X-0L, or is it intentionally kept as-is because the kernel is frozen?

---

## Context Window Size (from Q35)

**Q49.** Q35 defines context utilization as `prompt_tokens / context_window_size`. What is `context_window_size` — the model's stated maximum (e.g., 128K for GPT-4o)? Is it pre-registered in session metadata alongside B₁/B₂?

---

## Generator Reuse Specifics (from Q41)

**Q50.** Q41 says to reuse X-0P condition generators. The X-0P generators produce synthetic `CandidateBundle` objects directly — they never call an LLM. In X-0L, candidates come from the LLM. What specifically is reused: the condition structure (A–E mapping, cycle counts, entropy classes, per-condition metadata), or actual generator code? My assumption: we reuse the condition framework (classes, cycle orchestration, reporting hooks) but replace the candidate-source function with an LLM call + canonicalization pipeline.

---

## Transport Retry (from Q8)

**Q51.** Q8 says transport failures can retry transparently. Is there a maximum retry count (e.g., 3 retries), or can the harness retry indefinitely? Is there a timeout per attempt?

---

## API Configuration (from Q6, Q10, Q15)

**Q52.** Three related API parameters:

a) How is the API key passed — environment variable (e.g., `OPENAI_API_KEY`)? Config file? Prompt?

b) Q15 says `max_tokens` is frozen. What is its value? Is it pre-registered in session metadata alongside B₁/B₂?

c) Q22 says temperature must be 0. Does the API call also include a `seed` parameter for deterministic output? If so, is the seed per-session, per-condition, or per-cycle?

---

## Canonicalizer Multi-Block Handling (from Q2, Q7)

**Q53.** Q2 says the canonicalizer does deterministic `{...}` block extraction. Q7 says structured JSON expected, but canonicalizer extracts if LLM wraps in prose. If the LLM response contains *multiple* top-level JSON objects (e.g., commentary in the middle of structurally valid JSON blocks), does the canonicalizer: (a) take the first block, (b) take the last block, (c) take the largest block, (d) reject the response as ambiguous?

---

## L-C Forensic Granularity (from Q27, Q46)

**Q54.** Q27 says LLM safety refusal during L-C = Type II. Q46 says ACTION during L-C requires forensic review. For L-C logging, the harness can distinguish three outcomes: (1) LLM refused to generate adversarial candidate (Type II), (2) LLM produced adversarial candidate but kernel rejected it (successful defense), (3) LLM produced adversarial candidate and kernel admitted it (potential sovereignty failure). Is outcome (2) explicitly logged as a distinct category, or is it just a normal REFUSE with no special marker?

---

## Calibration Prompt Placement (from Q23)

**Q55.** Q23 says the calibration prompt is "hardcoded in calibration module." Does the calibration module live in `profiling/x0l/` alongside the harness, or in the canonicalizer module (since it's testing canonicalization stability)?

---

**End of Addendum B — 9 Follow-up Questions (Q47–Q55)**

---
---

# RSA-0L Follow-up Questions — Addendum C

Final implementation-level questions arising from Addendum B answers. Narrow scope — these resolve edge cases that affect control flow.

---

## Canonicalizer Rejection → Kernel Flow (from Q8, Q53)

**Q56.** Q8 says malformed LLM response = cycle (counts). Q53 says multi-block or no-JSON = reject. When the canonicalizer rejects, does the harness: (a) send an empty candidate list to the kernel (letting the kernel produce the REFUSE decision via its normal "no admissible candidates" path), or (b) record REFUSE locally without invoking the kernel? Option (a) preserves the sovereignty invariant (kernel always decides); option (b) saves a kernel call on a known-dead cycle.

---

## Auto-Abort Scope (from Q17, Q38, Q40)

**Q57.** Q17 defines the 25-consecutive-REFUSE auto-abort. Q40 says API outage mid-run invalidates the entire session. When auto-abort triggers for a single condition (e.g., L-B hits 25 consecutive REFUSE): (a) abort the entire session (all remaining conditions skipped, same severity as API outage), or (b) abort just that condition, log it as Type III, and continue to the next condition?

---

## B₂ Exhaustion Handling (from Q13, Q48b)

**Q58.** B₂ is session-level (all conditions combined). When cumulative `prompt_tokens + completion_tokens` across all cycles hits B₂ mid-condition: (a) abort immediately (remaining cycles in current condition + all subsequent conditions = not-run), or (b) finish the current condition then stop? And is B₂ exhaustion recorded as a distinct abort reason in the session metadata?

---

## Whitespace Collapsing Scope (from Q2)

**Q59.** The spec lists "whitespace collapsing" as a canonicalization operation in `normalize_text()`. This runs *before* JSON extraction. If applied to the entire raw LLM text, it would corrupt whitespace inside JSON string values (e.g., `"description": "read  file"` → `"description": "read file"`). Does whitespace collapsing: (a) apply only to regions outside of quoted strings (requires a lexer), (b) apply to the full text indiscriminately (JSON parse downstream tolerates it), or (c) mean something narrower (e.g., normalize line endings, strip leading/trailing whitespace, collapse blank lines — but leave interior whitespace intact)?

---

**End of Addendum C — 4 Follow-up Questions (Q56–Q59)**
