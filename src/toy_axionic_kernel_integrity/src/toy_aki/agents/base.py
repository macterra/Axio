"""
Agent Base: Common agent interface and utilities.

All agents (honest and pseudo) inherit from this base.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from toy_aki.common.hashing import hash_json, compute_trace_commit
from toy_aki.acv import Commitment, Anchor, create_commitment, generate_nonce
from toy_aki.kernel.watchdog import KernelWatchdog, current_time_ms


@dataclass
class TraceNode:
    """A node in an agent's reasoning trace."""
    node_id: str
    node_type: str  # "observation", "reasoning", "decision", "action"
    content: dict[str, Any]
    prev_hash: str = ""
    node_hash: str = ""

    def __post_init__(self):
        if not self.node_hash:
            self.node_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute hash of this node."""
        hashable = {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "content": self.content,
            "prev_hash": self.prev_hash,
        }
        return hash_json(hashable)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "node_hash": self.node_hash,
            "prev_hash": self.prev_hash,
            "content": self.content,
        }


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Provides common functionality for:
    - Trace building
    - Proposal creation
    - Commitment generation
    """

    def __init__(self, agent_id: str | None = None):
        """Initialize agent with optional ID."""
        self.agent_id = agent_id or f"agent-{uuid.uuid4()}"
        self._trace_nodes: list[TraceNode] = []
        self._prev_hash = "0" * 64  # Genesis previous hash

    @property
    def trace_nodes(self) -> list[TraceNode]:
        """Get current trace nodes."""
        return list(self._trace_nodes)

    def add_trace_node(
        self,
        node_type: str,
        content: dict[str, Any],
    ) -> TraceNode:
        """
        Add a node to the agent's trace.

        Args:
            node_type: Type of node
            content: Node content

        Returns:
            The created node
        """
        node = TraceNode(
            node_id=f"node-{uuid.uuid4()}",
            node_type=node_type,
            content=content,
            prev_hash=self._prev_hash,
        )
        self._trace_nodes.append(node)
        self._prev_hash = node.node_hash
        return node

    def build_trace(self) -> dict[str, Any]:
        """
        Build a trace object from current nodes.

        Returns:
            Trace dictionary with nodes and commit
        """
        nodes = [n.to_dict() for n in self._trace_nodes]
        node_hashes = [n.node_hash for n in self._trace_nodes]
        # compute_trace_commit expects the trace dict (without trace_commit field)
        # We build the trace without trace_commit first, then compute it
        trace_without_commit = {
            "trace_version": "0.1",
            "nodes": nodes,
        }
        trace_commit = compute_trace_commit(trace_without_commit)

        return {
            "trace_version": "0.1",
            "nodes": nodes,
            "trace_commit": trace_commit,
        }

    def build_request(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        requested_class: str = "STANDARD",
    ) -> dict[str, Any]:
        """
        Build an actuation request.

        Args:
            action: Action type name
            args: Action arguments
            requested_class: Action class

        Returns:
            Request dictionary
        """
        return {
            "request_id": str(uuid.uuid4()),
            "intent": {
                "action": action,
                "args": args or {},
            },
            "requested_class": requested_class,
            "timestamp_ms": current_time_ms(),
        }

    def build_proposal(
        self,
        request: dict[str, Any],
        policy_digest: str,
        env_digest: str,
        interface_spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build a complete proposal.

        Args:
            request: The actuation request
            policy_digest: Current policy digest
            env_digest: Current environment digest
            interface_spec: Interface specification

        Returns:
            Complete proposal dictionary
        """
        if interface_spec is None:
            interface_spec = {
                "mode": "aki_v0",
                "coupling": "A",
            }

        trace = self.build_trace()
        timestamp_ms = current_time_ms()

        # Build proposal without hash first
        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": interface_spec,
            "request": request,
            "trace": trace,
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": timestamp_ms,
        }

        # Add proposal hash
        from toy_aki.common.hashing import compute_proposal_hash
        proposal["proposal_hash"] = compute_proposal_hash(proposal)

        return proposal

    def create_commitment(
        self,
        proposal: dict[str, Any],
        kernel_public_key: str,
    ) -> Commitment:
        """
        Create a commitment for a proposal.

        Args:
            proposal: The proposal to commit to
            kernel_public_key: Kernel's public key

        Returns:
            Commitment object
        """
        return create_commitment(
            proposal=proposal,
            kernel_public_key=kernel_public_key,
            timestamp_ms=current_time_ms(),
        )

    def clear_trace(self) -> None:
        """Clear the current trace."""
        self._trace_nodes = []
        self._prev_hash = "0" * 64

    @abstractmethod
    def decide_action(self, observation: dict[str, Any]) -> str:
        """
        Decide what action to take based on observation.

        Args:
            observation: Current environment observation

        Returns:
            Action name to take
        """
        pass

    @abstractmethod
    def act(self, kernel: KernelWatchdog) -> dict[str, Any] | None:
        """
        Execute one step of agent behavior.

        Args:
            kernel: The kernel watchdog

        Returns:
            Result of the action, or None
        """
        pass
