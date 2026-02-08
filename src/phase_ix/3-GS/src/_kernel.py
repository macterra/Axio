"""
GS Import Helper — Resolves IX-2 kernel module imports.

All IX-3 modules import IX-2 symbols through this module to avoid
path manipulation in every file.
"""

import importlib
import os
import sys

# ─── Path setup: make IX-2 CUD importable ──────────────────────

_GS_SRC = os.path.dirname(os.path.abspath(__file__))
_GS_ROOT = os.path.normpath(os.path.join(_GS_SRC, '..'))
_CUD_ROOT = os.path.normpath(os.path.join(_GS_ROOT, '..', '2-CUD'))

if _CUD_ROOT not in sys.path:
    sys.path.insert(0, _CUD_ROOT)

# ─── Import IX-2 kernel modules ────────────────────────────────

_agent_model = importlib.import_module("src.agent_model")
_world_state = importlib.import_module("src.world_state")
_authority_store = importlib.import_module("src.authority_store")
_admissibility = importlib.import_module("src.admissibility")
_deadlock_classifier = importlib.import_module("src.deadlock_classifier")
_epoch_controller = importlib.import_module("src.epoch_controller")

# ─── Re-export symbols ─────────────────────────────────────────

# agent_model
RSA = _agent_model.RSA
Observation = _agent_model.Observation
ActionRequest = _agent_model.ActionRequest
Message = _agent_model.Message

# world_state
WorldState = _world_state.WorldState

# authority_store
AuthorityStore = _authority_store.AuthorityStore

# admissibility
evaluate_admissibility = _admissibility.evaluate_admissibility
EXECUTED = _admissibility.EXECUTED
JOINT_ADMISSIBILITY_FAILURE = _admissibility.JOINT_ADMISSIBILITY_FAILURE
ACTION_FAULT = _admissibility.ACTION_FAULT
NO_ACTION = _admissibility.NO_ACTION

# deadlock_classifier (IX-2 version, for reference)
CUDDeadlockClassifier = _deadlock_classifier.DeadlockClassifier
CUD_STATE_DEADLOCK = _deadlock_classifier.STATE_DEADLOCK
CUD_STATE_LIVELOCK = _deadlock_classifier.STATE_LIVELOCK
CUD_COLLAPSE = _deadlock_classifier.COLLAPSE
CUD_ORPHANING = _deadlock_classifier.ORPHANING
