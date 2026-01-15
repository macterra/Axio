"""v2.1 Telemetry module

Additive extension of v2.0 telemetry with authority.* namespace.
"""

from .logger import (
    StepTelemetryV210,
    AuthorityTelemetry,
    TelemetryLoggerV210,
)

__all__ = [
    "StepTelemetryV210",
    "AuthorityTelemetry",
    "TelemetryLoggerV210",
]
