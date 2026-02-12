"""
X-0P Generator Common Utilities

Shared infrastructure for all condition generators:
- Observation construction
- CandidateBundle construction
- Token counting (whitespace word count per BA4)
- Seed management
- Corpus loading
- Constitution clause ID enumeration
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from kernel.src.artifacts import (
    ActionRequest,
    ActionType,
    Author,
    CandidateBundle,
    Justification,
    Observation,
    ObservationKind,
    ScopeClaim,
    canonical_json,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# All resolvable authority IDs in constitution v0.1.1
CONSTITUTION_CLAUSE_IDS: List[str] = [
    "INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
    "INV-AUTHORITY-CITED",
    "INV-NON-PRIVILEGED-REFLECTION",
    "INV-REPLAY-DETERMINISM",
]

CITATION_PREFIX = "constitution:v0.1.1#"

# Valid action types per closed action space
VALID_ACTION_TYPES: List[str] = [
    ActionType.NOTIFY.value,
    ActionType.READ_LOCAL.value,
    ActionType.WRITE_LOCAL.value,
]

# IO allowlist paths
READ_PATHS = ["./artifacts/", "./workspace/"]
WRITE_PATHS = ["./workspace/", "./logs/"]

# Default budget (generous for profiling)
DEFAULT_BUDGET = {
    "llm_output_token_count": 100,
    "llm_candidates_reported": 1,
    "llm_parse_errors": 0,
}

# Default cycle timestamp
DEFAULT_TIMESTAMP = "2026-02-11T00:00:00Z"


# ---------------------------------------------------------------------------
# Token counting (per BA4: whitespace word count)
# ---------------------------------------------------------------------------

def word_count(text: str) -> int:
    """Operational token count: len(text.split())."""
    return len(text.split())


def enforce_token_bounds(text: str, lo: int = 50, hi: int = 300) -> bool:
    """Return True if word count is within [lo, hi]."""
    wc = word_count(text)
    return lo <= wc <= hi


# ---------------------------------------------------------------------------
# Observation builders
# ---------------------------------------------------------------------------

def make_observations(
    user_text: str,
    timestamp: str = DEFAULT_TIMESTAMP,
    budget: Optional[Dict[str, Any]] = None,
    extra_observations: Optional[List[Observation]] = None,
) -> List[Observation]:
    """Build the standard observation triple (user_input, timestamp, budget)."""
    obs: List[Observation] = [
        Observation(
            kind=ObservationKind.USER_INPUT.value,
            payload={"text": user_text, "source": "x0p_harness"},
            author=Author.USER.value,
        ),
        Observation(
            kind=ObservationKind.TIMESTAMP.value,
            payload={"iso8601_utc": timestamp},
            author=Author.HOST.value,
        ),
        Observation(
            kind=ObservationKind.BUDGET.value,
            payload=budget or DEFAULT_BUDGET,
            author=Author.HOST.value,
        ),
    ]
    if extra_observations:
        obs.extend(extra_observations)
    return obs


# ---------------------------------------------------------------------------
# CandidateBundle builders
# ---------------------------------------------------------------------------

def make_notify_candidate(
    observations: List[Observation],
    message: str,
    clause_id: str = "INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
    claim: str = "User request acknowledged; notify response.",
    justification_text: str = "Authority to notify cited explicitly.",
) -> CandidateBundle:
    """Build a fully valid Notify candidate with proper citations and scope."""
    citation = f"{CITATION_PREFIX}{clause_id}"
    ar = ActionRequest(
        action_type=ActionType.NOTIFY.value,
        fields={"target": "stdout", "message": message},
        author=Author.REFLECTION.value,
    )
    sc = ScopeClaim(
        observation_ids=[observations[0].id],
        claim=claim,
        clause_ref=citation,
        author=Author.REFLECTION.value,
    )
    just = Justification(
        text=justification_text,
        author=Author.REFLECTION.value,
    )
    return CandidateBundle(
        action_request=ar,
        scope_claim=sc,
        justification=just,
        authority_citations=[citation],
    )


def make_read_candidate(
    observations: List[Observation],
    path: str = "./artifacts/phase-x/constitution/rsa_constitution.v0.1.1.yaml",
    clause_id: str = "INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
    claim: str = "Read requested file within allowlist.",
    justification_text: str = "Authority to read: file is within allowed paths.",
) -> CandidateBundle:
    """Build a fully valid ReadLocal candidate."""
    citation = f"{CITATION_PREFIX}{clause_id}"
    ar = ActionRequest(
        action_type=ActionType.READ_LOCAL.value,
        fields={"path": path},
        author=Author.REFLECTION.value,
    )
    sc = ScopeClaim(
        observation_ids=[observations[0].id],
        claim=claim,
        clause_ref=citation,
        author=Author.REFLECTION.value,
    )
    just = Justification(
        text=justification_text,
        author=Author.REFLECTION.value,
    )
    return CandidateBundle(
        action_request=ar,
        scope_claim=sc,
        justification=just,
        authority_citations=[citation],
    )


def make_write_candidate(
    observations: List[Observation],
    path: str = "./workspace/x0p_test.txt",
    content: str = "profiling test write",
    clause_id: str = "INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
    claim: str = "Write to allowed workspace path.",
    justification_text: str = "Authority to write: path is within allowed paths.",
) -> CandidateBundle:
    """Build a fully valid WriteLocal candidate."""
    citation = f"{CITATION_PREFIX}{clause_id}"
    ar = ActionRequest(
        action_type=ActionType.WRITE_LOCAL.value,
        fields={"path": path, "content": content},
        author=Author.REFLECTION.value,
    )
    sc = ScopeClaim(
        observation_ids=[observations[0].id],
        claim=claim,
        clause_ref=citation,
        author=Author.REFLECTION.value,
    )
    just = Justification(
        text=justification_text,
        author=Author.REFLECTION.value,
    )
    return CandidateBundle(
        action_request=ar,
        scope_claim=sc,
        justification=just,
        authority_citations=[citation],
    )


# ---------------------------------------------------------------------------
# Cycle input container
# ---------------------------------------------------------------------------

@dataclass
class CycleInput:
    """All inputs for a single profiling cycle."""
    cycle_id: str
    condition: str
    entropy_class: str
    observations: List[Observation]
    candidates: List[CandidateBundle]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def input_hash(self) -> str:
        """Deterministic hash of this cycle's inputs."""
        d = {
            "cycle_id": self.cycle_id,
            "condition": self.condition,
            "observations": [canonical_json(o.to_dict()) for o in self.observations],
            "candidates": [canonical_json(c.to_dict()) for c in self.candidates],
        }
        return hashlib.sha256(canonical_json(d).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

@dataclass
class ConditionManifest:
    """Manifest for a complete condition run."""
    condition: str
    entropy_class: str
    n_cycles: int
    seed: int
    cycles: List[CycleInput] = field(default_factory=list)
    corpus_hash: Optional[str] = None
    generator_version: str = "x0p-v0.1"

    def manifest_hash(self) -> str:
        """Deterministic hash of the entire manifest."""
        d = {
            "condition": self.condition,
            "entropy_class": self.entropy_class,
            "n_cycles": self.n_cycles,
            "seed": self.seed,
            "corpus_hash": self.corpus_hash or "",
            "generator_version": self.generator_version,
            "cycle_hashes": [c.input_hash() for c in self.cycles],
        }
        return hashlib.sha256(canonical_json(d).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Corpus loader
# ---------------------------------------------------------------------------

def load_corpus(path: Path) -> List[str]:
    """Load a text corpus file, one entry per non-empty line."""
    if not path.exists():
        raise FileNotFoundError(f"Corpus file not found: {path}")
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [line.strip() for line in lines if line.strip()]


def corpus_hash(lines: List[str]) -> str:
    """Hash a corpus for manifest recording."""
    joined = "\n".join(lines)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Seeded random helpers
# ---------------------------------------------------------------------------

def seeded_rng(seed: int) -> random.Random:
    """Create a seeded Random instance for deterministic generation."""
    return random.Random(seed)


def timestamp_for_cycle(base: str, cycle_index: int) -> str:
    """Generate a deterministic timestamp by incrementing seconds."""
    # Parse base ISO-8601 and add cycle_index seconds
    # Simple: just replace the seconds component
    # Base format: 2026-02-11T00:00:00Z
    # Increment by cycle_index seconds
    from datetime import datetime, timedelta, timezone
    dt = datetime.fromisoformat(base.replace("Z", "+00:00"))
    dt = dt + timedelta(seconds=cycle_index)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
