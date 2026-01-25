"""v1.1 Agent Loop

MVRA with audit-grade introspection.

Pipeline: Justify → Compile (+ Audits) → Mask → Select → Execute
"""

from typing import Optional, Dict, List, Set
from dataclasses import dataclass

# Import components
try:
    from ...v100.envs.commitment_trap import CommitmentTrapV100
    from ..jaf.schema import JAF110
    from ..jcomp.compiler import JCOMP110, CompilationResult
    from ..generator.deterministic import DeterministicGeneratorV110
    from ..selector.blind import BlindActionSelectorV110
    from ..state.normative import NormativeStateV110
except ImportError:
    from rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
    from rsa_poc.v110.jaf.schema import JAF110
    from rsa_poc.v110.jcomp.compiler import JCOMP110, CompilationResult
    from rsa_poc.v110.generator.deterministic import DeterministicGeneratorV110
    from rsa_poc.v110.selector.blind import BlindActionSelectorV110
    from rsa_poc.v110.state.normative import NormativeStateV110


@dataclass
class StepResult:
    """Result of one agent step"""
    step: int
    jaf: Optional[JAF110]
    compilation_result: Optional[CompilationResult]
    selected_action: Optional[str]
    reward: float
    done: bool
    info: Dict
    halted: bool = False
    halt_reason: Optional[str] = None


class MVRAAgentV110:
    """
    Minimal Viable Reflective Agent v1.1.

    Extends v1.0 with audit-grade introspection:
    - Predictive correctness (Audit A)
    - Non-vacuity (Audit B)
    - Outcome prediction (Audit C/C′)
    """

    def __init__(
        self,
        env: CommitmentTrapV100,
        normative_state: NormativeStateV110,
        generator: DeterministicGeneratorV110,
        selector: BlindActionSelectorV110,
        agent_id: str = "MVRA_v110"
    ):
        """
        Initialize v1.1 agent.

        Args:
            env: v100 environment with APCM (unchanged)
            normative_state: v110 normative state
            generator: v110 generator with prediction computation
            selector: v110 blind selector (no access to predictions)
            agent_id: Agent identifier
        """
        self.env = env
        self.normative_state = normative_state
        self.generator = generator
        self.selector = selector
        self.agent_id = agent_id

        # Initialize v1.1 compiler with environment vocabulary
        self.compiler = JCOMP110(
            valid_actions=set(env.get_action_inventory()),
            valid_preferences=env.get_all_preferences()
        )

        # Episode state
        self._step = 0
        self._total_reward = 0.0
        self._halted = False
        self._halt_reason = None
        self._step_history: List[StepResult] = []

    def reset(self, seed: Optional[int] = None):
        """Reset agent for new episode"""
        obs = self.env.reset(seed=seed)
        self.normative_state.reset()
        self.generator.reset()
        self.selector.reset(seed=seed)

        self._step = 0
        self._total_reward = 0.0
        self._halted = False
        self._halt_reason = None
        self._step_history.clear()

        return obs

    def step(self) -> StepResult:
        """
        Execute one agent step: Justify → Compile (+ Audits) → Mask → Select → Execute

        Returns:
            StepResult with full pipeline trace including audit results
        """
        self._step += 1

        if self._halted:
            return StepResult(
                step=self._step,
                jaf=None,
                compilation_result=None,
                selected_action=None,
                reward=0.0,
                done=True,
                info={"halt_reason": self._halt_reason},
                halted=True,
                halt_reason=self._halt_reason
            )

        # Get current state
        obs = self.env._get_obs()
        feasible_actions = obs["feasible_actions"]
        apcm = obs["apcm"]

        # === JUSTIFY ===
        jaf = self.generator.generate(
            feasible_actions=feasible_actions,
            apcm=apcm,
            agent_id=self.agent_id
        )

        # === COMPILE (with v1.1 audits) ===
        precedent = self.normative_state.get_precedent()
        compilation_result = self.compiler.compile(
            jaf=jaf,
            apcm=apcm,
            feasible_actions=set(feasible_actions),
            precedent=precedent
        )

        # Check for compilation failure (includes v1.0 rules + v1.1 audits)
        if not compilation_result.success:
            self._halted = True
            self._halt_reason = f"Compilation failed: {[e.code for e in compilation_result.errors]}"

            return StepResult(
                step=self._step,
                jaf=jaf,
                compilation_result=compilation_result,
                selected_action=None,
                reward=0.0,
                done=True,
                info={"halt_reason": self._halt_reason},
                halted=True,
                halt_reason=self._halt_reason
            )

        # Record precedent for next step
        self.normative_state.record_precedent(
            authorized_violations=jaf.authorized_violations,
            required_preservations=jaf.required_preservations,
            conflict_attribution=jaf.conflict_attribution,
            digest=compilation_result.digest,
            step=self._step
        )

        # === MASK ===
        action_mask = compilation_result.action_mask  # Set of forbidden actions

        # === SELECT ===
        selected_action = self.selector.select(
            feasible_actions=feasible_actions,
            forbidden_actions=action_mask
        )

        # Check for selection failure (no valid options)
        if selected_action is None:
            self._halted = True
            self._halt_reason = "No valid actions after masking"

            return StepResult(
                step=self._step,
                jaf=jaf,
                compilation_result=compilation_result,
                selected_action=None,
                reward=0.0,
                done=True,
                info={"halt_reason": self._halt_reason},
                halted=True,
                halt_reason=self._halt_reason
            )

        # === EXECUTE ===
        obs, reward, done, info = self.env.step(selected_action)
        self._total_reward += reward

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

        return result

    def run_episode(self, max_steps: Optional[int] = None) -> List[StepResult]:
        """
        Run full episode until done or halted.

        Args:
            max_steps: Override environment max_steps

        Returns:
            List of StepResult for full episode
        """
        if max_steps:
            original_max = self.env.max_steps
            self.env.max_steps = max_steps

        self.reset()

        while not self.env._done and not self._halted:
            self.step()

        if max_steps:
            self.env.max_steps = original_max

        return self._step_history.copy()

    def get_metrics(self) -> Dict:
        """Get episode metrics"""
        if not self._step_history:
            # Return halt state if halted before any steps
            if self._halted:
                return {
                    "total_steps": 0,
                    "total_reward": 0.0,
                    "violation_count": 0,
                    "collision_steps": 0,
                    "authorized_violations": 0,
                    "halted": True,
                    "halt_reason": self._halt_reason,
                    "violation_rate": 0.0,
                    # v1.1: Audit failure counts
                    "audit_failures": {
                        "effect_mismatch": 0,
                        "decorative_justification": 0,
                        "prediction_error": 0,
                        "total": 0
                    }
                }
            return {}

        # Compute violation statistics
        violation_count = 0
        collision_step_count = 0
        authorized_violation_count = 0

        # v1.1: Audit failure tracking
        audit_failures = {
            "effect_mismatch": 0,
            "decorative_justification": 0,
            "prediction_error": 0,
            "total": 0
        }

        for result in self._step_history:
            info = result.info
            if info.get("violated_prefs"):
                violation_count += len(info["violated_prefs"])

            if info.get("is_collision_step"):
                collision_step_count += 1

            if result.jaf and result.jaf.authorized_violations:
                authorized_violation_count += len(result.jaf.authorized_violations)

            # Track audit failures
            if result.compilation_result and not result.compilation_result.success:
                for error in result.compilation_result.errors:
                    if error.code == "E_EFFECT_MISMATCH":
                        audit_failures["effect_mismatch"] += 1
                        audit_failures["total"] += 1
                    elif error.code == "E_DECORATIVE_JUSTIFICATION":
                        audit_failures["decorative_justification"] += 1
                        audit_failures["total"] += 1
                    elif error.code == "E_PREDICTION_ERROR":
                        audit_failures["prediction_error"] += 1
                        audit_failures["total"] += 1

        total_steps = len(self._step_history)

        return {
            "total_steps": total_steps,
            "total_reward": self._total_reward,
            "violation_count": violation_count,
            "collision_steps": collision_step_count,
            "authorized_violations": authorized_violation_count,
            "halted": self._halted,
            "halt_reason": self._halt_reason,
            "violation_rate": violation_count / total_steps if total_steps > 0 else 0.0,
            "audit_failures": audit_failures
        }
