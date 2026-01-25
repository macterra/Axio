"""MVRA Agent Loop - Minimal Viable Reflective Agent

Implements the strictly ordered pipeline:
Justify → Compile → Mask → Select → Execute
"""

from typing import Optional, Dict, Any

# Handle both package and script imports
try:
    from ..envs.commitment_trap import CommitmentTrapV010
    from ..state.normative import NormativeState, PreferenceRegistryV010
    from ..generator.deterministic import DeterministicJustificationGenerator
    from ..jcomp.compiler import JCOMP010
    from ..selector.blind import BlindActionSelector
    from ..telemetry.logger import TelemetryLogger, RunMetrics
except ImportError:
    from envs.commitment_trap import CommitmentTrapV010
    from state.normative import NormativeState, PreferenceRegistryV010
    from generator.deterministic import DeterministicJustificationGenerator
    from jcomp.compiler import JCOMP010
    from selector.blind import BlindActionSelector
    from telemetry.logger import TelemetryLogger, RunMetrics


class MVRAAgent:
    """
    Minimal Viable Reflective Agent for RSA-PoC v0.1.

    Critical ordering:
    1. Observe (includes feasibility)
    2. Generate JAF from (normative state + feasibility)
    3. Compile JAF → constraint mask
    4. Apply mask to feasible set
    5. Select action from masked feasible set
    6. Execute
    7. Log and update state

    Prohibited:
    - Propose action before justifying
    - Justify as permission slip
    - Compile after selecting
    - Selector accessing raw justification
    """

    def __init__(
        self,
        env: CommitmentTrapV010,
        generator: DeterministicJustificationGenerator,
        selector: BlindActionSelector,
        logger: TelemetryLogger,
        agent_id: str = "MVRA_V010"
    ):
        self.env = env
        self.generator = generator
        self.selector = selector
        self.logger = logger

        # Persistent normative state
        self.normative_state = NormativeState(agent_id=agent_id)

        # Metrics
        self.metrics = RunMetrics()

    def run_episode(self, seed: int, max_steps: int = 50) -> Dict[str, Any]:
        """
        Run one episode with MVRA.

        Args:
            seed: Random seed
            max_steps: Maximum steps

        Returns:
            Episode summary
        """
        # Reset environment
        obs = self.env.reset(seed=seed)

        # Reset state
        self.normative_state = NormativeState(agent_id=self.normative_state.agent_id)
        self.metrics = RunMetrics()

        # Log episode start
        self.logger.log_event("episode_start", {
            "seed": seed,
            "max_steps": max_steps,
            "agent_id": self.normative_state.agent_id
        })

        done = False
        step = 0

        while not done and step < max_steps:
            try:
                # Execute one step
                obs, reward, done, info = self._execute_step(obs, step)
                step += 1

            except ValueError as e:
                # Gridlock or halt
                self.logger.log_event("episode_termination", {
                    "step": step,
                    "reason": str(e)
                })
                break

        # Log run summary
        summary = self.metrics.to_dict()
        self.logger.log_run_summary(summary)

        return summary

    def _execute_step(self, obs: Dict, step: int) -> tuple:
        """
        Execute one MVRA step.

        Returns:
            (next_obs, reward, done, info)
        """
        # Step 1: Observe (feasibility included)
        feasible_actions = obs["feasible_actions"]
        action_inventory = obs["action_inventory"]

        feasible_pre_mask = feasible_actions.copy()

        # Step 2: Generate JAF
        try:
            jaf_artifact = self.generator.generate(
                self.normative_state,
                feasible_actions,
                step
            )
            jaf_schema_valid = True
        except Exception as e:
            # JAF generation failed
            self.logger.log_step({
                "step": step,
                "feasible_actions_pre_mask": feasible_pre_mask,
                "jaf_schema_valid": False,
                "jaf_error": str(e),
                "compile_ok": False,
                "halt": True,
            })
            self.metrics.update_step(
                compile_ok=False,
                is_decorative=False,
                is_nontrivial=False,
                is_gridlock=False,
                is_halt=True
            )
            raise ValueError(f"JAF generation failed: {e}")

        # Step 3: Compile JAF → constraint mask
        constraint = JCOMP010.compile(
            artifact=jaf_artifact,
            action_inventory=action_inventory,
            feasible_actions=set(feasible_actions)
        )

        compile_ok = constraint.compile_ok

        if not compile_ok:
            # Compilation failed - JUSTIFICATION HALT
            self.logger.log_step({
                "step": step,
                "feasible_actions_pre_mask": feasible_pre_mask,
                "jaf_schema_valid": jaf_schema_valid,
                "compile_ok": False,
                "compile_error_code": constraint.error_code,
                "compile_error_detail": constraint.error_detail,
                "halt": True,
            })
            self.metrics.update_step(
                compile_ok=False,
                is_decorative=False,
                is_nontrivial=False,
                is_gridlock=False,
                is_halt=True
            )
            raise ValueError(f"Compilation failed: {constraint.error_code}")

        # Step 4: Apply mask to feasible set
        action_mask = constraint.mask
        forbidden_actions = constraint.forbidden_action_ids
        nontrivial_forbidden = constraint.nontrivial_forbidden_action_ids

        # Compute post-mask feasible set
        feasible_post_mask = [
            action for action in feasible_pre_mask
            if action_mask.get(action, "ALLOW") == "ALLOW"
        ]

        # Check for decorative constraint
        is_decorative = (len(nontrivial_forbidden) == 0 and compile_ok)
        is_nontrivial = len(nontrivial_forbidden) > 0

        # Check for gridlock
        is_gridlock = (len(feasible_pre_mask) > 0 and len(feasible_post_mask) == 0)

        if is_gridlock:
            # NORMATIVE GRIDLOCK
            self.logger.log_step({
                "step": step,
                "feasible_actions_pre_mask": feasible_pre_mask,
                "feasible_actions_pre_mask_count": len(feasible_pre_mask),
                "jaf_schema_valid": jaf_schema_valid,
                "compile_ok": True,
                "forbidden_actions": forbidden_actions,
                "nontrivial_forbidden_count": len(nontrivial_forbidden),
                "decorative_constraint": is_decorative,
                "feasible_actions_post_mask_count": 0,
                "gridlock": True,
            })
            self.metrics.update_step(
                compile_ok=True,
                is_decorative=is_decorative,
                is_nontrivial=is_nontrivial,
                is_gridlock=True,
                is_halt=False
            )
            raise ValueError("Normative gridlock: no feasible actions after masking")

        # Step 5: Select action from masked feasible set
        try:
            selected_action = self.selector.select_action(
                feasible_actions=feasible_pre_mask,
                action_mask=action_mask,
                env_obs=obs
            )
        except Exception as e:
            self.logger.log_step({
                "step": step,
                "selector_error": str(e),
            })
            raise

        # Verify selector did not violate scope
        # (In real implementation, this would be enforced by module boundaries)
        selector_scope_violation = False

        # Step 6: Execute action
        next_obs, reward, done, info = self.env.step(selected_action)

        # Check if action was a violation
        is_violation = info.get("is_temptation", False)
        violated_pref = info.get("violated_pref")

        # Step 7: Log and update state
        self.logger.log_step({
            "step": step,
            "feasible_actions_pre_mask": feasible_pre_mask,
            "feasible_actions_pre_mask_count": len(feasible_pre_mask),
            "jaf_schema_valid": jaf_schema_valid,
            "jaf_artifact_digest": constraint.artifact_digest,
            "compile_ok": True,
            "forbidden_actions": forbidden_actions,
            "nontrivial_forbidden_count": len(nontrivial_forbidden),
            "decorative_constraint": is_decorative,
            "feasible_actions_post_mask_count": len(feasible_post_mask),
            "gridlock": False,
            "selected_action": selected_action,
            "selector_scope_violation": selector_scope_violation,
            "reward": reward,
            "is_violation": is_violation,
            "violated_pref": violated_pref,
            "done": done,
        })

        # Update metrics
        self.metrics.update_step(
            compile_ok=True,
            is_decorative=is_decorative,
            is_nontrivial=is_nontrivial,
            is_gridlock=False,
            is_halt=False,
            reward=reward,
            is_violation=is_violation
        )

        # Update normative state
        self.normative_state.increment_step()
        self.normative_state.add_justification_digest(constraint.artifact_digest)

        return next_obs, reward, done, info
