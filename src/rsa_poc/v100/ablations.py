"""Ablation Studies for v1.0

Three conditions:
1. ASB (Atheoretic Stochastic Baseline) - No JAF pipeline
2. MVRA Scrambled - False collision attribution (tests Rule 2)
3. MVRA Bypass - Skips compilation (tests causal necessity)
"""

from typing import Optional, List, Dict

# Import base components
try:
    from .envs.commitment_trap import CommitmentTrapV100
    from .state.normative import NormativeStateV100
    from .generator.deterministic import DeterministicGeneratorV100, ScrambledConflictGenerator
    from .selector.blind import BlindActionSelectorV100, ASBNullSelectorV100
    from .agent import MVRAAgentV100, StepResult
except ImportError:
    from src.rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
    from src.rsa_poc.v100.state.normative import NormativeStateV100
    from src.rsa_poc.v100.generator.deterministic import DeterministicGeneratorV100, ScrambledConflictGenerator
    from src.rsa_poc.v100.selector.blind import BlindActionSelectorV100, ASBNullSelectorV100
    from src.rsa_poc.v100.agent import MVRAAgentV100, StepResult


class ASBAgentV100:
    """
    Atheoretic Stochastic Baseline v1.0.

    No JAF pipeline - selects uniformly from feasible actions.
    This is the control condition showing stochastic agency without reflection.
    """

    def __init__(self, env: CommitmentTrapV100, agent_id: str = "ASB_v100"):
        """
        Initialize ASB agent.

        Args:
            env: v100 environment
            agent_id: Agent identifier
        """
        self.env = env
        self.agent_id = agent_id
        self.selector = ASBNullSelectorV100()

        # Episode state
        self._step = 0
        self._total_reward = 0.0
        self._step_history: List[StepResult] = []

    def reset(self, seed: Optional[int] = None):
        """Reset agent for new episode"""
        obs = self.env.reset(seed=seed)
        self.selector.reset(seed=seed)

        self._step = 0
        self._total_reward = 0.0
        self._step_history.clear()

        return obs

    def step(self) -> StepResult:
        """Execute one step: select uniformly, execute"""
        self._step += 1

        # Get feasible actions
        obs = self.env._get_obs()
        feasible_actions = obs["feasible_actions"]

        # Select uniformly (no constraints)
        selected_action = self.selector.select(feasible_actions)

        if selected_action is None:
            # Should never happen with ASB, but handle gracefully
            return StepResult(
                step=self._step,
                jaf=None,
                compilation_result=None,
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

        result = StepResult(
            step=self._step,
            jaf=None,
            compilation_result=None,
            selected_action=selected_action,
            reward=reward,
            done=done,
            info=info,
            halted=False
        )

        self._step_history.append(result)

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
        """Get episode metrics"""
        if not self._step_history:
            return {}

        violation_count = 0
        collision_step_count = 0

        for result in self._step_history:
            info = result.info
            if info.get("violated_prefs"):
                violation_count += len(info["violated_prefs"])

            if info.get("is_collision_step"):
                collision_step_count += 1

        total_steps = len(self._step_history)

        return {
            "total_steps": total_steps,
            "total_reward": self._total_reward,
            "violation_count": violation_count,
            "collision_steps": collision_step_count,
            "authorized_violations": 0,  # ASB doesn't authorize
            "halted": False,
            "halt_reason": None,
            "violation_rate": violation_count / total_steps if total_steps > 0 else 0.0,
        }


class MVRAScrambledAgentV100(MVRAAgentV100):
    """
    MVRA with scrambled conflict attribution.

    Tests whether truthful collision detection is causally load-bearing.
    Expected: High halt rate due to E_FALSE_COLLISION errors.
    """

    def __init__(
        self,
        env: CommitmentTrapV100,
        normative_state: NormativeStateV100,
        seed: int = 42,
        agent_id: str = "MVRA_v100_Scrambled"
    ):
        """Initialize scrambled agent"""
        # Use scrambled generator
        generator = ScrambledConflictGenerator(normative_state, seed=seed)
        selector = BlindActionSelectorV100(seed=seed)

        super().__init__(
            env=env,
            normative_state=normative_state,
            generator=generator,
            selector=selector,
            agent_id=agent_id
        )


class MVRABypassAgentV100:
    """
    MVRA with compiler bypass.

    Tests whether compilation is causally load-bearing.
    Expected: 100% violation rate (no constraints enforced).
    """

    def __init__(
        self,
        env: CommitmentTrapV100,
        normative_state: NormativeStateV100,
        agent_id: str = "MVRA_v100_Bypass"
    ):
        """Initialize bypass agent"""
        self.env = env
        self.normative_state = normative_state
        self.agent_id = agent_id

        # Generator and selector (generator runs but output ignored)
        self.generator = DeterministicGeneratorV100(normative_state)
        self.selector = ASBNullSelectorV100()  # Uniform selection, ignore mask

        # Episode state
        self._step = 0
        self._total_reward = 0.0
        self._step_history: List[StepResult] = []

    def reset(self, seed: Optional[int] = None):
        """Reset agent for new episode"""
        obs = self.env.reset(seed=seed)
        self.normative_state.reset()
        self.generator.reset()
        self.selector.reset(seed=seed)

        self._step = 0
        self._total_reward = 0.0
        self._step_history.clear()

        return obs

    def step(self) -> StepResult:
        """Execute one step: generate JAF but skip compilation"""
        self._step += 1

        # Get current state
        obs = self.env._get_obs()
        feasible_actions = obs["feasible_actions"]
        apcm = obs["apcm"]

        # Generate JAF (for logging, but not used)
        jaf = self.generator.generate(
            feasible_actions=feasible_actions,
            apcm=apcm,
            agent_id=self.agent_id
        )

        # BYPASS: Skip compilation, select uniformly
        selected_action = self.selector.select(feasible_actions)

        if selected_action is None:
            return StepResult(
                step=self._step,
                jaf=jaf,
                compilation_result=None,
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

        result = StepResult(
            step=self._step,
            jaf=jaf,
            compilation_result=None,  # Bypassed
            selected_action=selected_action,
            reward=reward,
            done=done,
            info=info,
            halted=False
        )

        self._step_history.append(result)

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
        """Get episode metrics"""
        if not self._step_history:
            return {}

        violation_count = 0
        collision_step_count = 0

        for result in self._step_history:
            info = result.info
            if info.get("violated_prefs"):
                violation_count += len(info["violated_prefs"])

            if info.get("is_collision_step"):
                collision_step_count += 1

        total_steps = len(self._step_history)

        return {
            "total_steps": total_steps,
            "total_reward": self._total_reward,
            "violation_count": violation_count,
            "collision_steps": collision_step_count,
            "authorized_violations": 0,  # Bypass doesn't use authorization
            "halted": False,
            "halt_reason": None,
            "violation_rate": violation_count / total_steps if total_steps > 0 else 0.0,
        }
