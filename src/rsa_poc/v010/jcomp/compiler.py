"""JCOMP-0.1 Deterministic Justification Compiler

Implements the normative compiler from jcomp_spec_v0.1.md

Critical properties:
- Deterministic
- Syntactic only
- No inference
- No repair
- No probabilistic behavior
"""

from typing import List, Set, Dict, Any, Optional
import hashlib

# Handle both package and script imports
try:
    from ..jaf.schema import JAF010
except ImportError:
    from jaf.schema import JAF010


class CompileError(Exception):
    """Compilation error with error code"""
    def __init__(self, error_code: str, error_detail: str):
        self.error_code = error_code
        self.error_detail = error_detail[:120]  # Max 120 chars per spec
        super().__init__(f"{error_code}: {self.error_detail}")


class ConstraintObject:
    """
    Compiled constraint object from JCOMP-0.1.

    Either a success or failure object per spec.
    """
    def __init__(
        self,
        constraint_version: str,
        step: int,
        compile_ok: bool,
        artifact_digest: str,
        # Success fields
        forbidden_action_ids: Optional[List[str]] = None,
        mask: Optional[Dict[str, str]] = None,
        nontrivial_forbidden_action_ids: Optional[List[str]] = None,
        reason_code: Optional[str] = None,
        # Failure fields
        error_code: Optional[str] = None,
        error_detail: Optional[str] = None,
    ):
        self.constraint_version = constraint_version
        self.step = step
        self.compile_ok = compile_ok
        self.artifact_digest = artifact_digest

        if compile_ok:
            self.forbidden_action_ids = forbidden_action_ids or []
            self.mask = mask or {}
            self.nontrivial_forbidden_action_ids = nontrivial_forbidden_action_ids or []
            self.reason_code = reason_code
        else:
            self.error_code = error_code
            self.error_detail = error_detail

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        d = {
            "constraint_version": self.constraint_version,
            "step": self.step,
            "compile_ok": self.compile_ok,
            "artifact_digest": self.artifact_digest,
        }

        if self.compile_ok:
            d.update({
                "forbidden_action_ids": self.forbidden_action_ids,
                "mask": self.mask,
                "nontrivial_forbidden_action_ids": self.nontrivial_forbidden_action_ids,
                "reason_code": self.reason_code,
            })
        else:
            d.update({
                "error_code": self.error_code,
                "error_detail": self.error_detail,
            })

        return d


class JCOMP010:
    """
    JCOMP-0.1 - Deterministic Justification Compiler

    Strictly syntactic, non-semantic, deterministic compilation
    of JAF-0.1 artifacts into action masks.
    """

    VERSION = "JCOMP-0.1"

    @staticmethod
    def compute_digest(artifact: JAF010) -> str:
        """
        Compute stable digest of artifact.

        Uses BLAKE2b-128 on canonical JSON per spec.
        """
        canonical = artifact.to_canonical_json()
        h = hashlib.blake2b(canonical.encode('utf-8'), digest_size=16)
        return h.hexdigest()

    @staticmethod
    def compile(
        artifact: JAF010,
        action_inventory: List[str],
        feasible_actions: Set[str],
        policy_scope: str = "V0_1"
    ) -> ConstraintObject:
        """
        Compile JAF-0.1 artifact into constraint object.

        Args:
            artifact: Validated JAF-0.1 artifact
            action_inventory: Complete ordered list of action IDs
            feasible_actions: Set of currently feasible action IDs
            policy_scope: Policy version (default V0_1)

        Returns:
            ConstraintObject (success or failure)
        """
        step = artifact.step
        digest = JCOMP010.compute_digest(artifact)

        try:
            # Step 1: Validate schema
            try:
                artifact.validate()
            except ValueError as e:
                raise CompileError("E_JAF_INVALID", str(e))

            # Step 2: Validate action IDs
            inventory_set = set(action_inventory)
            candidate = artifact.action_claim.candidate_action_id

            if candidate not in inventory_set:
                raise CompileError(
                    "E_ACTION_UNKNOWN",
                    f"candidate_action_id '{candidate}' not in inventory"
                )

            for action_id in artifact.compiler_hints.forbid_action_ids:
                if action_id not in inventory_set:
                    raise CompileError(
                        "E_ACTION_UNKNOWN",
                        f"forbid_action_id '{action_id}' not in inventory"
                    )

            # Step 3: Determine forbidden action set F
            mode = artifact.compiler_hints.forbid_mode

            if mode == "NONE":
                F = set()
            elif mode == "FORBID_CANDIDATE_ONLY":
                F = {candidate}
            elif mode == "EXPLICIT_LIST":
                F = set(artifact.compiler_hints.forbid_action_ids)
            else:
                raise CompileError("E_JAF_INVALID", f"Invalid forbid_mode: {mode}")

            # Violation-driven enforcement rule
            if artifact.action_claim.relation == "VIOLATES":
                if candidate not in F:
                    raise CompileError(
                        "E_VIOLATION_BUT_NOT_FORBIDDEN",
                        f"Claimed VIOLATES but candidate '{candidate}' not in forbid set"
                    )

            # Step 4: Construct mask
            mask = {}
            for action_id in action_inventory:
                mask[action_id] = "FORBID" if action_id in F else "ALLOW"

            # Step 5: Compute non-trivial subset
            F_star = F.intersection(feasible_actions)
            nontrivial_forbidden = sorted(list(F_star))

            # Step 6: Emit success object
            return ConstraintObject(
                constraint_version=JCOMP010.VERSION,
                step=step,
                compile_ok=True,
                artifact_digest=digest,
                forbidden_action_ids=sorted(list(F)),
                mask=mask,
                nontrivial_forbidden_action_ids=nontrivial_forbidden,
                reason_code=artifact.compiler_hints.constraint_reason_code,
            )

        except CompileError as e:
            # Expected compilation failure
            return ConstraintObject(
                constraint_version=JCOMP010.VERSION,
                step=step,
                compile_ok=False,
                artifact_digest=digest,
                error_code=e.error_code,
                error_detail=e.error_detail,
            )
        except Exception as e:
            # Unexpected error - map to E_JAF_INVALID per spec
            return ConstraintObject(
                constraint_version=JCOMP010.VERSION,
                step=step,
                compile_ok=False,
                artifact_digest=digest,
                error_code="E_JAF_INVALID",
                error_detail=f"Unexpected error: {str(e)[:100]}",
            )
