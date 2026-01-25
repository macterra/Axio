"""v2.3 Experiment Runplans

Core harness for running v2.3 experiments with Strategic Adversary Model.

Extends v2.2 with:
- SAM (Strategic Adversary Model) integration
- Paired-run evaluation (SAM vs neutralized, same seed)
- E-CHOICE step filtering
- Rules M/N/O/P aggregate audit

Key components:
- V230ExperimentHarness: Main experiment runner with paired evaluation
- PairedRunResult: Results from SAM vs neutralized comparison
- V230RunConfig: Configuration with SAM profile selection
"""

from .harness_v230 import (
    V230ExperimentHarness,
    V230RunConfig,
    V230RunResult,
    V230EpisodeRecord,
    V230StepRecord,
    PairedRunResult,
    PairedEpisodeResult,
)

__all__ = [
    "V230ExperimentHarness",
    "V230RunConfig",
    "V230RunResult",
    "V230EpisodeRecord",
    "V230StepRecord",
    "PairedRunResult",
    "PairedEpisodeResult",
]
