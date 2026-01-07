"""
RSA (Reflective Sovereign Agents) stress layer.

RSA v0.1/v0.2: Verifier-Outcome Noise Injection
RSA v1.0: Intentional Fixed Adversaries (Action-Layer Misuse)

A removable stress layer for stress-testing AKI's constitutional mechanics.

Note: ALSHarnessV080_SV and SVConfig are NOT exported here to avoid circular
imports. Import them directly from toy_aki.rsa.synthetic_verifier.
"""

from toy_aki.rsa.config import RSAConfig, RSANoiseModel, RSAScope
from toy_aki.rsa.adversary import RSAAdversary
from toy_aki.rsa.telemetry import (
    RSAEpochRecord,
    RSARunSummary,
    RSATelemetry,
)
from toy_aki.rsa.policy import (
    RSAPolicyModel,
    RSAPolicyConfig,
    RSAPolicy,
    RSAPolicyWrapper,
    AlwaysFailCommitmentPolicy,
    MinimalEligibilityOnlyPolicy,
    FixedRenewalTimingPolicy,
    AlwaysSelfRenewPolicy,
    LazyDictatorPolicy,
    create_policy,
)

# NOTE: ALSHarnessV080_SV and SVConfig must be imported directly from
# toy_aki.rsa.synthetic_verifier to avoid circular import issues.
# The synthetic_verifier module imports from toy_aki.als.harness, which
# imports from toy_aki.rsa, creating a cycle if we export SV here.

__all__ = [
    # v0.1/v0.2 exports
    "RSAConfig",
    "RSANoiseModel",
    "RSAScope",
    "RSAAdversary",
    "RSAEpochRecord",
    "RSARunSummary",
    "RSATelemetry",
    # v1.0 exports
    "RSAPolicyModel",
    "RSAPolicyConfig",
    "RSAPolicy",
    "RSAPolicyWrapper",
    "AlwaysFailCommitmentPolicy",
    "MinimalEligibilityOnlyPolicy",
    "FixedRenewalTimingPolicy",
    "AlwaysSelfRenewPolicy",
    "LazyDictatorPolicy",
    "create_policy",
]
