"""Normative State v1.1

Reuses v100 normative state unchanged.
v1.1 doesn't modify state logic, only audit layer.
"""

# Just re-export v100 state
try:
    from ...v100.state.normative import NormativeStateV100
except ImportError:
    from rsa_poc.v100.state.normative import NormativeStateV100

# v1.1 uses same state as v1.0
NormativeStateV110 = NormativeStateV100
