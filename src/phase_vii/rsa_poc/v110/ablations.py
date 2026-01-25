"""Ablation Studies for v1.1

Four conditions:
1. ASB (Atheoretic Stochastic Baseline) - Reuses v100
2. MVRA v1.1 Normal - Full pipeline with audits
3. Scrambled Predictions - Valid v1.0 fields, corrupted predictions
4. Bypass - Skip compilation, select uniformly
"""

from typing import Optional, List, Dict

# Import base components
try:
    from ...v100.ablations import ASBAgentV100  # Reuse v100 ASB
    from ...v100.envs.commitment_trap import CommitmentTrapV100
    from ..state.normative import NormativeStateV110
    from ..generator.deterministic import DeterministicGeneratorV110, ScrambledPredictionsGeneratorV110
    from ..selector.blind import BlindActionSelectorV110, ASBNullSelectorV110
    from ..agent import MVRAAgentV110, StepResult
except ImportError:
    from rsa_poc.v100.ablations import ASBAgentV100
    from rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
    from rsa_poc.v110.state.normative import NormativeStateV110
    from rsa_poc.v110.generator.deterministic import DeterministicGeneratorV110, ScrambledPredictionsGeneratorV110
    from rsa_poc.v110.selector.blind import BlindActionSelectorV110, ASBNullSelectorV110
    from rsa_poc.v110.agent import MVRAAgentV110, StepResult


# Re-export ASB from v100 (unchanged for v1.1)
ASBAgentV110 = ASBAgentV100


class MVRAScrambledAgentV110(MVRAAgentV110):
    """
    MVRA with scrambled predictions.

    Tests whether audit layer is causally load-bearing.
    Expected: High audit failure rate (E_EFFECT_MISMATCH, E_PREDICTION_ERROR).
    """

    def __init__(
        self,
        env: CommitmentTrapV100,
        normative_state: NormativeStateV110,
        seed: int = 42,
        agent_id: str = "MVRA_v110_Scrambled"
    ):
        """Initialize scrambled agent"""
        # Use scrambled predictions generator
        generator = ScrambledPredictionsGeneratorV110(normative_state, seed=seed)
        selector = BlindActionSelectorV110(seed=seed)

        super().__init__(
            env=env,
            normative_state=normative_state,
            generator=generator,
            selector=selector,
            agent_id=agent_id
        )


class MVRABypassAgentV110:
    """
    MVRA with compiler bypass (Bypass-mask mode).

    Generates JAF and runs compilation+audits for telemetry comparability,
    but IGNORES the action mask for selection (selects uniformly from feasible).

    Tests whether mask enforcement is causally load-bearing.
    Expected: Action distribution collapses toward ASB-like uniform selection.

    v1.1 Fix 4: Adds falsifiability metrics (mask_applied, collapse distance).
    """

    def __init__(
        self,
        env: CommitmentTrapV100,
        normative_state: NormativeStateV110,
        agent_id: str = "MVRA_v110_Bypass"
    ):
        """Initialize bypass agent"""
        self.env = env
        self.normative_state = normative_state
        self.agent_id = agent_id

        # Generator (runs and produces predictions)
        self.generator = DeterministicGeneratorV110(normative_state)
        # Selector (uniform selection, ignores mask)
        self.selector = ASBNullSelectorV110()

        # Compiler (for audits, but mask not enforced)
        try:
            from ..jcomp.compiler import JCOMP110
        except ImportError:
            from rsa_poc.v110.jcomp.compiler import JCOMP110

        # Get valid actions and preferences from environment
        env.reset()
        obs = env._get_obs()
        valid_actions = list(set(a for a in obs.get("apcm", {}).keys()))
        valid_preferences = list(normative_state.get_preferences())

        self.compiler = JCOMP110(
            valid_actions=valid_actions if valid_actions else ["COOPERATE", "DEFECT", "WAIT"],
            valid_preferences=valid_preferences if valid_preferences else ["P_NO_EXPLOIT", "P_COOPERATION"]
        )

        # Episode state
        self._step = 0
        self._total_reward = 0.0
        self._step_history: List[StepResult] = []

        # Bypass metrics
        self._mask_violations = 0  # Times selected_action not in A_actual
        self._action_distribution = {}  # Track action selection frequency

    def reset(self, seed: Optional[int] = None):
        """Reset agent for new episode"""
        obs = self.env.reset(seed=seed)
        self.normative_state.reset()
        self.generator.reset()
        self.selector.reset(seed=seed)

        self._step = 0
        self._total_reward = 0.0
        self._step_history.clear()
        self._mask_violations = 0
        self._action_distribution.clear()

        return obs

    def step(self) -> StepResult:
        """Execute one step: generate JAF, compile for audits, but ignore mask"""
        self._step += 1

        # Get current state
        obs = self.env._get_obs()
        feasible_actions = obs["feasible_actions"]
        apcm = obs["apcm"]

        # Generate JAF
        jaf = self.generator.generate(
            feasible_actions=feasible_actions,
            apcm=apcm,
            agent_id=self.agent_id
        )

        # Compile JAF (runs audits, computes mask)
        precedent = self.normative_state.get_precedent()
        compilation_result = self.compiler.compile(
            jaf=jaf,
            apcm=apcm,
            feasible_actions=set(feasible_actions),
            precedent=precedent
        )

        # Extract A_actual from compilation (for metrics)
        A_actual = set()
        if compilation_result.success and compilation_result.action_mask:
            F_actual = compilation_result.action_mask
            A_actual = set(feasible_actions) - F_actual

        # BYPASS: Select uniformly from feasible, ignoring mask
        selected_action = self.selector.select(feasible_actions)

        # Track bypass metrics
        if selected_action:
            # Track action distribution
            self._action_distribution[selected_action] = \
                self._action_distribution.get(selected_action, 0) + 1

            # Track mask violations (selected action not in allowed set)
            if A_actual and selected_action not in A_actual:
                self._mask_violations += 1

        if selected_action is None:
            return StepResult(
                step=self._step,
                jaf=jaf,
                compilation_result=compilation_result,
                selected_action=None,
                reward=0.0,
                done=True,
                info={"halt_reason": "No feasible actions"},
                halted=True,
                halt_reason="No feasible actions"
            )

        # Execute
        obs, reward, done, info = self.env.step(selected_action)
        self._total_reward += reward

        # Add bypass-specific info
        info["mask_applied"] = False  # Key metric: mask not enforced
        info["selected_in_allowed"] = selected_action in A_actual if A_actual else None
        info["A_actual"] = list(A_actual) if A_actual else []
        info["F_actual"] = list(compilation_result.action_mask) if compilation_result.action_mask else []

        result = StepResult(
            step=self._step,
            jaf=jaf,
            compilation_result=compilation_result,
            selected_action=selected_action,
            reward=reward,
            done=done,
            info=info,
            halted=False
        )

        self._step_history.append(result)

        # Update precedent if compilation succeeded
        if compilation_result.success:
            self.normative_state.record_precedent(
                authorized_violations=jaf.authorized_violations,
                required_preservations=jaf.required_preservations,
                conflict_attribution=jaf.conflict_attribution,
                digest=compilation_result.digest,
                step=self._step
            )

        return result

    def run_episode(self, max_steps: Optional[int] = None) -> List[StepResult]:
        """Run full episode"""
        if max_steps:
            original_max = self.env.max_steps
            self.env.max_steps = max_steps

        self.reset()

        while not self.env._done:
            self.step()

        if max_steps:
            self.env.max_steps = original_max

        return self._step_history.copy()

    def get_metrics(self) -> Dict:
        """Get episode metrics including bypass-specific collapse indicators"""
        if not self._step_history:
            return {}

        violation_count = 0
        collision_step_count = 0
        mask_divergence_count = 0  # Steps where selected not in A_actual

        for result in self._step_history:
            info = result.info
            if info.get("violated_prefs"):
                violation_count += len(info["violated_prefs"])

            if info.get("is_collision_step"):
                collision_step_count += 1

            # Count mask divergence
            if info.get("selected_in_allowed") == False:
                mask_divergence_count += 1

        total_steps = len(self._step_history)

        return {
            "total_steps": total_steps,
            "total_reward": self._total_reward,
            "violation_count": violation_count,
            "collision_steps": collision_step_count,
            "authorized_violations": 0,  # Bypass doesn't enforce authorization
            "halted": False,
            "halt_reason": None,
            "violation_rate": violation_count / total_steps if total_steps > 0 else 0.0,
            "audit_failures": {
                "effect_mismatch": 0,
                "decorative_justification": 0,
                "prediction_error": 0,
                "total": 0
            },
            # Bypass-specific metrics (v1.1 Fix 4)
            "bypass_metrics": {
                "mask_applied": False,  # Hard-coded: mask never enforced
                "mask_violations": self._mask_violations,
                "mask_divergence_count": mask_divergence_count,
                "mask_divergence_rate": mask_divergence_count / total_steps if total_steps > 0 else 0.0,
                "action_distribution": dict(self._action_distribution),
                "action_entropy": self._compute_action_entropy()
            }
        }

    def _compute_action_entropy(self) -> float:
        """Compute Shannon entropy of action distribution"""
        if not self._action_distribution:
            return 0.0

        import math
        total = sum(self._action_distribution.values())
        if total == 0:
            return 0.0

        entropy = 0.0
        for count in self._action_distribution.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        return entropy
