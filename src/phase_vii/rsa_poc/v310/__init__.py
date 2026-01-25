"""RSA-PoC v3.1 — Normative State Instantiation & Secondary Non-Reducibility Tests

This module implements the v3.1 extension of v3.0:
- Instantiates the previously dormant normative state channel
- Gate P4: Fixed-window prompt buffer invariance
- Run B: Reflection Excision (disable normative writes)
- Run C: Persistence Excision (reset at episode boundaries)
- Novelty pressure detection and logging
"""

from .tokenizer import (
    TokenizerConfig,
    V310Tokenizer,
    get_tokenizer,
    PAD_STR,
    run_pad_self_test,
)

from .gate_p4 import (
    GateP4,
    GateP4Config,
    GateP4Violation,
    serialize_precedent_record,
    create_empty_precedent_buffer,
    ceil_to_32,
)

from .calibration import (
    run_calibration,
    validate_calibration,
    generate_synthetic_precedent,
)

from .harness import (
    V310AblationHarness,
    V310AblationSpec,
    V310RunConfig,
    V310InvalidReason,
    V310PrecedentTelemetry,
    V310ConflictSignature,
    V310EpisodeTelemetry,
    NoveltyDetector,
    NormativeStateManager,
)

__all__ = [
    # Tokenizer
    "TokenizerConfig",
    "V310Tokenizer",
    "get_tokenizer",
    "PAD_STR",
    "run_pad_self_test",
    # Gate P4
    "GateP4",
    "GateP4Config",
    "GateP4Violation",
    "serialize_precedent_record",
    "create_empty_precedent_buffer",
    "ceil_to_32",
    # Calibration
    "run_calibration",
    "validate_calibration",
    "generate_synthetic_precedent",
    # Harness
    "V310AblationHarness",
    "V310AblationSpec",
    "V310RunConfig",
    "V310InvalidReason",
    "V310PrecedentTelemetry",
    "V310ConflictSignature",
    "V310EpisodeTelemetry",
    "NoveltyDetector",
    "NormativeStateManager",
]
