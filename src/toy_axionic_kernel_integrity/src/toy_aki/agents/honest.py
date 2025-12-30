"""
Honest Agent: Kernel-conforming agent.

This agent:
- Always uses proper ACV protocol
- Never calls temptation APIs
- Never requests forbidden actions
- Creates valid proposals with proper traces
"""

from __future__ import annotations

from typing import Any

from toy_aki.agents.base import BaseAgent
from toy_aki.kernel.watchdog import KernelWatchdog, current_time_ms
from toy_aki.env.toyworld import ActionType, PERMITTED_ACTIONS


class HonestAgent(BaseAgent):
    """
    A kernel-conforming honest agent.

    This agent follows all kernel protocols correctly:
    - Creates valid reasoning traces
    - Uses proper commit-anchor-reveal protocol
    - Only requests permitted actions
    - Never attempts to bypass kernel controls
    """

    def __init__(self, agent_id: str | None = None):
        """Initialize honest agent."""
        super().__init__(agent_id or "honest-agent")
        self._goal_seeking = True  # Default behavior: seek goal

    def decide_action(self, observation: dict[str, Any]) -> str:
        """
        Decide next action based on observation.

        Simple goal-seeking policy:
        - Move right toward goal
        - Harvest when at low resources
        - Wait if at goal
        """
        position = observation.get("position", 0)
        goal = observation.get("goal", 9)
        resources = observation.get("resources", 0)
        goal_reached = observation.get("goal_reached", False)

        # Record observation in trace
        self.add_trace_node(
            node_type="observation",
            content={
                "position": position,
                "goal": goal,
                "resources": resources,
                "goal_reached": goal_reached,
            },
        )

        # Decide action
        if goal_reached:
            action = "WAIT"
            reasoning = "Goal reached, waiting"
        elif position < goal:
            action = "MOVE_RIGHT"
            reasoning = f"Moving toward goal (position {position} < goal {goal})"
        else:
            action = "HARVEST"
            reasoning = "At goal position, harvesting resources"

        # Record decision in trace
        self.add_trace_node(
            node_type="reasoning",
            content={
                "reasoning": reasoning,
                "chosen_action": action,
            },
        )

        return action

    def act(self, kernel: KernelWatchdog) -> dict[str, Any] | None:
        """
        Execute one complete action cycle.

        This follows the proper ACV protocol:
        1. Get observation
        2. Decide action
        3. Build proposal
        4. Create commitment
        5. Submit commitment, receive anchor
        6. Submit proposal with nonce reveal
        7. If accepted, execute actuation

        Args:
            kernel: The kernel watchdog

        Returns:
            Actuation result or None if rejected
        """
        # Clear trace for new action
        self.clear_trace()

        # Get observation
        observation = kernel.env.get_observation()

        # Decide action
        action = self.decide_action(observation)

        # Build request
        request = self.build_request(action=action)

        # Record action intent in trace
        self.add_trace_node(
            node_type="action",
            content={
                "action": action,
                "request_id": request["request_id"],
            },
        )

        # Build proposal
        proposal = self.build_proposal(
            request=request,
            policy_digest=kernel.policy_digest,
            env_digest=kernel.env_digest,
        )

        # Create commitment
        commitment = self.create_commitment(
            proposal=proposal,
            kernel_public_key=kernel.kernel_public_key,
        )

        # Submit commitment, receive anchor
        anchor = kernel.receive_commitment(commitment, self.agent_id)

        # Submit proposal (reveal phase)
        decision = kernel.receive_proposal(
            proposal=proposal,
            revealed_nonce=commitment.nonce,
            agent_id=self.agent_id,
        )

        # If accepted, execute actuation
        if decision.accepted and decision.certificate:
            result = kernel.execute_actuation(
                certificate=decision.certificate,
                proposal=proposal,
            )
            return result

        return None


class GoalSeekingAgent(HonestAgent):
    """
    An honest agent that specifically seeks the goal.

    More sophisticated goal-seeking behavior with harvesting.
    """

    def __init__(self, agent_id: str | None = None):
        """Initialize goal-seeking agent."""
        super().__init__(agent_id or "goal-seeker")
        self._harvest_threshold = 200  # Harvest when below this

    def decide_action(self, observation: dict[str, Any]) -> str:
        """
        Decide action with resource-aware goal seeking.
        """
        position = observation.get("position", 0)
        goal = observation.get("goal", 9)
        resources = observation.get("resources", 0)
        goal_reached = observation.get("goal_reached", False)

        # Record observation
        self.add_trace_node(
            node_type="observation",
            content=observation,
        )

        # Decision logic
        if goal_reached:
            action = "WAIT"
            reasoning = "Goal reached"
        elif resources < self._harvest_threshold and position > 0:
            action = "HARVEST"
            reasoning = f"Resources low ({resources}), harvesting"
        elif position < goal:
            action = "MOVE_RIGHT"
            reasoning = f"Moving toward goal"
        else:
            action = "WAIT"
            reasoning = "At boundary, waiting"

        # Record decision
        self.add_trace_node(
            node_type="reasoning",
            content={"reasoning": reasoning, "action": action},
        )

        return action


class DelegatingAgent(HonestAgent):
    """
    An honest agent that can delegate actions.

    Demonstrates proper delegation within allowed depth.
    """

    def __init__(
        self,
        agent_id: str | None = None,
        delegatee: BaseAgent | None = None,
    ):
        """Initialize delegating agent."""
        super().__init__(agent_id or "delegator")
        self._delegatee = delegatee
        self._delegation_probability = 0.3  # 30% chance to delegate

    def set_delegatee(self, delegatee: BaseAgent) -> None:
        """Set the agent to delegate to."""
        self._delegatee = delegatee

    def decide_action(self, observation: dict[str, Any]) -> str:
        """
        Decide action, potentially delegating.
        """
        import random

        # Record observation
        self.add_trace_node(
            node_type="observation",
            content=observation,
        )

        # Check if we should delegate
        if self._delegatee and random.random() < self._delegation_probability:
            action = "DELEGATE"
            reasoning = f"Delegating to {self._delegatee.agent_id}"
        else:
            # Normal goal-seeking
            position = observation.get("position", 0)
            goal = observation.get("goal", 9)

            if observation.get("goal_reached"):
                action = "WAIT"
                reasoning = "Goal reached"
            elif position < goal:
                action = "MOVE_RIGHT"
                reasoning = "Moving toward goal"
            else:
                action = "HARVEST"
                reasoning = "Harvesting"

        self.add_trace_node(
            node_type="reasoning",
            content={"reasoning": reasoning, "action": action},
        )

        return action

    def act(self, kernel: KernelWatchdog) -> dict[str, Any] | None:
        """
        Execute action, handling delegation.
        """
        self.clear_trace()

        observation = kernel.env.get_observation()
        action = self.decide_action(observation)

        if action == "DELEGATE" and self._delegatee:
            # Build delegation request
            request = self.build_request(
                action="DELEGATE",
                args={"delegatee": self._delegatee.agent_id},
            )

            self.add_trace_node(
                node_type="action",
                content={
                    "action": "DELEGATE",
                    "delegatee": self._delegatee.agent_id,
                },
            )

            # Build proposal with delegation
            proposal = self.build_proposal(
                request=request,
                policy_digest=kernel.policy_digest,
                env_digest=kernel.env_digest,
            )

            # Add delegation chain
            proposal["delegation_chain"] = [{
                "delegator_id": self.agent_id,
                "delegatee_id": self._delegatee.agent_id,
                "original_proposal_hash": proposal["proposal_hash"],
                "depth": 1,
            }]

            # Re-compute proposal hash with chain
            from toy_aki.common.hashing import compute_proposal_hash
            proposal["proposal_hash"] = compute_proposal_hash(proposal)

            # Normal ACV flow
            commitment = self.create_commitment(
                proposal=proposal,
                kernel_public_key=kernel.kernel_public_key,
            )

            anchor = kernel.receive_commitment(commitment, self.agent_id)

            decision = kernel.receive_proposal(
                proposal=proposal,
                revealed_nonce=commitment.nonce,
                agent_id=self.agent_id,
            )

            if decision.accepted and decision.certificate:
                return kernel.execute_actuation(
                    certificate=decision.certificate,
                    proposal=proposal,
                )
            return None
        else:
            # Normal action
            return super().act(kernel)
