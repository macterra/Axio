"""RSA-PoC v1.0 (MVRA-1) - Coherence Under Self-Conflict

This package implements the RSA-PoC v1.0 specification:
a strict extension of v0.1 that tests whether an agent with causally load-bearing
justification can remain coherent when its own commitments collide.

v1.0 adds:
- APCM (Action-Preference Consequence Map) truth grounding
- Authorized Violations and Required Preservations
- Conflict Attribution and Precedent Reference
- Necessity Clause (Rule 1.5) - prevents gratuitous violations
- Anti-oscillation enforcement
"""

__version__ = "1.0.0"
