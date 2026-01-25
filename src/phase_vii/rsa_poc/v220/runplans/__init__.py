"""v2.2 Experiment Runplans

Core harness for running v2.2 Run 0 experiments with institutional friction.

Key components:
- V220ExperimentHarness: Main experiment runner
- Anti-Zeno termination logic
- Institution profile management
- Control vs Sovereign agent orchestration
"""

from .harness_v220 import (
    V220ExperimentHarness,
    V220RunConfig,
    V220RunResult,
    V220EpisodeRecord,
    V220StepRecord,
    AgentType,
)

from .anti_zeno import (
    AntiZenoMonitor,
    AntiZenoTermination,
    TerminationType,
    ANTI_ZENO_N,
    ANTI_ZENO_W,
    ANTI_ZENO_T,
)

__all__ = [
    "V220ExperimentHarness",
    "V220RunConfig",
    "V220RunResult",
    "V220EpisodeRecord",
    "V220StepRecord",
    "AgentType",
    "AntiZenoMonitor",
    "AntiZenoTermination",
    "TerminationType",
    "ANTI_ZENO_N",
    "ANTI_ZENO_W",
    "ANTI_ZENO_T",
]
