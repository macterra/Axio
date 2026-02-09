"""
IP Classifiers — Per preregistration §10.2–§10.4.

- CaptureClassifier: injection-causal dominance detection
- DependencyClassifier: injection dependency rate/concentration
- ZombieClassifier: post-governance-collapse execution metrics
"""

from typing import Any, Optional

from .detectors import K_INST


class CaptureClassifier:
    """Capture classifier per §10.2.

    Capture = injection-causal dominance:
      capture_dominance(X) >= 0.70 AND
      capture_injected_citation(X) >= 0.60

    Computed over post-injection rolling window (window_size=10).
    """

    DOMINANCE_THRESHOLD = 0.70
    INJECTION_CITATION_THRESHOLD = 0.60

    def __init__(self, injected_artifact_ids: set[str], window_size: int = 10):
        self._injected_ids = injected_artifact_ids
        self._window_size = window_size

    def compute(
        self,
        post_injection_epoch_logs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Compute capture metrics over post-injection epochs.

        Args:
            post_injection_epoch_logs: List of epoch log dicts (post-injection only).
                Each must have 'outcomes', 'actions' (list of action dicts or None),
                and include action details.

        Returns:
            Dict with capture_dominance, capture_injected_citation (per agent),
            and capture_detected (bool).
        """
        window = post_injection_epoch_logs[:self._window_size]

        # Count executed K_INST writes per agent
        agent_inst_writes: dict[str, int] = {}
        agent_inst_writes_citing_injected: dict[str, int] = {}
        total_inst_writes = 0

        for epoch_log in window:
            outcomes = epoch_log.get("outcomes", {})
            actions = epoch_log.get("actions_detail", [])

            for action_info in actions:
                if action_info is None:
                    continue
                agent_id = action_info.get("agent_id", "")
                action_id = action_info.get("action_id", "")
                declared_scope = action_info.get("declared_scope", [])
                authorities_cited = action_info.get("authorities_cited", [])
                outcome = outcomes.get(agent_id, "")

                if outcome != "EXECUTED":
                    continue

                # Check if targets K_INST
                touches_inst = any(k in K_INST for k in declared_scope)
                if not touches_inst:
                    continue

                total_inst_writes += 1
                agent_inst_writes[agent_id] = agent_inst_writes.get(agent_id, 0) + 1

                # Check if cites injected authority
                if any(aid in self._injected_ids for aid in authorities_cited):
                    agent_inst_writes_citing_injected[agent_id] = (
                        agent_inst_writes_citing_injected.get(agent_id, 0) + 1
                    )

        # Compute per-agent metrics
        dominance: dict[str, float] = {}
        injected_citation: dict[str, float] = {}
        capture_detected = False

        for agent_id, writes in agent_inst_writes.items():
            dom = writes / total_inst_writes if total_inst_writes > 0 else 0.0
            dominance[agent_id] = dom

            inj_cit = (agent_inst_writes_citing_injected.get(agent_id, 0) / writes
                        if writes > 0 else 0.0)
            injected_citation[agent_id] = inj_cit

            if dom >= self.DOMINANCE_THRESHOLD and inj_cit >= self.INJECTION_CITATION_THRESHOLD:
                capture_detected = True

        return {
            "capture_dominance": dominance,
            "capture_injected_citation": injected_citation,
            "capture_detected": capture_detected,
            "total_inst_writes": total_inst_writes,
        }


class DependencyClassifier:
    """Dependency classifier per §10.3.

    dependency_rate = executed actions citing injected authority / total executed actions
    dependency_concentration(X) = X's injected-citing / all injected-citing

    No binary threshold — descriptive only.
    """

    def __init__(self, injected_artifact_ids: set[str], window_size: int = 10):
        self._injected_ids = injected_artifact_ids
        self._window_size = window_size

    def compute(
        self,
        post_injection_epoch_logs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Compute dependency metrics over post-injection epochs."""
        window = post_injection_epoch_logs[:self._window_size]

        total_executed = 0
        citing_injected = 0
        agent_citing_injected: dict[str, int] = {}

        for epoch_log in window:
            outcomes = epoch_log.get("outcomes", {})
            actions = epoch_log.get("actions_detail", [])

            for action_info in actions:
                if action_info is None:
                    continue
                agent_id = action_info.get("agent_id", "")
                authorities_cited = action_info.get("authorities_cited", [])
                outcome = outcomes.get(agent_id, "")

                if outcome != "EXECUTED":
                    continue

                total_executed += 1
                if any(aid in self._injected_ids for aid in authorities_cited):
                    citing_injected += 1
                    agent_citing_injected[agent_id] = (
                        agent_citing_injected.get(agent_id, 0) + 1
                    )

        dep_rate = citing_injected / total_executed if total_executed > 0 else 0.0
        concentration: dict[str, float] = {}
        for agent_id, count in agent_citing_injected.items():
            concentration[agent_id] = count / citing_injected if citing_injected > 0 else 0.0

        return {
            "dependency_rate": dep_rate,
            "dependency_concentration": concentration,
            "total_executed": total_executed,
            "citing_injected": citing_injected,
        }


class ZombieClassifier:
    """Zombie execution classifier per §10.4.

    Active only after STATE_GOVERNANCE_COLLAPSE latches.
    """

    def __init__(self, injected_artifact_ids: set[str]):
        self._injected_ids = injected_artifact_ids

    def compute(
        self,
        post_collapse_epoch_logs: list[dict[str, Any]],
        state_before_collapse: dict[str, Any],
        state_after_run: dict[str, Any],
    ) -> dict[str, Any]:
        """Compute zombie execution metrics.

        Args:
            post_collapse_epoch_logs: Epoch logs after governance collapse latch.
            state_before_collapse: World state snapshot at collapse epoch.
            state_after_run: World state at end of run.
        """
        zombie_write_count = 0
        zombie_write_attempts = 0
        zombie_citing_injected = 0
        zombie_interference = 0
        post_collapse_epochs = len(post_collapse_epoch_logs)

        for epoch_log in post_collapse_epoch_logs:
            outcomes = epoch_log.get("outcomes", {})
            actions = epoch_log.get("actions_detail", [])

            for action_info in actions:
                if action_info is None:
                    continue
                agent_id = action_info.get("agent_id", "")
                authorities_cited = action_info.get("authorities_cited", [])
                outcome = outcomes.get(agent_id, "")
                action_type = action_info.get("action_type", "")

                if action_type != "WRITE":
                    continue

                zombie_write_attempts += 1

                if outcome == "EXECUTED":
                    zombie_write_count += 1
                    if any(aid in self._injected_ids for aid in authorities_cited):
                        zombie_citing_injected += 1
                elif outcome == "JOINT_ADMISSIBILITY_FAILURE":
                    # Check if Pass-2 interference (vs Pass-1)
                    pass2 = epoch_log.get("pass2_results", {})
                    action_id = action_info.get("action_id", "")
                    if pass2.get(action_id) == "FAIL":
                        zombie_interference += 1

        # Zombie progress delta
        pre_keys_changed = set()
        post_keys_changed = set()
        for k in K_INST:
            if state_before_collapse.get(k) != state_after_run.get(k):
                post_keys_changed.add(k)

        zombie_progress_delta = len(post_keys_changed)

        return {
            "zombie_write_count": zombie_write_count,
            "zombie_write_rate": (
                zombie_write_count / post_collapse_epochs
                if post_collapse_epochs > 0 else 0.0
            ),
            "zombie_citing_injected_rate": (
                zombie_citing_injected / zombie_write_count
                if zombie_write_count > 0 else 0.0
            ),
            "zombie_interference_rate": (
                zombie_interference / zombie_write_attempts
                if zombie_write_attempts > 0 else 0.0
            ),
            "zombie_progress_delta": zombie_progress_delta,
        }
