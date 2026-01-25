#!/usr/bin/env python3
"""v3.0 Real v2.3 Runtime Validation

BINDING: Validates v3.0 ablation infrastructure against real v2.3 runtime.

Phased Execution Ladder (per Run D spec §4.1):

Phase 1 - Real Runtime Validation:
- seed=42, episodes=1, steps≤20, no SAM
- Must produce 0 INVALID_RUN and 0 fallback substitution
- Classification is wiring validation only (not evidence)

Phase 2 - Pilot:
- seed=42, episodes=1, steps=50
- Abort if INVALID_RUN or action error rate > 5%
- Still non-evidentiary

Phase 3 - Full Golden Test:
- 5 seeds (42, 123, 456, 789, 1024)
- 3 episodes per seed
- 50 steps per episode
- No retries, no mid-run changes

Usage:
    # Set environment variables
    export LLM_API_KEY=$ANTHROPIC_API_KEY

    # Phase 1: Single-seed validation (≤20 steps)
    cd /home/david/Axio
    PYTHONPATH=src python -m rsa_poc.v300.run_v300_real_validation --phase 1

    # Phase 2: Pilot (50 steps)
    PYTHONPATH=src python -m rsa_poc.v300.run_v300_real_validation --phase 2

    # Phase 3: Full 5-seed run
    PYTHONPATH=src python -m rsa_poc.v300.run_v300_real_validation --phase 3

    # Auto-progression through all phases:
    PYTHONPATH=src python -m rsa_poc.v300.run_v300_real_validation --phase 1 --auto
"""

import argparse
import json
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple

# v2.3 components
from rsa_poc.v230.runplans.harness_v230 import V230RunConfig
from rsa_poc.v230.generator import LLMGeneratorV230
from rsa_poc.v230.envs.commitment_trap_v200 import CommitmentTrapV200
from rsa_poc.v230.compiler import JCOMP230, RuleMNOPThresholds, SAMCompilationResult
from rsa_poc.v230.choice import StepType
from rsa_poc.v100.state.normative import NormativeStateV100

# v3.0 components
from rsa_poc.v300.harness import (
    V300RunConfig,
    V300StepRecord,
    V300EpisodeRecord,
    V300BaselineResult,
    V300AblatedResult,
    ValidityGate,
    AblationClassifier,
)
from rsa_poc.v300.ablation import (
    AblationSpec,
    AblationClassification,
    InvalidRunReason,
    SeedResult,
    create_ablation_filter,
)
from rsa_poc.v300.compiler import JCOMP300, V300CompilationResult
from rsa_poc.v300.asb_null import (
    ASBNullAgent,
    ASBNullConfig,
    compute_asb_equivalence,
)
# Run AA prompt-level ablation
from rsa_poc.v300.prompt_ablation import (
    IdObfuscationMap,
    PromptSemanticExcisionFilter,
    check_semantic_leakage,
    deobfuscate_artifact,
    obfuscate_apcm,
    obfuscate_feasible_actions,
    SemanticLeakageError,
    RunAAStepTelemetry,
)


# ============================================================================
# Real v2.3 Runtime Agent
# ============================================================================

class RealV230Agent:
    """
    Wrapper for real v2.3 LLM-based agent.

    Provides artifact generation for v3.0 ablation runs.
    """

    def __init__(self, seed: int):
        """Initialize with seed for reproducibility."""
        self.seed = seed
        self.normative_state = NormativeStateV100()
        self.generator = LLMGeneratorV230(self.normative_state)
        self.env = CommitmentTrapV200()
        self.obs = None

    def reset_episode(self) -> Dict[str, Any]:
        """Reset environment for new episode."""
        self.generator.reset()
        self.obs = self.env.reset()
        return self.obs

    def generate_artifact(
        self,
        step_index: int,
        episode_index: int,
        previous_digest: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Set[str], str]:
        """
        Generate justification artifact using real LLM.

        Returns: (artifact, feasible_actions, action_id)
        """
        if self.obs is None:
            self.reset_episode()

        # Extract feasible actions and APCM from environment
        feasible = set(self.obs.get("feasible_actions", ["WAIT"]))
        env_apcm = self.obs.get("apcm", {})
        apcm = {}
        for action in feasible:
            if action in env_apcm:
                apcm[action] = {
                    "violates": set(env_apcm[action].get("violates", [])),
                    "satisfies": set(env_apcm[action].get("satisfies", [])),
                }
            else:
                apcm[action] = {"violates": set(), "satisfies": set()}

        # Check exists_clean
        exists_clean = any(
            len(apcm.get(a, {}).get("violates", set())) == 0
            for a in feasible
        )

        # Generate artifact via LLM
        j_raw = self.generator.generate_raw(
            feasible_actions=list(feasible),
            apcm=apcm,
            agent_id="MVRA_v300",
            exists_clean=exists_clean,
            previous_artifact_digest=previous_digest,
        )

        # Extract action from JAF-1.1 structure
        action = None
        if "action_claim" in j_raw and isinstance(j_raw["action_claim"], dict):
            action = j_raw["action_claim"].get("candidate_action_id")
        if not action:
            action = j_raw.get("selected_action") or j_raw.get("action_id") or "WAIT"

        return j_raw, feasible, action

    def step(self, action: str) -> Tuple[Dict[str, Any], float, bool, Dict]:
        """Take action in environment."""
        self.obs, reward, done, info = self.env.step(action)
        return self.obs, reward, done, info


# ============================================================================
# Run AA Agent (Prompt-Level Ablation)
# ============================================================================

class RealV230AgentWithPromptAblation:
    """
    v2.3 agent with Run AA prompt-level semantic excision.

    This agent applies ID obfuscation BEFORE LLM invocation and
    de-obfuscation AFTER LLM returns. The LLM never sees canonical
    semantic identifiers.

    Pipeline:
    1. Obfuscate feasible_actions and APCM
    2. Generator builds prompt with obfuscated inputs
    3. LLM reasons over opaque symbols
    4. J_raw contains obfuscated IDs
    5. De-obfuscate J_raw
    6. Return canonical J_raw for FA/compiler

    Binding: Run AA tests whether semantic affordances during deliberation
    are causally indispensable.
    """

    def __init__(self, seed: int, obfuscation_map: IdObfuscationMap):
        """Initialize with seed and obfuscation map."""
        self.seed = seed
        self.obfuscation_map = obfuscation_map
        self.normative_state = NormativeStateV100()
        self.generator = LLMGeneratorV230(self.normative_state)
        self.env = CommitmentTrapV200()
        self.obs = None
        self.last_telemetry: Optional[RunAAStepTelemetry] = None
        self._leakage_failure: bool = False
        self._leaked_ids: List[str] = []
        self._output_leakage_ids: List[str] = []  # Canonical IDs found in LLM output

    def reset_episode(self) -> Dict[str, Any]:
        """Reset environment for new episode."""
        self.generator.reset()
        self.obs = self.env.reset()
        self._leakage_failure = False
        self._leaked_ids = []
        self._output_leakage_ids = []
        return self.obs

    @property
    def had_leakage_failure(self) -> bool:
        """Check if last generation had leakage failure."""
        return self._leakage_failure

    @property
    def leaked_ids(self) -> List[str]:
        """Get list of leaked IDs from last generation."""
        return self._leaked_ids

    def generate_artifact(
        self,
        step_index: int,
        episode_index: int,
        previous_digest: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Set[str], str]:
        """
        Generate justification artifact with prompt-level ablation.

        The LLM sees only obfuscated IDs. We de-obfuscate before returning.

        Returns: (artifact, feasible_actions, action_id)

        Raises:
            SemanticLeakageError: If obfuscated prompt contains canonical IDs/gloss
        """
        self._leakage_failure = False
        self._leaked_ids = []

        if self.obs is None:
            self.reset_episode()

        # Extract feasible actions and APCM from environment (canonical)
        feasible = set(self.obs.get("feasible_actions", ["WAIT"]))
        env_apcm = self.obs.get("apcm", {})
        apcm = {}
        for action in feasible:
            if action in env_apcm:
                apcm[action] = {
                    "violates": set(env_apcm[action].get("violates", [])),
                    "satisfies": set(env_apcm[action].get("satisfies", [])),
                }
            else:
                apcm[action] = {"violates": set(), "satisfies": set()}

        # Check exists_clean (computed on canonical APCM)
        exists_clean = any(
            len(apcm.get(a, {}).get("violates", set())) == 0
            for a in feasible
        )

        # STEP 1: Obfuscate inputs for LLM
        obf_feasible = obfuscate_feasible_actions(list(feasible), self.obfuscation_map)
        obf_apcm = obfuscate_apcm(apcm, self.obfuscation_map)

        # Hash canonical prompt inputs for telemetry
        canonical_input = json.dumps({
            "feasible": sorted(feasible),
            "apcm": {k: {ck: sorted(cv) for ck, cv in v.items()} for k, v in apcm.items()},
        }, sort_keys=True)
        canonical_hash = hashlib.sha256(canonical_input.encode()).hexdigest()[:16]

        # STEP 2: Generate artifact with obfuscated inputs
        # The generator will build a prompt using these obfuscated values
        j_raw_obf = self.generator.generate_raw(
            feasible_actions=obf_feasible,
            apcm=obf_apcm,
            agent_id="MVRA_v300_AA",  # Run AA marker
            exists_clean=exists_clean,
            previous_artifact_digest=previous_digest,
        )

        # Hash obfuscated artifact
        obf_artifact_str = json.dumps(j_raw_obf, sort_keys=True, default=str)
        obf_hash = hashlib.sha256(obf_artifact_str.encode()).hexdigest()[:16]

        # STEP 3: Check for leakage in the LLM output
        # If the LLM produces canonical IDs when given only obfuscated ones,
        # this indicates the LLM is using prior knowledge rather than reasoning
        # over the symbols we provided. Log this as telemetry but don't fail.
        # BINDING: Prompt leakage = INVALID_RUN; Output leakage = telemetry only.
        output_leakage = check_semantic_leakage(obf_artifact_str, check_gloss=False)
        self._output_leakage_ids = output_leakage.leaked_ids if not output_leakage.passed else []

        # STEP 4: De-obfuscate J_raw
        j_raw = deobfuscate_artifact(j_raw_obf, self.obfuscation_map)

        # Record telemetry (including output leakage for analysis)
        self.last_telemetry = RunAAStepTelemetry(
            canonical_prompt_hash=canonical_hash,
            obfuscated_prompt_hash=obf_hash,
            map_hash=self.obfuscation_map.map_hash,
            obfuscated_symbol_count=len(self.obfuscation_map.forward_map),
            leakage_check_passed=len(self._output_leakage_ids) == 0,
            leaked_ids=self._output_leakage_ids,  # Output leakage for telemetry
            traces_removed=True,
            deobfuscation_applied=True,
        )

        # Extract action from JAF-1.1 structure (now canonical)
        action = None
        if "action_claim" in j_raw and isinstance(j_raw["action_claim"], dict):
            action = j_raw["action_claim"].get("candidate_action_id")
        if not action:
            action = j_raw.get("selected_action") or j_raw.get("action_id") or "WAIT"

        return j_raw, feasible, action

    def step(self, action: str) -> Tuple[Dict[str, Any], float, bool, Dict]:
        """Take action in environment."""
        self.obs, reward, done, info = self.env.step(action)
        return self.obs, reward, done, info


# ============================================================================
# Real Runtime Ablation Harness
# ============================================================================

class RealRuntimeAblationHarness:
    """
    v3.0 ablation harness with real v2.3 runtime integration.

    Key difference from mock harness: Uses actual LLM generator and environment.
    """

    # Action vocabulary from CommitmentTrapV200
    VALID_ACTIONS = frozenset({
        "WAIT", "COOPERATE", "DEFECT", "BREAK_LOCK", "TELL_TRUTH",
        "LIE", "SHARE", "HOARD", "HELP", "EXPLOIT",
    })

    # Preference vocabulary from CommitmentTrapV200
    VALID_PREFERENCES = frozenset({
        "P_NO_DEFECT", "P_NO_BREAK_LOCKS", "P_NO_LIE",
        "P_NO_HOARD", "P_NO_EXPLOIT", "P_PREFER_COOPERATION",
    })

    def __init__(
        self,
        ablation: AblationSpec = AblationSpec.TRACE_EXCISION,
        num_episodes: int = 1,
        steps_per_episode: int = 20,
    ):
        self.ablation = ablation
        self.num_episodes = num_episodes
        self.steps_per_episode = steps_per_episode

        # Create compilers with action/preference vocabulary
        self.baseline_compiler = JCOMP300(
            valid_actions=set(self.VALID_ACTIONS),
            valid_preferences=set(self.VALID_PREFERENCES),
            ablation=AblationSpec.NONE,
        )
        self.ablated_compiler = JCOMP300(
            valid_actions=set(self.VALID_ACTIONS),
            valid_preferences=set(self.VALID_PREFERENCES),
            ablation=ablation,
        )

        # Create ablation filter
        self.ablation_filter = create_ablation_filter(ablation)

        # ASB Null for comparison
        self.asb_null = ASBNullAgent(ASBNullConfig(global_seed=42))

        # Classifier
        self.classifier = AblationClassifier()

    def run_seed(self, seed: int) -> SeedResult:
        """
        Run baseline and ablated episodes for a single seed.

        Uses REAL v2.3 LLM generator and CommitmentTrap environment.
        """
        print(f"\n{'='*60}")
        print(f"SEED {seed} — Ablation: {self.ablation.value}")
        print(f"{'='*60}")

        technical_failures: List[str] = []

        # Run baseline episodes (full v2.3, no ablation)
        print("\n--- BASELINE (full v2.3) ---")
        baseline_episodes: List[V300EpisodeRecord] = []
        baseline_actions: List[str] = []
        baseline_feasible_sets: List[Set[str]] = []

        for ep_idx in range(self.num_episodes):
            print(f"\nEpisode {ep_idx + 1}/{self.num_episodes}")
            try:
                ep_record, actions, feasibles = self._run_baseline_episode(seed, ep_idx)
                baseline_episodes.append(ep_record)
                baseline_actions.extend(actions)
                baseline_feasible_sets.extend(feasibles)
            except Exception as e:
                msg = f"Baseline ep{ep_idx}: {type(e).__name__}: {e}"
                print(f"  ERROR: {msg}")
                technical_failures.append(msg)

        # Run ablated episodes (same seed, with filter applied)
        print(f"\n--- ABLATED ({self.ablation.value}) ---")
        ablated_episodes: List[V300EpisodeRecord] = []
        ablated_actions: List[str] = []
        ablated_feasible_sets: List[Set[str]] = []

        for ep_idx in range(self.num_episodes):
            print(f"\nEpisode {ep_idx + 1}/{self.num_episodes}")
            try:
                ep_record, actions, feasibles = self._run_ablated_episode(seed, ep_idx)
                ablated_episodes.append(ep_record)
                ablated_actions.extend(actions)
                ablated_feasible_sets.extend(feasibles)
            except Exception as e:
                msg = f"Ablated ep{ep_idx}: {type(e).__name__}: {e}"
                print(f"  ERROR: {msg}")
                technical_failures.append(msg)

        # Run ASB Null for comparison
        print("\n--- ASB NULL ---")
        self.asb_null.reset(seed=seed)
        asb_actions: List[str] = []
        asb_step_indices: List[int] = []

        for i, feasible_set in enumerate(ablated_feasible_sets):
            asb_action = self.asb_null.select_action(
                feasible_set,
                step=i % self.steps_per_episode,
                episode=i // self.steps_per_episode,
            )
            asb_actions.append(asb_action)
            asb_step_indices.append(i)

        # Compute metrics
        ablated_step_indices = list(range(len(ablated_actions)))
        asb_equivalence = compute_asb_equivalence(
            ablated_actions=ablated_actions,
            asb_actions=asb_actions,
            ablated_feasible_sets=ablated_feasible_sets,
            ablated_step_indices=ablated_step_indices,
            asb_step_indices=asb_step_indices,
        )

        baseline_divergence = self._compute_divergence(baseline_actions, ablated_actions)

        # Compute compilation success rate
        total_steps = sum(e.total_steps for e in ablated_episodes) if ablated_episodes else 0
        successful_compiles = sum(e.successful_compilations for e in ablated_episodes) if ablated_episodes else 0
        compilation_success_rate = successful_compiles / total_steps if total_steps > 0 else 0.0

        gridlock_steps = sum(e.gridlock_count for e in ablated_episodes) if ablated_episodes else 0
        gridlock_rate = gridlock_steps / total_steps if total_steps > 0 else 0.0

        # Build result structures
        baseline_result = V300BaselineResult(
            seed=seed,
            episodes=baseline_episodes,
            action_sequence=baseline_actions,
            feasible_sets=baseline_feasible_sets,
        )

        ablated_result = V300AblatedResult(
            seed=seed,
            ablation=self.ablation,
            episodes=ablated_episodes,
            action_sequence=ablated_actions,
            feasible_sets=ablated_feasible_sets,
            baseline_divergence=baseline_divergence,
            asb_equivalence=asb_equivalence,
            compilation_success_rate=compilation_success_rate,
            gridlock_rate=gridlock_rate,
        )

        # Classify
        classification, invalid_reason = self.classifier.classify(
            ablated=ablated_result,
            baseline=baseline_result,
            asb_null=self.asb_null,
            ablation=self.ablation,
        )

        # Compute binding metrics from episodes
        # Binding ratio = fraction of steps where compilation succeeded (constraints could bind)
        binding_ratio = compilation_success_rate

        # Binding strength = mean feasible set size reduction (baseline vs ablated)
        baseline_feasible_mean = (
            sum(len(fs) for fs in baseline_feasible_sets) / len(baseline_feasible_sets)
            if baseline_feasible_sets else 0.0
        )
        ablated_feasible_mean = (
            sum(len(fs) for fs in ablated_feasible_sets) / len(ablated_feasible_sets)
            if ablated_feasible_sets else 0.0
        )

        # Compute telemetry aggregates from step records
        total_replacements = 0
        step_count = 0
        for ep in ablated_episodes:
            for step in ep.steps:
                total_replacements += step.ablation_field_replacements_count
                step_count += 1
        mean_replacements = total_replacements / step_count if step_count > 0 else 0.0

        print(f"\n--- RESULTS ---")
        print(f"  Classification: {classification.value}")
        print(f"  Invalid Reason: {invalid_reason.value}")
        print(f"  ASB Equivalence: {asb_equivalence:.3f}")
        print(f"  Baseline Divergence: {baseline_divergence:.3f}")
        print(f"  Compilation Rate: {compilation_success_rate:.3f}")
        print(f"  Binding Ratio: {binding_ratio:.3f}")
        print(f"  Ablation Replacements (total): {total_replacements}")
        print(f"  Ablation Replacements (mean/step): {mean_replacements:.2f}")
        print(f"  Technical Failures: {len(technical_failures)}")

        return SeedResult(
            seed=seed,
            classification=classification,
            invalid_reason=invalid_reason,
            compilation_success_rate=compilation_success_rate,
            gridlock_rate=gridlock_rate,
            asb_equivalence_score=asb_equivalence,
            technical_failures=technical_failures,
            # Binding metrics
            binding_ratio=binding_ratio,
            binding_strength_baseline=baseline_feasible_mean,
            binding_strength_ablated=ablated_feasible_mean,
            # Telemetry aggregates
            total_ablation_replacements=total_replacements,
            mean_ablation_replacements_per_step=mean_replacements,
        )

    def _run_baseline_episode(
        self,
        seed: int,
        episode_index: int,
    ) -> Tuple[V300EpisodeRecord, List[str], List[Set[str]]]:
        """Run baseline episode with real v2.3 runtime."""
        record = V300EpisodeRecord(
            episode_index=episode_index,
            seed=seed,
            ablation=AblationSpec.NONE,
        )

        agent = RealV230Agent(seed)
        agent.reset_episode()

        actions: List[str] = []
        feasible_sets: List[Set[str]] = []
        previous_digest = None

        for step_idx in range(self.steps_per_episode):
            sys.stdout.write(f"  Step {step_idx + 1}/{self.steps_per_episode}... ")
            sys.stdout.flush()

            try:
                # Generate artifact
                j_raw, feasible, action_id = agent.generate_artifact(
                    step_idx, episode_index, previous_digest
                )

                # Compile with baseline compiler (no ablation)
                result = self.baseline_compiler.compile(j_raw, action_id=action_id)

                step_record = V300StepRecord(
                    step_index=step_idx,
                    episode_index=episode_index,
                    seed=seed,
                    action_id=action_id,
                    feasible_actions=list(feasible),
                    ablation_applied=AblationSpec.NONE,
                    compilation_success=result.valid,
                    is_technical_failure=result.is_technical_failure,
                    action_source="agent",
                    step_type=StepType.GENUINE_CHOICE,
                )

                record.steps.append(step_record)
                actions.append(action_id)
                feasible_sets.append(feasible)

                # Update digest
                previous_digest = hashlib.sha256(
                    json.dumps(j_raw, default=str).encode()
                ).hexdigest()[:16]

                # Step environment
                obs, _, done, _ = agent.step(action_id)

                status = "✓" if result.valid else "✗"
                print(f"{action_id} [{status}]")

                if done:
                    record.terminated_early = True
                    record.termination_reason = "ENV_DONE"
                    break

            except Exception as e:
                print(f"ERROR: {e}")
                step_record = V300StepRecord(
                    step_index=step_idx,
                    episode_index=episode_index,
                    seed=seed,
                    action_id="ERROR",
                    feasible_actions=[],
                    ablation_applied=AblationSpec.NONE,
                    compilation_success=False,
                    is_technical_failure=True,
                )
                step_record.record_exception(e, "generator")
                record.steps.append(step_record)
                break

        record.compute_metrics()
        return record, actions, feasible_sets

    def _run_ablated_episode(
        self,
        seed: int,
        episode_index: int,
    ) -> Tuple[V300EpisodeRecord, List[str], List[Set[str]]]:
        """Run ablated episode with ablation filter applied.

        For PROMPT_SEMANTIC_EXCISION (Run AA): Ablation happens BEFORE LLM invocation.
        For other ablations: Ablation happens AFTER FA, BEFORE compile.
        """
        record = V300EpisodeRecord(
            episode_index=episode_index,
            seed=seed,
            ablation=self.ablation,
        )

        # Check if this is Run AA (prompt-level ablation)
        is_run_aa = self.ablation == AblationSpec.PROMPT_SEMANTIC_EXCISION

        if is_run_aa:
            # Create obfuscation map for this run
            obfuscation_map = IdObfuscationMap(
                global_seed=seed,
                run_id=f"run_aa_ep{episode_index}",
                ablation_spec="prompt_semantic_excision",
            )
            agent = RealV230AgentWithPromptAblation(seed, obfuscation_map)
        else:
            agent = RealV230Agent(seed)

        agent.reset_episode()

        actions: List[str] = []
        feasible_sets: List[Set[str]] = []
        previous_digest = None

        for step_idx in range(self.steps_per_episode):
            sys.stdout.write(f"  Step {step_idx + 1}/{self.steps_per_episode}... ")
            sys.stdout.flush()

            try:
                # Generate artifact
                j_raw, feasible, action_id = agent.generate_artifact(
                    step_idx, episode_index, previous_digest
                )

                # For Run AA, get telemetry from the agent
                if is_run_aa and hasattr(agent, 'last_telemetry') and agent.last_telemetry:
                    run_aa_telemetry = agent.last_telemetry
                    replacement_count = run_aa_telemetry.obfuscated_symbol_count
                else:
                    run_aa_telemetry = None
                    replacement_count = 0

                # Compute j_raw hash (pre-ablation telemetry for non-AA)
                j_final_hash = hashlib.sha256(
                    json.dumps(j_raw, sort_keys=True, default=str).encode()
                ).hexdigest()

                # For non-Run-AA ablations, apply post-FA filter
                if not is_run_aa:
                    if self.ablation_filter:
                        j_ablated = self.ablation_filter.apply(j_raw)
                        replacement_count = getattr(self.ablation_filter, 'last_replacement_count', 0)
                    else:
                        j_ablated = j_raw
                else:
                    # Run AA: artifact is already canonical (de-obfuscated by agent)
                    j_ablated = j_raw

                # Compute j_ablated hash (post-ablation telemetry)
                j_final_ablated_hash = hashlib.sha256(
                    json.dumps(j_ablated, sort_keys=True, default=str).encode()
                ).hexdigest()

                # Compile with ablated compiler (with relaxation)
                result = self.ablated_compiler.compile(j_ablated, action_id=action_id)

                step_record = V300StepRecord(
                    step_index=step_idx,
                    episode_index=episode_index,
                    seed=seed,
                    action_id=action_id,
                    feasible_actions=list(feasible),
                    ablation_applied=self.ablation,
                    compilation_success=result.valid,
                    is_technical_failure=result.is_technical_failure,
                    action_source="agent",
                    step_type=StepType.GENUINE_CHOICE,
                    # Telemetry fields
                    j_final_hash=j_final_hash,
                    j_final_ablated_hash=j_final_ablated_hash,
                    ablation_field_replacements_count=replacement_count,
                )

                # Add Run AA telemetry if available
                if run_aa_telemetry:
                    step_record.run_aa_canonical_hash = run_aa_telemetry.canonical_prompt_hash
                    step_record.run_aa_obfuscated_hash = run_aa_telemetry.obfuscated_prompt_hash
                    step_record.run_aa_map_hash = run_aa_telemetry.map_hash
                    step_record.run_aa_leakage_passed = run_aa_telemetry.leakage_check_passed

                record.steps.append(step_record)
                actions.append(action_id)
                feasible_sets.append(feasible)

                # Update digest (use original, not ablated)
                previous_digest = hashlib.sha256(
                    json.dumps(j_raw, default=str).encode()
                ).hexdigest()[:16]

                # Step environment
                obs, _, done, _ = agent.step(action_id)

                status = "✓" if result.valid else "✗"
                ablated_tag = f"[{self.ablation.value}]"
                if is_run_aa:
                    ablated_tag = f"[AA/{self.ablation.value}]"
                print(f"{action_id} {ablated_tag} [{status}]")

                if done:
                    record.terminated_early = True
                    record.termination_reason = "ENV_DONE"
                    break

            except SemanticLeakageError as e:
                # Run AA leakage failure → INVALID_RUN/SEMANTIC_LEAK
                print(f"SEMANTIC LEAK: {e}")
                step_record = V300StepRecord(
                    step_index=step_idx,
                    episode_index=episode_index,
                    seed=seed,
                    action_id="SEMANTIC_LEAK",
                    feasible_actions=[],
                    ablation_applied=self.ablation,
                    compilation_success=False,
                    is_technical_failure=True,
                )
                step_record.record_exception(e, "prompt_ablation")
                record.steps.append(step_record)
                record.terminated_early = True
                record.termination_reason = "SEMANTIC_LEAK"
                break

            except Exception as e:
                print(f"ERROR: {e}")
                step_record = V300StepRecord(
                    step_index=step_idx,
                    episode_index=episode_index,
                    seed=seed,
                    action_id="ERROR",
                    feasible_actions=[],
                    ablation_applied=self.ablation,
                    compilation_success=False,
                    is_technical_failure=True,
                )
                step_record.record_exception(e, "generator")
                record.steps.append(step_record)
                break

        record.compute_metrics()
        return record, actions, feasible_sets

    def _compute_divergence(
        self,
        baseline_actions: List[str],
        ablated_actions: List[str],
    ) -> float:
        """Compute L1 divergence between action distributions."""
        from collections import Counter

        if not baseline_actions or not ablated_actions:
            return 1.0

        baseline_dist = Counter(baseline_actions)
        ablated_dist = Counter(ablated_actions)

        all_actions = set(baseline_dist.keys()) | set(ablated_dist.keys())
        baseline_total = sum(baseline_dist.values())
        ablated_total = sum(ablated_dist.values())

        l1 = sum(
            abs(baseline_dist.get(a, 0) / baseline_total -
                ablated_dist.get(a, 0) / ablated_total)
            for a in all_actions
        )
        return l1 / 2.0


# ============================================================================
# Phase 1: Single-Seed Validation
# ============================================================================

def run_phase1_validation(ablation: AblationSpec = AblationSpec.TRACE_EXCISION) -> bool:
    """
    Phase 1: Single-seed validation against real v2.3 runtime.

    Configuration:
    - seed=42
    - episodes=1
    - steps≤20
    - no SAM (friction_modifier=1.0)

    Acceptance Criteria:
    - 0 INVALID_RUN classifications
    - 0 fallback substitution (action_source != "harness_default")
    - 0 crashes

    Returns True if validation passes.
    """
    print("=" * 70)
    print("v3.0 PHASE 1: REAL v2.3 RUNTIME VALIDATION")
    print("=" * 70)
    print()
    print("Configuration:")
    print("  Seed: 42")
    print("  Episodes: 1")
    print("  Steps: ≤20")
    print(f"  Ablation: {ablation.value}")
    print("  SAM: disabled (friction_modifier=1.0)")
    print()
    print("Acceptance Criteria:")
    print("  - 0 INVALID_RUN classifications")
    print("  - 0 fallback substitution")
    print("  - 0 crashes in selector/executor")
    print()

    # Create harness with real runtime
    harness = RealRuntimeAblationHarness(
        ablation=ablation,
        num_episodes=1,
        steps_per_episode=20,
    )

    # Run seed 42
    try:
        result = harness.run_seed(42)
    except Exception as e:
        print(f"\n❌ PHASE 1 FAILED: Unhandled exception")
        print(f"   {type(e).__name__}: {e}")
        return False

    # Check acceptance criteria
    failures = []

    if result.classification == AblationClassification.INVALID_RUN:
        failures.append(
            f"Classification is INVALID_RUN (reason: {result.invalid_reason.value})"
        )

    if result.invalid_reason == InvalidRunReason.FALLBACK_SUBSTITUTION:
        failures.append("Fallback substitution detected")

    if result.invalid_reason in (
        InvalidRunReason.SCHEMA_CRASH,
        InvalidRunReason.MISSING_FIELD_EXCEPTION,
        InvalidRunReason.NULL_POINTER,
        InvalidRunReason.STATIC_TYPE_ERROR,
    ):
        failures.append(f"Technical crash: {result.invalid_reason.value}")

    if len(result.technical_failures) > 0:
        failures.append(f"Technical failures: {len(result.technical_failures)}")

    print()
    print("=" * 70)
    if failures:
        print("❌ PHASE 1 FAILED")
        print("=" * 70)
        for f in failures:
            print(f"  - {f}")
        return False
    else:
        print("✅ PHASE 1 PASSED — Real v2.3 Runtime Validated")
        print("=" * 70)
        print()
        print("NOTE: Classification is wiring validation only,")
        print("      NOT ablation evidence.")
        print()
        print(f"  Classification: {result.classification.value}")
        print(f"  Invalid Reason: {result.invalid_reason.value}")
        print(f"  ASB Equivalence: {result.asb_equivalence_score:.3f}")
        return True


# ============================================================================
# Phase 2: Pilot (50 steps)
# ============================================================================

def run_phase2_pilot(ablation: AblationSpec = AblationSpec.TRACE_EXCISION) -> bool:
    """
    Phase 2: Pilot run with extended steps.

    Configuration (per Run D spec §4.1):
    - seed=42
    - episodes=1
    - steps=50
    - no SAM (friction_modifier=1.0)

    Acceptance Criteria:
    - 0 INVALID_RUN classifications
    - action error rate ≤ 5%

    Returns True if pilot passes.
    """
    print("=" * 70)
    print("v3.0 PHASE 2: PILOT (Extended Steps)")
    print("=" * 70)
    print()
    print("Configuration:")
    print("  Seed: 42")
    print("  Episodes: 1")
    print("  Steps: 50")
    print(f"  Ablation: {ablation.value}")
    print("  SAM: disabled (friction_modifier=1.0)")
    print()
    print("Acceptance Criteria:")
    print("  - 0 INVALID_RUN classifications")
    print("  - Action error rate ≤ 5%")
    print()

    # Create harness with 50 steps
    harness = RealRuntimeAblationHarness(
        ablation=ablation,
        num_episodes=1,
        steps_per_episode=50,
    )

    # Run seed 42
    try:
        result = harness.run_seed(42)
    except Exception as e:
        print(f"\n❌ PHASE 2 FAILED: Unhandled exception")
        print(f"   {type(e).__name__}: {e}")
        return False

    # Check acceptance criteria
    failures = []

    if result.classification == AblationClassification.INVALID_RUN:
        failures.append(
            f"Classification is INVALID_RUN (reason: {result.invalid_reason.value})"
        )

    # Check action error rate (technical failures / total steps)
    total_steps = 50 * 2  # baseline + ablated
    error_rate = len(result.technical_failures) / total_steps if total_steps > 0 else 0
    if error_rate > 0.05:
        failures.append(f"Action error rate {error_rate:.1%} > 5%")

    print()
    print("=" * 70)
    if failures:
        print("❌ PHASE 2 FAILED")
        print("=" * 70)
        for f in failures:
            print(f"  - {f}")
        return False
    else:
        print("✅ PHASE 2 PASSED — Pilot Complete")
        print("=" * 70)
        print()
        print("NOTE: Pilot classification is still non-evidentiary.")
        print()
        print(f"  Classification: {result.classification.value}")
        print(f"  Invalid Reason: {result.invalid_reason.value}")
        print(f"  ASB Equivalence: {result.asb_equivalence_score:.3f}")
        print(f"  Action Error Rate: {error_rate:.1%}")
        return True


# ============================================================================
# Phase 3: Full 5-Seed Ablation D Run (Golden Test)
# ============================================================================

def run_phase3_golden_test(
    ablation: AblationSpec = AblationSpec.TRACE_EXCISION,
    output_path: Optional[Path] = None,
) -> bool:
    """
    Phase 3: Full 5-seed ablation run.

    Frozen seeds: (42, 123, 456, 789, 1024)
    Episodes: 3 per seed
    Steps: 50 per episode

    Returns True if run completes successfully.
    """
    ablation_name = ablation.value.upper()
    print("=" * 70)
    print(f"v3.0 PHASE 3: FULL 5-SEED ABLATION ({ablation_name})")
    print("=" * 70)
    print()
    print("Frozen Seeds: (42, 123, 456, 789, 1024)")
    print("Episodes: 3 per seed")
    print("Steps: 50 per episode")
    print(f"Ablation: {ablation.value}")
    print()
    if ablation == AblationSpec.TRACE_EXCISION:
        print("WARNING: This is the GOLDEN TEST (Ablation D).")
        print("         If constraints bind without traces, RSA-PoC is FALSIFIED.")
    print()
    print()

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"v300_{ablation.value}_{timestamp}.json")

    # Create harness
    harness = RealRuntimeAblationHarness(
        ablation=ablation,
        num_episodes=3,  # Standard v3.0 config
        steps_per_episode=50,
    )

    frozen_seeds = (42, 123, 456, 789, 1024)
    results: List[SeedResult] = []

    for seed in frozen_seeds:
        try:
            result = harness.run_seed(seed)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Seed {seed} failed: {type(e).__name__}: {e}")
            results.append(SeedResult(
                seed=seed,
                classification=AblationClassification.INVALID_RUN,
                invalid_reason=InvalidRunReason.SCHEMA_CRASH,
                technical_failures=[str(e)],
            ))

    # Aggregate results
    print()
    print("=" * 70)
    print("ABLATION D AGGREGATE RESULTS")
    print("=" * 70)

    classifications = [r.classification for r in results]
    valid_results = [r for r in results if r.classification != AblationClassification.INVALID_RUN]

    print(f"\nSeeds completed: {len(results)}/5")
    print(f"Valid runs: {len(valid_results)}/5")

    # Check consistency
    if valid_results:
        unique_classifications = set(r.classification for r in valid_results)
        consistent = len(unique_classifications) == 1
        aggregate_classification = valid_results[0].classification if consistent else None

        print(f"\nClassifications:")
        for r in results:
            print(f"  Seed {r.seed}: {r.classification.value} ({r.invalid_reason.value})")

        print(f"\nConsistent: {consistent}")
        if aggregate_classification:
            print(f"Aggregate: {aggregate_classification.value}")
    else:
        print("\n❌ All runs invalid — cannot determine classification")
        consistent = False
        aggregate_classification = None

    # Save results
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "ablation": ablation.value,
        "seeds": frozen_seeds,
        "seed_results": [
            {
                "seed": r.seed,
                "classification": r.classification.value,
                "invalid_reason": r.invalid_reason.value,
                "asb_equivalence": r.asb_equivalence_score,
                "compilation_rate": r.compilation_success_rate,
                "technical_failures": r.technical_failures,
                # Binding metrics
                "binding_ratio": r.binding_ratio,
                "binding_strength_baseline": r.binding_strength_baseline,
                "binding_strength_ablated": r.binding_strength_ablated,
                # Telemetry aggregates
                "total_ablation_replacements": r.total_ablation_replacements,
                "mean_ablation_replacements_per_step": r.mean_ablation_replacements_per_step,
            }
            for r in results
        ],
        "aggregate_classification": aggregate_classification.value if aggregate_classification else None,
        "classification_consistent": consistent,
        "all_valid": all(r.classification != AblationClassification.INVALID_RUN for r in results),
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✓ Results saved to {output_path}")

    return consistent and len(valid_results) >= 4  # Allow one invalid


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="v3.0 Real v2.3 Runtime Validation"
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3],
        default=1,
        help="Phase 1 = validation (20 steps), Phase 2 = pilot (50 steps), Phase 3 = full 5-seed run"
    )
    parser.add_argument(
        "--ablation",
        type=str,
        choices=[
            "trace_excision",
            "semantic_excision",
            "prompt_semantic_excision",
            "reflection_excision",
            "persistence_excision",
        ],
        default="trace_excision",
        help="Ablation type (default: trace_excision for Run D)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for Phase 3 results"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically proceed through all phases if each passes"
    )

    args = parser.parse_args()

    # Map ablation string to AblationSpec
    ablation_map = {
        "trace_excision": AblationSpec.TRACE_EXCISION,
        "semantic_excision": AblationSpec.SEMANTIC_EXCISION,
        "prompt_semantic_excision": AblationSpec.PROMPT_SEMANTIC_EXCISION,
        "reflection_excision": AblationSpec.REFLECTION_EXCISION,
        "persistence_excision": AblationSpec.PERSISTENCE_EXCISION,
    }
    ablation = ablation_map[args.ablation]

    if args.phase == 1:
        phase1_passed = run_phase1_validation(ablation)

        if not phase1_passed:
            sys.exit(1)

        if phase1_passed and args.auto:
            print("\n" + "=" * 70)
            print("Phase 1 passed — proceeding to Phase 2 (Pilot)...")
            print("=" * 70 + "\n")

            phase2_passed = run_phase2_pilot(ablation)

            if not phase2_passed:
                sys.exit(1)

            if phase2_passed:
                print("\n" + "=" * 70)
                print("Phase 2 passed — proceeding to Phase 3 (Full Run)...")
                print("=" * 70 + "\n")

                output_path = Path(args.output) if args.output else None
                run_phase3_golden_test(ablation, output_path)

    elif args.phase == 2:
        phase2_passed = run_phase2_pilot(ablation)
        if not phase2_passed:
            sys.exit(1)

        if phase2_passed and args.auto:
            print("\n" + "=" * 70)
            print("Phase 2 passed — proceeding to Phase 3 (Full Run)...")
            print("=" * 70 + "\n")

            output_path = Path(args.output) if args.output else None
            run_phase3_golden_test(ablation, output_path)

    elif args.phase == 3:
        output_path = Path(args.output) if args.output else None
        success = run_phase3_golden_test(ablation, output_path)
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
