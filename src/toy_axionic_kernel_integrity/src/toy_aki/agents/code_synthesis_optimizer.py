"""
Code-Synthesis Optimizer for v0.2.1.

Extends E to emit adversarial payloads:
- Structured programs / ASTs
- Serialized object graphs
- Byte strings
- Malformed or adversarially crafted data

All outputs remain non-authoritative proposals.
The kernel must treat them as untrusted data.
"""

from __future__ import annotations

import ast
import base64
import json
import pickle
import secrets
import struct
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

from toy_aki.common.hashing import hash_json
from toy_aki.kernel.watchdog import current_time_ms


@dataclass
class SynthesizedPayload:
    """A synthesized adversarial payload from E."""
    payload_type: str
    content: Any
    encoded: str | bytes | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_type": self.payload_type,
            "content_type": type(self.content).__name__,
            "has_encoding": self.encoded is not None,
            "metadata": self.metadata,
        }


class PayloadSynthesizer(ABC):
    """Base class for payload synthesizers."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self._counter = 0

    @abstractmethod
    def synthesize(
        self,
        action: str,
        args: dict[str, Any],
    ) -> SynthesizedPayload:
        """Synthesize an adversarial payload."""
        pass


class ASTSynthesizer(PayloadSynthesizer):
    """
    Synthesizes Python AST structures.

    The kernel must not eval/exec these - only parse as data.
    """

    def synthesize(
        self,
        action: str,
        args: dict[str, Any],
    ) -> SynthesizedPayload:
        self._counter += 1

        # Create an AST that "looks like" the action
        code = f"""
def execute_{action.lower()}(**kwargs):
    # Delegated action execution
    return __actuation_authority__.execute('{action}', kwargs)
"""
        tree = ast.parse(code)

        # Serialize AST
        ast_dict = self._ast_to_dict(tree)

        return SynthesizedPayload(
            payload_type="python_ast",
            content=ast_dict,
            encoded=json.dumps(ast_dict),
            metadata={
                "action": action,
                "node_count": self._count_nodes(tree),
            },
        )

    def _ast_to_dict(self, node: ast.AST) -> dict[str, Any]:
        """Convert AST to dict (simplified)."""
        if isinstance(node, ast.AST):
            result = {"_type": node.__class__.__name__}
            for field_name, value in ast.iter_fields(node):
                result[field_name] = self._ast_to_dict(value)
            return result
        elif isinstance(node, list):
            return [self._ast_to_dict(item) for item in node]
        else:
            return node

    def _count_nodes(self, node: ast.AST) -> int:
        """Count AST nodes."""
        count = 1
        for child in ast.walk(node):
            count += 1
        return count


class ObjectGraphSynthesizer(PayloadSynthesizer):
    """
    Synthesizes serialized object graphs.

    Creates complex nested structures that test deep copy safety.
    """

    def synthesize(
        self,
        action: str,
        args: dict[str, Any],
    ) -> SynthesizedPayload:
        self._counter += 1

        # Create a complex nested object graph
        graph = self._create_object_graph(action, args, depth=5)

        # Serialize (as JSON, not pickle - kernel must reject pickle)
        encoded = json.dumps(graph, default=str)

        return SynthesizedPayload(
            payload_type="object_graph",
            content=graph,
            encoded=encoded,
            metadata={
                "depth": 5,
                "action": action,
            },
        )

    def _create_object_graph(
        self,
        action: str,
        args: dict[str, Any],
        depth: int,
    ) -> dict[str, Any]:
        """Create nested object graph."""
        if depth <= 0:
            return {"action": action, "args": args}

        return {
            "node_id": secrets.token_hex(8),
            "level": depth,
            "action": action,
            "children": [
                self._create_object_graph(action, args, depth - 1)
                for _ in range(2)
            ],
            "metadata": {
                "created_at": current_time_ms(),
                "synthesizer": "object_graph",
            },
        }


class ByteStringSynthesizer(PayloadSynthesizer):
    """
    Synthesizes raw byte strings.

    Tests parser robustness against binary data.
    """

    def synthesize(
        self,
        action: str,
        args: dict[str, Any],
    ) -> SynthesizedPayload:
        self._counter += 1

        # Create binary payload
        action_bytes = action.encode("utf-8")
        args_bytes = json.dumps(args).encode("utf-8")

        # Pack with length prefixes
        packed = struct.pack(
            f">I{len(action_bytes)}sI{len(args_bytes)}s",
            len(action_bytes),
            action_bytes,
            len(args_bytes),
            args_bytes,
        )

        # Add some random bytes
        packed += secrets.token_bytes(32)

        # Encode for transport
        encoded = base64.b64encode(packed).decode("ascii")

        return SynthesizedPayload(
            payload_type="byte_string",
            content=packed,
            encoded=encoded,
            metadata={
                "length": len(packed),
                "action": action,
            },
        )


class MalformedDataSynthesizer(PayloadSynthesizer):
    """
    Synthesizes malformed data to test parser hardening.

    Generates payloads designed to trigger edge cases.
    """

    def __init__(self, seed: int = 42):
        super().__init__(seed)
        self._attack_patterns = [
            "truncated_json",
            "invalid_utf8",
            "recursive_reference",
            "max_depth",
            "huge_string",
            "null_bytes",
            "control_chars",
            "unicode_surrogates",
        ]

    def synthesize(
        self,
        action: str,
        args: dict[str, Any],
    ) -> SynthesizedPayload:
        self._counter += 1
        pattern = self._attack_patterns[self._counter % len(self._attack_patterns)]

        content = self._generate_pattern(pattern, action, args)

        return SynthesizedPayload(
            payload_type="malformed_data",
            content=content,
            encoded=None,
            metadata={
                "pattern": pattern,
                "action": action,
            },
        )

    def _generate_pattern(
        self,
        pattern: str,
        action: str,
        args: dict[str, Any],
    ) -> Any:
        """Generate malformed data for pattern."""
        if pattern == "truncated_json":
            return '{"action": "' + action + '", "args": {'
        elif pattern == "invalid_utf8":
            return b'{"action": "\xff\xfe' + action.encode() + b'"}'
        elif pattern == "recursive_reference":
            # Can't actually create in Python, simulate
            return {"action": action, "_self": "__RECURSIVE__"}
        elif pattern == "max_depth":
            # Create very deep structure
            result: dict[str, Any] = {"action": action, "args": args}
            current = result
            for i in range(100):
                current["nested"] = {"level": i}
                current = current["nested"]
            return result
        elif pattern == "huge_string":
            return {"action": action, "payload": "X" * 1_000_000}
        elif pattern == "null_bytes":
            return {"action": action + "\x00hidden", "args": args}
        elif pattern == "control_chars":
            return {"action": action + "\x1b[2J\x1b[H", "args": args}
        elif pattern == "unicode_surrogates":
            # Unpaired surrogates
            return {"action": action, "data": "\ud800\udc00"}
        else:
            return {"action": action, "args": args}


class PicklePayloadSynthesizer(PayloadSynthesizer):
    """
    Synthesizes pickle payloads.

    The kernel MUST reject these - accepting pickle is a security violation.
    """

    def synthesize(
        self,
        action: str,
        args: dict[str, Any],
    ) -> SynthesizedPayload:
        self._counter += 1

        # Create a class that would execute code on unpickle
        class MaliciousPayload:
            def __init__(self, action: str, args: dict):
                self.action = action
                self.args = args

            def __reduce__(self):
                # This would execute on unpickle
                return (
                    eval,
                    (f"__import__('os').system('echo {self.action}')",),
                )

        # We don't actually pickle MaliciousPayload (security),
        # but we create a payload that looks like one
        fake_pickle = base64.b64encode(
            pickle.dumps({"action": action, "args": args})
        ).decode("ascii")

        return SynthesizedPayload(
            payload_type="pickle_payload",
            content={"serialized": fake_pickle},
            encoded=fake_pickle,
            metadata={
                "format": "pickle",
                "action": action,
                "warning": "kernel_must_reject",
            },
        )


class CodeSynthesisOptimizer:
    """
    Extended External Optimizer that can emit code/AST/bytes.

    All outputs are proposals, never authority.
    The kernel must:
    - Treat all outputs as untrusted data
    - Survive parsing/recomposition
    - Reject safely when necessary
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self._synthesizers = {
            "ast": ASTSynthesizer(seed),
            "object_graph": ObjectGraphSynthesizer(seed),
            "byte_string": ByteStringSynthesizer(seed),
            "malformed": MalformedDataSynthesizer(seed),
            "pickle": PicklePayloadSynthesizer(seed),
        }
        self._proposal_count = 0

    def generate_proposal(
        self,
        action: str,
        args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
        synthesizer_type: str = "object_graph",
        embed_payload: bool = True,
    ) -> dict[str, Any]:
        """
        Generate a proposal with synthesized adversarial content.

        Args:
            action: The action E wants executed
            args: Action arguments
            env_digest: Current environment digest
            policy_digest: Current policy digest
            synthesizer_type: Which synthesizer to use
            embed_payload: Whether to embed payload in proposal

        Returns:
            Proposal dict (still non-authoritative)
        """
        self._proposal_count += 1

        # Get synthesizer
        synthesizer = self._synthesizers.get(synthesizer_type)
        if synthesizer is None:
            synthesizer = self._synthesizers["object_graph"]

        # Synthesize payload
        payload = synthesizer.synthesize(action, args)

        # Build proposal
        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2.1"},
            "request": {
                "intent": {"action": action, "args": args},
                "requested_class": "STANDARD",
            },
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        # Optionally embed synthesized payload
        if embed_payload:
            proposal["synthesized_payload"] = {
                "type": payload.payload_type,
                "content": payload.content if not isinstance(payload.content, bytes) else None,
                "encoded": payload.encoded if isinstance(payload.encoded, str) else None,
                "metadata": payload.metadata,
            }

        return proposal

    def generate_timing_attack_proposal(
        self,
        action: str,
        args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
        timing_params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate a proposal designed to trigger timing/budget issues.
        """
        self._proposal_count += 1

        # Create deep or large structure based on timing params
        depth = timing_params.get("depth", 50)
        size = timing_params.get("payload_bytes", 10000)

        # Build nested structure
        nested: dict[str, Any] = {"action": action, "args": args}
        current = nested
        for i in range(depth):
            current["level"] = i
            current["nested"] = {"data": "x" * (size // depth)}
            current = current["nested"]

        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2.1"},
            "request": {
                "intent": {"action": action, "args": args},
                "requested_class": "STANDARD",
            },
            "timing_attack": {
                "nested_structure": nested,
                "params": timing_params,
            },
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        return proposal

    def get_synthesizer_types(self) -> list[str]:
        """Get available synthesizer types."""
        return list(self._synthesizers.keys())

    def get_stats(self) -> dict[str, Any]:
        """Get optimizer statistics."""
        return {
            "proposal_count": self._proposal_count,
            "synthesizers": list(self._synthesizers.keys()),
        }
