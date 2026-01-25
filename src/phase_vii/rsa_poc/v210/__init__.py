"""RSA-PoC v2.1 — Authority Injection (Explicit Power Claims)

v2.1 extends v2.0 with authority artifact handling while preserving
all previous constraints (v0.1 → v2.0).

Key additions:
- External Authority Artifact (EAA) ingestion
- AuthorityRecord logging
- JCOMP-2.1 rules: I/J/K/L (authority rejection mechanics)
- Authority variants: A1 (non-enforcing), A2 (enforcing), A3 (deceptive)

v2.1 Invariant:
Authority claims have no force unless explicitly legislated into the agent's law;
legitimacy is a normative property, not an environmental fact.
"""

__version__ = "2.1.0"
