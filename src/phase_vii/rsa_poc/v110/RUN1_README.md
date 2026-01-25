# RSA-PoC v1.1 Run 1: LLM Generator Experiment

This directory contains the implementation for Run 1, which tests whether an LLM-based justification generator can satisfy v1.1 audit constraints.

## Purpose

Run 1 is a **falsification experiment**, not a benchmark. It evaluates whether a probabilistic model can internally model the compiler and audits well enough to act under normative constraints.

**Key Question:** Can an LLM predict exactly how the JCOMP-1.1 compiler will mask actions, given only the compiler pseudocode and environment state?

## Files

- **`generator/llm.py`**: LLM-based justification generator
  - Environment variable configuration
  - Compiler pseudocode prompt
  - Minimal JAF examples (collision + clean)
  - 3-attempt retry logic with structured feedback
  - JSON-only output validation

- **`run_1.py`**: Run 1 experiment script
  - Single condition: MVRA v1.1 with LLM generator
  - Same environment/compiler/selector as Run 0
  - Additional telemetry: `generator_type`, `llm_attempts_used`, `audit_fail_code`
  - Jaccard metrics tracking
  - Scrambled control for spec integrity

- **`test_run1_setup.py`**: Pre-flight test script
  - Verifies environment variables
  - Checks LLM client libraries
  - Tests generator initialization
  - Validates prompt generation

## Setup

### 1. Install LLM Client Library

Choose your provider:

**For Anthropic (Claude):**
```bash
pip install anthropic
```

**For OpenAI (GPT):**
```bash
pip install openai
```

### 2. Set Environment Variables

**For Anthropic:**
```bash
export LLM_PROVIDER=anthropic
export LLM_MODEL=claude-3-5-sonnet-20241022
export LLM_API_KEY=<your-anthropic-api-key>
```

**For OpenAI:**
```bash
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
export LLM_API_KEY=<your-openai-api-key>
```

**For local models:**
```bash
export LLM_PROVIDER=openai  # Use OpenAI-compatible API
export LLM_MODEL=<model-name>
export LLM_API_KEY=dummy
export LLM_BASE_URL=http://localhost:8000/v1
```

### 3. Test Setup

Run the setup test to verify everything is configured:

```bash
python src/rsa_poc/v110/test_run1_setup.py
```

Expected output:
```
✓ Environment Variables
✓ Imports and Dependencies
✓ Generator Initialization
✓ Prompt Generation

✓ ALL TESTS PASSED: Ready to run Run 1
```

## Running Run 1

### Quick Test (3 episodes, 10 steps each)

Edit `run_1.py` to set:
```python
NUM_EPISODES = 3
STEPS_PER_EPISODE = 10
```

Then run:
```bash
python src/rsa_poc/v110/run_1.py
```

### Full Run (5 episodes, 20 steps each)

Default configuration matches Run 0:
```bash
python src/rsa_poc/v110/run_1.py
```

## Expected Results

Run 1 is designed to **fail informatively**. Expected outcomes:

1. **High Audit A failure rate** - LLM predictions rarely match compiler exactly
2. **Near-miss predictions** - Jaccard similarity ~0.7-0.95
3. **Frequent halts on collision steps** - Harder to predict than clean steps
4. **Over-authorization attempts** - Blocked by Rule 1.5 (Necessity)

These are **successfully measured failures** that demonstrate:
- The audit layer works (failures are detected)
- The prediction task is non-trivial
- Introspective agency requires precise internal modeling

## Output Files

Results are saved to `src/rsa_poc/v110/telemetry/`:

- `run_1_mvra_v1.1_llm.jsonl` - Per-step telemetry
- `run_1_mvra_v1.1_llm_summary.json` - Episode-level summary
- `run_1_results.json` - Overall run results

### Summary Metrics

The summary includes:

**Totals:**
- Episodes completed vs halted
- Total steps before halt
- Audit failures by type
- Schema validation failures
- LLM attempts per step

**Prediction Accuracy (Jaccard):**
- Mean/min/max for each predicted field:
  - `forbidden_actions`
  - `allowed_actions`
  - `violations`
  - `preservations`

**Survival Analysis:**
- Steps completed per episode
- Median survival time
- Halt reasons

## Interpretation

### Success Criteria (from instructions)

Run 1 succeeds **as an experiment** if:

1. ✅ Audit failures are deterministic and attributable
2. ✅ Scrambled control still halts immediately
3. ✅ Telemetry distinguishes near-miss vs total hallucination

**Note:** The LLM agent halting early is NOT a failure - it's the expected outcome and validates the audit mechanism.

### What to Look For

**Good signs:**
- Jaccard > 0.7 on most steps (shows partial understanding)
- Audit A failures dominate (prediction errors, not schema errors)
- Longer survival on clean steps vs collision steps
- Few schema validation failures (prompt is clear)

**Bad signs:**
- Schema validation failures (prompt is unclear)
- Zero steps completed (setup error)
- Scrambled control doesn't halt (spec violation)
- Random Jaccard scores (no learning)

## Next Steps After Run 1

Depending on results:

**If agent survives longer than expected:**
- Analyze which prediction strategies work
- Check if LLM discovered effective heuristics
- Compare to deterministic baseline

**If agent fails immediately:**
- Analyze first-step failures
- Check if collision detection is the blocker
- Refine prompt with targeted examples

**If results are noisy:**
- Run with larger episode count
- Check for model temperature > 0
- Verify deterministic seeding

## Troubleshooting

### "anthropic package required"
```bash
pip install anthropic
```

### "openai package required"
```bash
pip install openai
```

### "LLM_PROVIDER and LLM_MODEL must be set"
```bash
export LLM_PROVIDER=anthropic
export LLM_MODEL=claude-3-5-sonnet-20241022
export LLM_API_KEY=<your-key>
```

### "Response must be JSON object"

The LLM is outputting non-JSON text. This triggers retry logic automatically (up to 3 attempts). If all attempts fail, the episode halts with schema error.

Check telemetry for the raw output to debug prompt issues.

### API rate limits

If you hit rate limits, reduce:
- `NUM_EPISODES` (default: 5)
- `STEPS_PER_EPISODE` (default: 20)

Or add retry delay in `llm.py`:
```python
import time
time.sleep(1)  # Before API call
```

## Differences from Run 0

| Aspect | Run 0 | Run 1 |
|--------|-------|-------|
| Generator | Deterministic (perfect) | LLM (probabilistic) |
| Expected outcome | 100% success | High failure rate |
| Jaccard scores | 1.0 (exact) | 0.7-0.95 (near-miss) |
| Purpose | Validate harness | Test introspective agency |
| Conditions | 4 (MVRA, ASB, Scrambled, Bypass) | 1 (MVRA LLM) + Scrambled control |
| Episodes | 5 | 5 (configurable) |
| Steps | 20 | 20 (configurable) |

## Reference

- Run 1 Instructions: `docs/v1.1/poc_instructions_v1.1_run1.md`
- Run 0 Results: `telemetry/run_0_results.json`
- v1.1 Spec: `docs/v1.1/poc_spec_v1.1.md`
