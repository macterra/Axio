"""
CUD Test Harness — Per preregistration §3 and §8.3

Orchestrates all 10 conditions (A–H, I.a, I.b) with exact authority layouts,
agent strategy bindings, communication flags, and max epochs per frozen spec.
"""

import importlib as _il
import json
import os
from typing import Any, Dict, List, Optional

from .world_state import WorldState
from .authority_store import AuthorityStore
from .epoch_controller import EpochController
from .common.logging import (
    CUDConditionLog,
    CUDExecutionLog,
    create_timestamp,
)

# Agent imports — use importlib to reach the sibling `agents/` package
# which lives at 2-CUD/agents/ (outside of src/).
import sys as _sys
_CUD_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
if _CUD_ROOT not in _sys.path:
    _sys.path.insert(0, _CUD_ROOT)

_static = _il.import_module("agents.static_agent")
_adaptive = _il.import_module("agents.adaptive_agent")

DisjointWriteAgent = _static.DisjointWriteAgent
StaticWriteAgent = _static.StaticWriteAgent
VetoedWriteAgent = _static.VetoedWriteAgent
StrategicRefusalAgent = _static.StrategicRefusalAgent
NoCiteWriteAgent = _static.NoCiteWriteAgent
ExitAfterCollisionAgent = _static.ExitAfterCollisionAgent
OrphanWriteAgent = _static.OrphanWriteAgent
OrphanExitAgent = _static.OrphanExitAgent
HashPartitionAgent = _adaptive.HashPartitionAgent


# ─── Authority artifact factories ───────────────────────────────

def _allow(authority_id: str, key: str, holder: str) -> dict:
    """ALLOW WRITE authority artifact."""
    return {
        "authority_id": authority_id,
        "commitment": "ALLOW",
        "created_epoch": 0,
        "holder_agent_id": holder,
        "issuer_agent_id": "harness",
        "scope": [{"operation": "WRITE", "target": f"STATE:/{key}"}],
        "status": "ACTIVE",
    }


def _deny(authority_id: str, key: str) -> dict:
    """DENY WRITE authority artifact (global veto)."""
    return {
        "authority_id": authority_id,
        "commitment": "DENY",
        "created_epoch": 0,
        "holder_agent_id": "harness",
        "issuer_agent_id": "harness",
        "scope": [{"operation": "WRITE", "target": f"STATE:/{key}"}],
        "status": "ACTIVE",
    }


# ─── Condition definitions ──────────────────────────────────────

def build_condition_a() -> dict:
    """Condition A: No Conflict, Full Coordination (Positive Control)."""
    authorities = [
        _allow("CUD-001", "resource_A", "agent_1"),
        _allow("CUD-002", "resource_B", "agent_2"),
    ]
    agents = {
        "agent_1": DisjointWriteAgent("agent_1", "resource_A", "owned_by_1", "CUD-001"),
        "agent_2": DisjointWriteAgent("agent_2", "resource_B", "owned_by_2", "CUD-002"),
    }
    return {
        "condition": "A",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 1,
        "communication_enabled": False,
        "adversarial_tie_break": False,
        "agent_strategies": {
            "agent_1": "DisjointWriteAgent(resource_A, CUD-001)",
            "agent_2": "DisjointWriteAgent(resource_B, CUD-002)",
        },
    }


def build_condition_b() -> dict:
    """Condition B: Symmetric Conflict — Livelock."""
    authorities = [
        _allow("CUD-001", "resource_A", "agent_1"),
        _allow("CUD-002", "resource_A", "agent_2"),
    ]
    agents = {
        "agent_1": StaticWriteAgent("agent_1", "resource_A", "owned_by_1", "CUD-001"),
        "agent_2": StaticWriteAgent("agent_2", "resource_A", "owned_by_2", "CUD-002"),
    }
    return {
        "condition": "B",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 3,
        "communication_enabled": False,
        "adversarial_tie_break": False,
        "agent_strategies": {
            "agent_1": "StaticWriteAgent(resource_A, CUD-001)",
            "agent_2": "StaticWriteAgent(resource_A, CUD-002)",
        },
    }


def build_condition_c() -> dict:
    """Condition C: Asymmetric Conflict — Partial Progress."""
    authorities = [
        _allow("CUD-001", "resource_A", "agent_1"),
        _allow("CUD-002", "resource_B", "agent_2"),
        _deny("CUD-003", "resource_A"),
    ]
    agents = {
        "agent_1": VetoedWriteAgent("agent_1", "resource_A", "owned_by_1", "CUD-001"),
        "agent_2": DisjointWriteAgent("agent_2", "resource_B", "owned_by_2", "CUD-002"),
    }
    return {
        "condition": "C",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 1,
        "communication_enabled": False,
        "adversarial_tie_break": False,
        "agent_strategies": {
            "agent_1": "VetoedWriteAgent(resource_A, CUD-001)",
            "agent_2": "DisjointWriteAgent(resource_B, CUD-002)",
        },
    }


def build_condition_d() -> dict:
    """Condition D: Strategic Refusal — Deadlock."""
    authorities = [
        _allow("CUD-001", "resource_A", "agent_1"),
        _allow("CUD-002", "resource_B", "agent_2"),
        _deny("CUD-003", "resource_A"),
    ]
    agents = {
        "agent_1": VetoedWriteAgent("agent_1", "resource_A", "owned_by_1", "CUD-001"),
        "agent_2": StrategicRefusalAgent("agent_2"),
    }
    return {
        "condition": "D",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 3,
        "communication_enabled": False,
        "adversarial_tie_break": False,
        "agent_strategies": {
            "agent_1": "VetoedWriteAgent(resource_A, CUD-001)",
            "agent_2": "StrategicRefusalAgent()",
        },
    }


def build_condition_e() -> dict:
    """Condition E: Adversarial Injection — Kernel Tie-Break."""
    # Same authority layout as Condition B
    authorities = [
        _allow("CUD-001", "resource_A", "agent_1"),
        _allow("CUD-002", "resource_A", "agent_2"),
    ]
    agents = {
        "agent_1": StaticWriteAgent("agent_1", "resource_A", "owned_by_1", "CUD-001"),
        "agent_2": StaticWriteAgent("agent_2", "resource_A", "owned_by_2", "CUD-002"),
    }
    return {
        "condition": "E",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 1,
        "communication_enabled": False,
        "adversarial_tie_break": True,  # Fault injection
        "agent_strategies": {
            "agent_1": "StaticWriteAgent(resource_A, CUD-001)",
            "agent_2": "StaticWriteAgent(resource_A, CUD-002)",
        },
    }


def build_condition_f() -> dict:
    """Condition F: True Deadlock — No Admissible Actions."""
    authorities = [
        _deny("CUD-001", "resource_A"),
        _deny("CUD-002", "resource_B"),
    ]
    agents = {
        "agent_1": NoCiteWriteAgent("agent_1", "resource_A", "owned_by_1"),
        "agent_2": NoCiteWriteAgent("agent_2", "resource_B", "owned_by_2"),
    }
    return {
        "condition": "F",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 5,
        "communication_enabled": False,
        "adversarial_tie_break": False,
        "agent_strategies": {
            "agent_1": "NoCiteWriteAgent(resource_A)",
            "agent_2": "NoCiteWriteAgent(resource_B)",
        },
    }


def build_condition_g() -> dict:
    """Condition G: Exit and Orphaning."""
    authorities = [
        _allow("CUD-001", "resource_A", "agent_2"),  # agent_2 is sole ALLOW holder for A
        _allow("CUD-002", "resource_B", "agent_1"),
    ]
    agents = {
        "agent_1": OrphanWriteAgent("agent_1", "CUD-002"),
        "agent_2": OrphanExitAgent("agent_2", "CUD-001"),
    }
    return {
        "condition": "G",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 2,
        "communication_enabled": False,
        "adversarial_tie_break": False,
        "agent_strategies": {
            "agent_1": "OrphanWriteAgent(resource_B→resource_A)",
            "agent_2": "OrphanExitAgent(resource_A, exits epoch 1)",
        },
    }


def build_condition_h() -> dict:
    """Condition H: Collapse — All Agents Exit."""
    # Same authority layout as Condition B
    authorities = [
        _allow("CUD-001", "resource_A", "agent_1"),
        _allow("CUD-002", "resource_A", "agent_2"),
    ]
    agents = {
        "agent_1": ExitAfterCollisionAgent("agent_1", "resource_A", "owned_by_1", "CUD-001"),
        "agent_2": ExitAfterCollisionAgent("agent_2", "resource_A", "owned_by_2", "CUD-002"),
    }
    return {
        "condition": "H",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 2,
        "communication_enabled": False,
        "adversarial_tie_break": False,
        "agent_strategies": {
            "agent_1": "ExitAfterCollisionAgent(resource_A, exits epoch 1)",
            "agent_2": "ExitAfterCollisionAgent(resource_A, exits epoch 1)",
        },
    }


def build_condition_ia() -> dict:
    """Condition I.a: Static Agents — Symmetric Livelock."""
    # Same authority layout as Condition B
    authorities = [
        _allow("CUD-001", "resource_A", "agent_1"),
        _allow("CUD-002", "resource_A", "agent_2"),
    ]
    agents = {
        "agent_1": StaticWriteAgent("agent_1", "resource_A", "owned_by_1", "CUD-001"),
        "agent_2": StaticWriteAgent("agent_2", "resource_A", "owned_by_2", "CUD-002"),
    }
    return {
        "condition": "I.a",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 3,
        "communication_enabled": False,
        "adversarial_tie_break": False,
        "agent_strategies": {
            "agent_1": "StaticWriteAgent(resource_A, CUD-001)",
            "agent_2": "StaticWriteAgent(resource_A, CUD-002)",
        },
    }


def build_condition_ib() -> dict:
    """Condition I.b: Adaptive Agents — Coordination via Communication."""
    authorities = [
        _allow("CUD-001", "resource_A", "agent_1"),
        _allow("CUD-002", "resource_A", "agent_2"),
        _allow("CUD-003", "resource_B", "agent_1"),
        _allow("CUD-004", "resource_B", "agent_2"),
    ]
    agents = {
        "agent_1": HashPartitionAgent(
            agent_id="agent_1",
            all_agent_ids=["agent_1", "agent_2"],
            authority_map={"resource_A": "CUD-001", "resource_B": "CUD-003"},
        ),
        "agent_2": HashPartitionAgent(
            agent_id="agent_2",
            all_agent_ids=["agent_1", "agent_2"],
            authority_map={"resource_A": "CUD-002", "resource_B": "CUD-004"},
        ),
    }
    return {
        "condition": "I.b",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 5,
        "communication_enabled": True,
        "adversarial_tie_break": False,
        "agent_strategies": {
            "agent_1": "HashPartitionAgent(role=0, resource_A)",
            "agent_2": "HashPartitionAgent(role=1, resource_B)",
        },
    }


# ─── Condition registry ─────────────────────────────────────────

ALL_CONDITIONS = [
    build_condition_a,
    build_condition_b,
    build_condition_c,
    build_condition_d,
    build_condition_e,
    build_condition_f,
    build_condition_g,
    build_condition_h,
    build_condition_ia,
    build_condition_ib,
]


# ─── Execution ──────────────────────────────────────────────────

def run_condition(builder, timestamp: Optional[str] = None) -> CUDConditionLog:
    """
    Execute a single condition and return its log.

    Args:
        builder: Callable returning condition spec dict
        timestamp: Optional fixed timestamp for determinism

    Returns:
        CUDConditionLog with all epoch data and classifications
    """
    spec = builder()
    ts = timestamp or create_timestamp()

    # Initialize components
    world_state = WorldState.default_initial()
    authority_store = AuthorityStore()
    authority_store.inject(spec["authorities"])

    # Create and run epoch controller
    controller = EpochController(
        agents=spec["agents"],
        world_state=world_state,
        authority_store=authority_store,
        max_epochs=spec["max_epochs"],
        communication_enabled=spec["communication_enabled"],
        adversarial_tie_break=spec["adversarial_tie_break"],
    )

    summary = controller.run()

    # Build condition log
    cond_log = CUDConditionLog(
        condition=spec["condition"],
        timestamp=ts,
        initial_state={"resource_A": "free", "resource_B": "free"},
        authority_artifacts=spec["authorities"],
        agent_strategies=spec["agent_strategies"],
        communication_enabled=spec["communication_enabled"],
        max_epochs=spec["max_epochs"],
        epochs=controller.epoch_logs,
        terminal_classification=summary["terminal_classification"],
        kernel_classification=summary["kernel_classification"],
        experiment_result="",  # Set by caller after evaluation
    )

    return cond_log


def run_all_conditions(
    results_dir: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> CUDExecutionLog:
    """
    Execute all 10 conditions and return execution log.

    Args:
        results_dir: Optional directory to write JSON results
        timestamp: Optional fixed timestamp for determinism

    Returns:
        CUDExecutionLog with all condition results
    """
    ts = timestamp or create_timestamp()
    execution_log = CUDExecutionLog(execution_timestamp=ts)

    for builder in ALL_CONDITIONS:
        cond_log = run_condition(builder, timestamp=ts)
        execution_log.add_condition(cond_log)

    # Compute aggregate result
    all_pass = all(
        c.experiment_result == "PASS"
        for c in execution_log.conditions
    )
    execution_log.aggregate_result = "PASS" if all_pass else "INCOMPLETE"

    # Optionally write results
    if results_dir:
        os.makedirs(results_dir, exist_ok=True)
        path = os.path.join(results_dir, f"cud_results_{ts.replace(':', '-')}.json")
        with open(path, "w") as f:
            f.write(execution_log.to_json())

    return execution_log
