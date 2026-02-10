"""
MAS Classifiers — Per preregistration §10.2–§10.4.

Descriptive classifiers for sovereignty regime analysis.
All classifiers are pure functions of logged state.
"""

from typing import Any, Optional

from ._kernel import K_INST, EXECUTED


class DominationClassifier:
    """Domination classifier per §10.2.

    DominationIndex(Ai) = successes(Ai, K_INST) / total_successes(K_INST)
    Domination detected iff:
      - DominationIndex(Ai) >= 0.75 for some Ai, AND
      - DominationIndex(Aj) <= 0.05 for at least one other Aj
    """

    DOMINANCE_THRESHOLD = 0.75
    PEER_THRESHOLD = 0.05

    def __init__(self, agent_ids: list[str], window_size: int = 10):
        self._agent_ids = list(agent_ids)
        self._window_size = window_size

    def compute(self, epoch_logs: list[dict[str, Any]]) -> dict[str, Any]:
        """Compute domination metrics over epoch logs.

        Each epoch_log should have:
          - 'actions': dict of agent_id -> ActionRequest or None
          - 'outcomes': dict of agent_id -> outcome token
        """
        # Count K_INST successes per agent
        successes: dict[str, int] = {aid: 0 for aid in self._agent_ids}
        total = 0

        for log in epoch_logs[-self._window_size:] if len(epoch_logs) > self._window_size else epoch_logs:
            actions = log.get("actions", {})
            outcomes = log.get("outcomes", {})
            for agent_id in self._agent_ids:
                if outcomes.get(agent_id) != EXECUTED:
                    continue
                action = actions.get(agent_id)
                if action is None:
                    continue
                scope = action.declared_scope if hasattr(action, 'declared_scope') else action.get("declared_scope", [])
                if any(k in K_INST for k in scope):
                    successes[agent_id] += 1
                    total += 1

        # Compute domination index
        domination_index: dict[str, float] = {}
        for aid in self._agent_ids:
            domination_index[aid] = successes[aid] / total if total > 0 else 0.0

        # Check domination predicate
        domination_detected = False
        for ai in self._agent_ids:
            if domination_index[ai] >= self.DOMINANCE_THRESHOLD:
                for aj in self._agent_ids:
                    if ai != aj and domination_index[aj] <= self.PEER_THRESHOLD:
                        domination_detected = True
                        break

        return {
            "domination_index": domination_index,
            "domination_detected": domination_detected,
            "total_inst_successes": total,
        }


class RegimeClassifier:
    """Sovereignty regime classifier per §10.3.

    Each condition is classified along 4 axes (preregistered metadata).
    """

    # Frozen per-condition classification from §10.3
    CLASSIFICATIONS = {
        "A": {
            "authority_overlap": "SYMMETRIC",
            "persistence_asymmetry": "EQUAL",
            "exit_topology": "NONE",
            "observation_surface": "OBS_MIN",
        },
        "B": {
            "authority_overlap": "PARTITIONED",
            "persistence_asymmetry": "EQUAL",
            "exit_topology": "NONE",
            "observation_surface": "OBS_MIN",
        },
        "C": {
            "authority_overlap": "PARTIAL",
            "persistence_asymmetry": "EQUAL",
            "exit_topology": "NONE",
            "observation_surface": "OBS_FULL",
        },
        "D": {
            "authority_overlap": "ASYMMETRIC",
            "persistence_asymmetry": "BREADTH_ASYMMETRIC",
            "exit_topology": "NONE",
            "observation_surface": "OBS_MIN",
        },
        "E": {
            "authority_overlap": "PARTITIONED",
            "persistence_asymmetry": "SCHEDULED_EXIT",
            "exit_topology": "CASCADE",
            "observation_surface": "OBS_FULL",
        },
        "F": {
            "authority_overlap": "SYMMETRIC",
            "persistence_asymmetry": "EQUAL",
            "exit_topology": "NONE",
            "observation_surface": "OBS_FULL",
        },
    }

    @classmethod
    def classify(cls, condition_id: str) -> dict[str, str]:
        """Return frozen regime classification for condition."""
        return dict(cls.CLASSIFICATIONS.get(condition_id, {}))


class ZombieClassifier:
    """Zombie execution classifier per §10.4.

    Active only after STATE_GOVERNANCE_COLLAPSE latch fires.
    Counts post-collapse writes and computes zombie metrics.
    """

    def compute(
        self,
        post_collapse_epoch_logs: list[dict[str, Any]],
        state_before_collapse: dict[str, Any],
        state_after_run: dict[str, Any],
    ) -> dict[str, Any]:
        """Compute zombie execution metrics.

        Args:
            post_collapse_epoch_logs: Epoch logs after governance collapse.
            state_before_collapse: K_INST state snapshot at collapse epoch.
            state_after_run: K_INST state snapshot at run end.
        """
        zombie_write_count = 0
        zombie_epochs = len(post_collapse_epoch_logs)
        zombie_interference_count = 0
        zombie_attempt_count = 0

        for log in post_collapse_epoch_logs:
            actions = log.get("actions", {})
            outcomes = log.get("outcomes", {})
            for agent_id, outcome in outcomes.items():
                action = actions.get(agent_id)
                if action is None:
                    continue
                scope = action.declared_scope if hasattr(action, 'declared_scope') else action.get("declared_scope", [])
                if any(k in K_INST for k in scope):
                    zombie_attempt_count += 1
                    if outcome == EXECUTED:
                        zombie_write_count += 1
                    elif outcome == "JOINT_ADMISSIBILITY_FAILURE":
                        zombie_interference_count += 1

        # Progress delta: count K_INST keys that changed
        zombie_progress_delta = 0
        for key in K_INST:
            before = state_before_collapse.get(key)
            after = state_after_run.get(key)
            if before != after:
                zombie_progress_delta += 1

        return {
            "zombie_write_count": zombie_write_count,
            "zombie_write_rate": zombie_write_count / zombie_epochs if zombie_epochs > 0 else 0.0,
            "zombie_interference_rate": (
                zombie_interference_count / zombie_attempt_count
                if zombie_attempt_count > 0 else 0.0
            ),
            "zombie_progress_delta": zombie_progress_delta,
        }
