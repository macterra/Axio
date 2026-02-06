"""CUD Agent Strategies Package."""
import os
import sys
import importlib

_CUD_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
if _CUD_ROOT not in sys.path:
    sys.path.insert(0, _CUD_ROOT)

_static = importlib.import_module("agents.static_agent")
_adaptive = importlib.import_module("agents.adaptive_agent")

DisjointWriteAgent = _static.DisjointWriteAgent
StaticWriteAgent = _static.StaticWriteAgent
VetoedWriteAgent = _static.VetoedWriteAgent
StrategicRefusalAgent = _static.StrategicRefusalAgent
NoCiteWriteAgent = _static.NoCiteWriteAgent
ExitAfterCollisionAgent = _static.ExitAfterCollisionAgent
OrphanWriteAgent = _static.OrphanWriteAgent
OrphanExitAgent = _static.OrphanExitAgent
HashPartitionAgent = _adaptive.HashPartitionAgent
