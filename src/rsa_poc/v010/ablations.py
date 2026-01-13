"""Ablation Variants for RSA-PoC v0.1

Required conditions per spec:
A. ASB Null Baseline
B. MVRA Normal
C. Ablation A: Scrambled Justifications
D. Ablation B: Compiler Bypass
"""

from typing import Dict, Any

# Handle both package and script imports
try:
    from ..envs.commitment_trap import CommitmentTrapV010
    from ..state.normative import NormativeState
    from ..generator.deterministic import DeterministicJustificationGenerator, ScrambledJustificationGenerator
    from ..jcomp.compiler import JCOMP010
    from ..selector.blind import BlindActionSelector, ASBNullSelector
    from ..telemetry.logger import TelemetryLogger, RunMetrics
except ImportError:
    from envs.commitment_trap import CommitmentTrapV010
    from state.normative import NormativeState
    from generator.deterministic import DeterministicJustificationGenerator, ScrambledJustificationGenerator
    from jcomp.compiler import JCOMP010
    from selector.blind import BlindActionSelector, ASBNullSelector
    from telemetry.logger import TelemetryLogger, RunMetrics


class ASBNullAgent:
    """
    Condition A: ASB Null Baseline

    No JAF, no compiler, no mask.
    Selects action directly from feasible set.
    """

    def __init__(
        self,
        env: CommitmentTrapV010,
        selector: ASBNullSelector,
        logger: TelemetryLogger
    ):
        self.env = env
        self.selector = selector
        self.logger = logger
        self.metrics = RunMetrics()

    def run_episode(self, seed: int, max_steps: int = 50) -> Dict[str, Any]:
        """Run episode with ASB null baseline"""
        obs = self.env.reset(seed=seed)
        self.metrics = RunMetrics()

        self.logger.log_event("episode_start", {
            "condition": "ASB_NULL_BASELINE",
            "seed": seed,
            "max_steps": max_steps
        })

        done = False
        step = 0

        while not done and step < max_steps:
            feasible_actions = obs["feasible_actions"]

            # Select directly without normative gating
            selected_action = self.selector.select_action(
                feasible_actions=feasible_actions,
                env_obs=obs
            )

            # Execute
            next_obs, reward, done, info = self.env.step(selected_action)

            is_violation = info.get("is_temptation", False)

            # Log step
            self.logger.log_step({
                "condition": "ASB_NULL",
                "step": step,
                "feasible_actions": feasible_actions,
                "feasible_count": len(feasible_actions),
                "selected_action": selected_action,
                "reward": reward,
                "is_violation": is_violation,
                "done": done,
            })

            # Update metrics
            self.metrics.update_step(
                compile_ok=True,  # N/A for ASB
                is_decorative=True,  # All "constraints" are decorative (none exist)
                is_nontrivial=False,
                is_gridlock=False,
                is_halt=False,
                reward=reward,
                is_violation=is_violation
            )

            obs = next_obs
            step += 1

        summary = self.metrics.to_dict()
        self.logger.log_run_summary(summary)

        return summary


class MVRAScrambledAgent:
    """
    Condition C: Ablation A - Scrambled Justifications

    Uses ScrambledJustificationGenerator to produce corrupted JAF artifacts.
    Expected: compile failures increase OR masks differ from normal MVRA.
    """

    def __init__(
        self,
        env: CommitmentTrapV010,
        generator: ScrambledJustificationGenerator,
        selector: BlindActionSelector,
        logger: TelemetryLogger,
        agent_id: str = "MVRA_SCRAMBLED"
    ):
        self.env = env
        self.generator = generator
        self.selector = selector
        self.logger = logger
        self.normative_state = NormativeState(agent_id=agent_id)
        self.metrics = RunMetrics()

    def run_episode(self, seed: int, max_steps: int = 50) -> Dict[str, Any]:
        """Run episode with scrambled justifications"""
        obs = self.env.reset(seed=seed)
        self.normative_state = NormativeState(agent_id=self.normative_state.agent_id)
        self.metrics = RunMetrics()

        self.logger.log_event("episode_start", {
            "condition": "MVRA_SCRAMBLED",
            "seed": seed,
            "max_steps": max_steps
        })

        done = False
        step = 0

        while not done and step < max_steps:
            feasible_actions = obs["feasible_actions"]
            action_inventory = obs["action_inventory"]

            # Generate scrambled JAF
            try:
                jaf_artifact = self.generator.generate(
                    self.normative_state,
                    feasible_actions,
                    step
                )
                jaf_generated = True
            except Exception as e:
                self.logger.log_step({
                    "condition": "MVRA_SCRAMBLED",
                    "step": step,
                    "jaf_generated": False,
                    "error": str(e),
                    "halt": True,
                })
                break

            # Compile (expected to fail often)
            constraint = JCOMP010.compile(
                artifact=jaf_artifact,
                action_inventory=action_inventory,
                feasible_actions=set(feasible_actions)
            )

            if not constraint.compile_ok:
                # Compilation failed - halt
                self.logger.log_step({
                    "condition": "MVRA_SCRAMBLED",
                    "step": step,
                    "compile_ok": False,
                    "compile_error_code": constraint.error_code,
                    "halt": True,
                })
                self.metrics.update_step(
                    compile_ok=False,
                    is_decorative=False,
                    is_nontrivial=False,
                    is_gridlock=False,
                    is_halt=True
                )
                break

            # If compilation succeeds, continue as normal
            action_mask = constraint.mask
            feasible_post_mask = [
                a for a in feasible_actions
                if action_mask.get(a, "ALLOW") == "ALLOW"
            ]

            if not feasible_post_mask:
                # Gridlock
                self.logger.log_step({
                    "condition": "MVRA_SCRAMBLED",
                    "step": step,
                    "gridlock": True,
                })
                break

            # Select
            selected_action = self.selector.select_action(
                feasible_actions=feasible_actions,
                action_mask=action_mask,
                env_obs=obs
            )

            # Execute
            next_obs, reward, done, info = self.env.step(selected_action)

            is_violation = info.get("is_temptation", False)

            self.logger.log_step({
                "condition": "MVRA_SCRAMBLED",
                "step": step,
                "compile_ok": True,
                "selected_action": selected_action,
                "reward": reward,
                "is_violation": is_violation,
            })

            self.metrics.update_step(
                compile_ok=True,
                is_decorative=(len(constraint.nontrivial_forbidden_action_ids) == 0),
                is_nontrivial=(len(constraint.nontrivial_forbidden_action_ids) > 0),
                is_gridlock=False,
                is_halt=False,
                reward=reward,
                is_violation=is_violation
            )

            obs = next_obs
            step += 1
            self.normative_state.increment_step()

        summary = self.metrics.to_dict()
        self.logger.log_run_summary(summary)

        return summary


class MVRABypassAgent:
    """
    Condition D: Ablation B - Compiler Bypass

    Bypasses compilation and forces empty forbid list (all actions allowed).
    Expected: behavior collapses toward ASB baseline.
    """

    def __init__(
        self,
        env: CommitmentTrapV010,
        generator: DeterministicJustificationGenerator,
        selector: BlindActionSelector,
        logger: TelemetryLogger,
        agent_id: str = "MVRA_BYPASS"
    ):
        self.env = env
        self.generator = generator
        self.selector = selector
        self.logger = logger
        self.normative_state = NormativeState(agent_id=agent_id)
        self.metrics = RunMetrics()

    def run_episode(self, seed: int, max_steps: int = 50) -> Dict[str, Any]:
        """Run episode with compiler bypass"""
        obs = self.env.reset(seed=seed)
        self.normative_state = NormativeState(agent_id=self.normative_state.agent_id)
        self.metrics = RunMetrics()

        self.logger.log_event("episode_start", {
            "condition": "MVRA_BYPASS",
            "seed": seed,
            "max_steps": max_steps
        })

        done = False
        step = 0

        while not done and step < max_steps:
            feasible_actions = obs["feasible_actions"]
            action_inventory = obs["action_inventory"]

            # Generate JAF (but ignore it)
            jaf_artifact = self.generator.generate(
                self.normative_state,
                feasible_actions,
                step
            )

            # BYPASS: Force empty forbid list (all ALLOW)
            action_mask = {action: "ALLOW" for action in action_inventory}

            # Select with trivial mask
            selected_action = self.selector.select_action(
                feasible_actions=feasible_actions,
                action_mask=action_mask,
                env_obs=obs
            )

            # Execute
            next_obs, reward, done, info = self.env.step(selected_action)

            is_violation = info.get("is_temptation", False)

            self.logger.log_step({
                "condition": "MVRA_BYPASS",
                "step": step,
                "bypass": True,
                "selected_action": selected_action,
                "reward": reward,
                "is_violation": is_violation,
            })

            self.metrics.update_step(
                compile_ok=True,
                is_decorative=True,  # All constraints bypassed
                is_nontrivial=False,
                is_gridlock=False,
                is_halt=False,
                reward=reward,
                is_violation=is_violation
            )

            obs = next_obs
            step += 1
            self.normative_state.increment_step()

        summary = self.metrics.to_dict()
        self.logger.log_run_summary(summary)

        return summary
