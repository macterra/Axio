"""JCOMP-1.0 Compiler

Compiles JAF-1.0 artifacts with truth grounding and anti-oscillation rules.

Rules:
1. Authorization Consistency: AV/RP must be truthful w.r.t. APCM
2. Conflict Truthfulness: conflict_attribution must match APCM collisions
3. Anti-Oscillation: Precedent violation detection
1.5. Necessity Clause: Prevent gratuitous violations when alternatives exist
"""

from typing import Dict, Set, Tuple, Optional, List
from dataclasses import dataclass
import hashlib
import json


# Import JAF-1.0 schema
try:
    from ..jaf.schema import JAF100, ConflictResolution
except ImportError:
    from src.rsa_poc.v100.jaf.schema import JAF100, ConflictResolution


@dataclass
class CompilerError:
    """Structured compilation error"""
    code: str
    message: str
    details: Dict


class CompilationResult:
    """Result of compilation attempt"""
    def __init__(self, success: bool, action_mask: Optional[Set[str]] = None,
                 errors: Optional[List[CompilerError]] = None,
                 digest: Optional[str] = None):
        self.success = success
        self.action_mask = action_mask or set()  # Actions to FORBID
        self.errors = errors or []
        self.digest = digest  # Artifact digest if successful

    def __repr__(self) -> str:
        if self.success:
            return f"CompilationResult(success=True, forbid_count={len(self.action_mask)})"
        else:
            return f"CompilationResult(success=False, errors={[e.code for e in self.errors]})"


class JCOMP100:
    """
    v1.0 compiler with APCM truth grounding and anti-oscillation.

    Deterministic, syntactic, non-probabilistic.
    """

    # Error codes
    E_FALSE_COLLISION = "E_FALSE_COLLISION"
    E_PRECEDENT_VIOLATION = "E_PRECEDENT_VIOLATION"
    E_AV_WITHOUT_COLLISION = "E_AV_WITHOUT_COLLISION"
    E_GRATUITOUS_VIOLATION = "E_GRATUITOUS_VIOLATION"
    E_INVALID_ACTION = "E_INVALID_ACTION"
    E_INVALID_PREFERENCE = "E_INVALID_PREFERENCE"
    E_MALFORMED_JAF = "E_MALFORMED_JAF"

    def __init__(self, valid_actions: Set[str], valid_preferences: Set[str]):
        """
        Initialize compiler with environment vocabulary.

        Args:
            valid_actions: Set of all valid action IDs from environment
            valid_preferences: Set of all valid preference IDs from environment
        """
        self.valid_actions = valid_actions
        self.valid_preferences = valid_preferences

    def compile(
        self,
        jaf: JAF100,
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: Set[str],
        precedent: Optional[Dict[str, any]] = None
    ) -> CompilationResult:
        """
        Compile JAF-1.0 artifact with full v1.0 rule enforcement.

        Args:
            jaf: JAF-1.0 artifact to compile
            apcm: Action-Preference Consequence Map (ground truth)
            feasible_actions: Currently feasible actions from environment
            precedent: Previous artifact structured fields (if exists):
                {
                    "authorized_violations": Set[str],
                    "required_preservations": Set[str],
                    "conflict_attribution": Set[Tuple[str, str]],
                    "digest": str
                }

        Returns:
            CompilationResult with success flag, action mask, and errors
        """
        errors = []

        # === Pre-validation ===
        if not self._validate_vocabulary(jaf, errors):
            return CompilationResult(success=False, errors=errors)

        # === Rule 2: Conflict Truthfulness ===
        if not self._check_conflict_truthfulness(jaf, apcm, feasible_actions, errors):
            pass  # Errors already appended

        # === Rule 1: Authorization Consistency ===
        if not self._check_authorization_consistency(jaf, apcm, feasible_actions, errors):
            pass  # Errors already appended

        # === Rule 3: Anti-Oscillation ===
        if precedent and not self._check_anti_oscillation(jaf, precedent, errors):
            pass  # Errors already appended

        # === Rule 1.5: Necessity Clause ===
        if not self._check_necessity_clause(jaf, apcm, feasible_actions, errors):
            pass  # Errors already appended

        # If any errors, compilation fails
        if errors:
            return CompilationResult(success=False, errors=errors)

        # === Success: Generate action mask ===
        action_mask = self._generate_action_mask(jaf, apcm, feasible_actions)
        digest = self._compute_digest(jaf)

        return CompilationResult(
            success=True,
            action_mask=action_mask,
            digest=digest
        )

    def _validate_vocabulary(self, jaf: JAF100, errors: List[CompilerError]) -> bool:
        """
        Validate that JAF uses only valid action and preference IDs.

        Returns True if valid, False otherwise (errors appended).
        """
        valid = True

        # Check action claim
        if jaf.action_claim.candidate_action_id not in self.valid_actions:
            errors.append(CompilerError(
                code=self.E_INVALID_ACTION,
                message=f"Invalid action ID in action_claim: {jaf.action_claim.candidate_action_id}",
                details={"action_id": jaf.action_claim.candidate_action_id}
            ))
            valid = False

        # Check forbid_action_ids in compiler_hints
        for action_id in jaf.compiler_hints.forbid_action_ids:
            if action_id not in self.valid_actions:
                errors.append(CompilerError(
                    code=self.E_INVALID_ACTION,
                    message=f"Invalid action ID in forbid_action_ids: {action_id}",
                    details={"action_id": action_id}
                ))
                valid = False

        # Check authorized_violations
        for pref_id in jaf.authorized_violations:
            if pref_id not in self.valid_preferences:
                errors.append(CompilerError(
                    code=self.E_INVALID_PREFERENCE,
                    message=f"Invalid preference ID in authorized_violations: {pref_id}",
                    details={"preference_id": pref_id}
                ))
                valid = False

        # Check required_preservations
        for pref_id in jaf.required_preservations:
            if pref_id not in self.valid_preferences:
                errors.append(CompilerError(
                    code=self.E_INVALID_PREFERENCE,
                    message=f"Invalid preference ID in required_preservations: {pref_id}",
                    details={"preference_id": pref_id}
                ))
                valid = False

        # Check conflict_attribution pairs
        for p1, p2 in jaf.conflict_attribution:
            if p1 not in self.valid_preferences:
                errors.append(CompilerError(
                    code=self.E_INVALID_PREFERENCE,
                    message=f"Invalid preference ID in conflict_attribution: {p1}",
                    details={"preference_id": p1}
                ))
                valid = False
            if p2 not in self.valid_preferences:
                errors.append(CompilerError(
                    code=self.E_INVALID_PREFERENCE,
                    message=f"Invalid preference ID in conflict_attribution: {p2}",
                    details={"preference_id": p2}
                ))
                valid = False

        return valid

    def _check_conflict_truthfulness(
        self,
        jaf: JAF100,
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: Set[str],
        errors: List[CompilerError]
    ) -> bool:
        """
        Rule 2: conflict_attribution must be truthful w.r.t. APCM.

        A pair (P1, P2) is a genuine collision iff:
        - For all feasible actions, at least one of P1 or P2 is violated
        """
        valid = True

        # Check each attributed collision
        for p1, p2 in jaf.conflict_attribution:
            is_genuine_collision = self._is_genuine_collision(p1, p2, apcm, feasible_actions)

            if not is_genuine_collision:
                errors.append(CompilerError(
                    code=self.E_FALSE_COLLISION,
                    message=f"False collision attributed: ({p1}, {p2})",
                    details={
                        "collision_pair": (p1, p2),
                        "reason": "Not all feasible actions violate at least one of these preferences"
                    }
                ))
                valid = False

        return valid

    def _is_genuine_collision(
        self,
        p1: str,
        p2: str,
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: Set[str]
    ) -> bool:
        """
        Check if (p1, p2) form a genuine collision in APCM.

        Returns True iff for all feasible actions, at least one is violated.
        """
        for action in feasible_actions:
            if action not in apcm:
                continue  # Skip if not in APCM (shouldn't happen with valid feasible set)

            violates = apcm[action]["violates"]

            # If neither p1 nor p2 is violated, it's NOT a collision
            if p1 not in violates and p2 not in violates:
                return False

        return True  # All feasible actions violate at least one

    def _check_authorization_consistency(
        self,
        jaf: JAF100,
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: Set[str],
        errors: List[CompilerError]
    ) -> bool:
        """
        Rule 1: authorized_violations must be truthful.

        AV can only be non-empty if there exists a genuine collision.
        Each preference in AV must be part of at least one collision pair.
        """
        valid = True

        if not jaf.authorized_violations:
            return True  # Empty AV is always valid

        # If AV is non-empty, there must be at least one collision
        if not jaf.conflict_attribution:
            errors.append(CompilerError(
                code=self.E_AV_WITHOUT_COLLISION,
                message="Authorized violations declared without any collision",
                details={
                    "authorized_violations": list(jaf.authorized_violations),
                    "conflict_attribution": []
                }
            ))
            return False

        # Each AV preference must appear in at least one collision pair
        collision_prefs = set()
        for p1, p2 in jaf.conflict_attribution:
            collision_prefs.add(p1)
            collision_prefs.add(p2)

        for av_pref in jaf.authorized_violations:
            if av_pref not in collision_prefs:
                errors.append(CompilerError(
                    code=self.E_AV_WITHOUT_COLLISION,
                    message=f"Authorized violation {av_pref} not in any collision",
                    details={
                        "preference": av_pref,
                        "colliding_preferences": list(collision_prefs)
                    }
                ))
                valid = False

        return valid

    def _check_anti_oscillation(
        self,
        jaf: JAF100,
        precedent: Dict[str, any],
        errors: List[CompilerError]
    ) -> bool:
        """
        Rule 3: Anti-Oscillation.

        If mode=REVISE:
        - authorized_violations must differ from precedent
        - OR required_preservations must differ from precedent

        If mode=MAINTAIN:
        - No checks (agent maintaining prior resolution)
        """
        valid = True

        if not jaf.conflict_resolution:
            return True  # No resolution declared

        if jaf.conflict_resolution.mode == "MAINTAIN":
            return True  # MAINTAIN mode exempts from oscillation check

        # REVISE mode: must show actual revision
        if jaf.conflict_resolution.mode == "REVISE":
            prev_av = precedent.get("authorized_violations", set())
            prev_rp = precedent.get("required_preservations", set())

            av_changed = (jaf.authorized_violations != prev_av)
            rp_changed = (jaf.required_preservations != prev_rp)

            if not (av_changed or rp_changed):
                errors.append(CompilerError(
                    code=self.E_PRECEDENT_VIOLATION,
                    message="REVISE mode declared but no actual revision detected",
                    details={
                        "current_av": list(jaf.authorized_violations),
                        "precedent_av": list(prev_av),
                        "current_rp": list(jaf.required_preservations),
                        "precedent_rp": list(prev_rp)
                    }
                ))
                valid = False

        return valid

    def _check_necessity_clause(
        self,
        jaf: JAF100,
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: Set[str],
        errors: List[CompilerError]
    ) -> bool:
        """
        Rule 1.5: Necessity Clause.

        If the claimed action violates any preference P:
        - There must NOT exist an alternative feasible action that:
          a) Does not violate P
          b) Is not already forbidden by JAF

        This prevents gratuitous violations.
        """
        valid = True

        claimed_action = jaf.action_claim.candidate_action_id

        claimed_violations = apcm[claimed_action]["violates"]
        forbidden_actions = jaf.compiler_hints.forbid_action_ids

        # For each preference violated by claimed action
        for pref in claimed_violations:
            # Check if there's a non-gratuitous alternative
            has_alternative = False
            alternatives = []

            for alt_action in feasible_actions:
                if alt_action == claimed_action:
                    continue  # Skip the claimed action itself
                if alt_action in forbidden_actions:
                    continue  # Skip forbidden alternatives
                if alt_action not in apcm:
                    continue

                alt_violations = apcm[alt_action]["violates"]

                # If alternative doesn't violate this preference, it's a valid alternative
                if pref not in alt_violations:
                    has_alternative = True
                    alternatives.append(alt_action)

            # If alternatives exist and preference is NOT authorized, violation is gratuitous
            if has_alternative and pref not in jaf.authorized_violations:
                errors.append(CompilerError(
                    code=self.E_GRATUITOUS_VIOLATION,
                    message=f"Gratuitous violation of {pref} - alternatives exist",
                    details={
                        "violated_preference": pref,
                        "claimed_action": claimed_action,
                        "alternatives": alternatives,
                        "authorized_violations": list(jaf.authorized_violations)
                    }
                ))
                valid = False

        return valid

    def _generate_action_mask(
        self,
        jaf: JAF100,
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: Set[str]
    ) -> Set[str]:
        """
        Generate action mask (set of actions to FORBID).

        Blacklist semantics:
        1. Explicitly forbidden actions from forbid_action_ids
        2. Actions violating required_preservations
        3. Actions violating any preference NOT in authorized_violations
        """
        forbid = set()

        # Explicit forbids
        forbid.update(jaf.compiler_hints.forbid_action_ids)

        # Scan all feasible actions
        for action in feasible_actions:
            if action not in apcm:
                continue

            violated_prefs = apcm[action]["violates"]

            # Forbid if violates required preservation
            if violated_prefs & jaf.required_preservations:
                forbid.add(action)
                continue

            # Forbid if violates any non-authorized preference
            unauthorized_violations = violated_prefs - jaf.authorized_violations
            if unauthorized_violations:
                forbid.add(action)

        return forbid

    def _compute_digest(self, jaf: JAF100) -> str:
        """
        Compute canonical digest of JAF artifact.

        Uses BLAKE2b-128 (same as v010 for consistency).
        """
        canonical_json = jaf.to_canonical_json()
        digest = hashlib.blake2b(canonical_json.encode("utf-8"), digest_size=16).hexdigest()
        return digest
