"""E-CHOICE Probe — Full Pipeline Verification

This probe verifies that the LLM generator produces distinguishable action
templates under benign institutional conditions. This is a pre-flight check
that must pass before LLM integration experiments can proceed.

E-CHOICE Condition:
- At least 2 lawful actions available (E)
- At least 2 compile-valid actions (C)
- At least 2 distinct action templates produced (D)

Full Pipeline:
  J_raw (LLM) → FA (Formal Assistant) → JCOMP-2.3 → Selector → Execute

Under BENIGN institution (friction_modifier=1.0), both probe scenarios must:
1. Produce distinct action templates (not all same action)
2. Pass compilation (JCOMP-2.3)
3. Complete without error

If the probe fails, LLM integration should be blocked.
"""

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from datetime import datetime


@dataclass
class EChoiceProbeScenario:
    """A single E-CHOICE probe scenario."""
    scenario_id: str
    feasible_actions: List[str]
    apcm: Dict[str, Dict[str, Set[str]]]
    exists_clean: bool
    description: str


@dataclass
class EChoiceProbeResult:
    """Result of running an E-CHOICE probe scenario."""
    scenario_id: str
    success: bool
    action_selected: Optional[str]
    artifact_digest: Optional[str]
    compile_passed: bool
    error_message: Optional[str]
    template_hash: Optional[str]  # Hash of action template for distinctness check
    latency_ms: float


@dataclass
class EChoiceProbeReport:
    """Complete report from E-CHOICE probe execution."""
    timestamp: datetime
    passed: bool
    scenarios_run: int
    scenarios_passed: int
    distinct_templates: int
    min_distinct_required: int
    results: List[EChoiceProbeResult]
    failure_reason: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "passed": self.passed,
            "scenarios_run": self.scenarios_run,
            "scenarios_passed": self.scenarios_passed,
            "distinct_templates": self.distinct_templates,
            "min_distinct_required": self.min_distinct_required,
            "failure_reason": self.failure_reason,
            "results": [
                {
                    "scenario_id": r.scenario_id,
                    "success": r.success,
                    "action_selected": r.action_selected,
                    "artifact_digest": r.artifact_digest,
                    "compile_passed": r.compile_passed,
                    "error_message": r.error_message,
                    "template_hash": r.template_hash,
                    "latency_ms": r.latency_ms,
                }
                for r in self.results
            ],
        }


# Standard E-CHOICE probe scenarios
ECHOICE_PROBE_SCENARIOS = [
    EChoiceProbeScenario(
        scenario_id="PROBE_A",
        feasible_actions=["COOPERATE", "WAIT", "HELP"],
        apcm={
            "COOPERATE": {"violates": set(), "satisfies": {"P_PREFER_COOPERATION"}},
            "WAIT": {"violates": set(), "satisfies": set()},
            "HELP": {"violates": set(), "satisfies": {"P_PREFER_COOPERATION"}},
        },
        exists_clean=True,
        description="Three lawful actions, cooperation-favoring preferences",
    ),
    EChoiceProbeScenario(
        scenario_id="PROBE_B",
        feasible_actions=["DEFECT", "WAIT", "COOPERATE", "HOLD"],
        apcm={
            "DEFECT": {"violates": {"P_NO_DEFECT"}, "satisfies": set()},
            "WAIT": {"violates": set(), "satisfies": set()},
            "COOPERATE": {"violates": set(), "satisfies": {"P_PREFER_COOPERATION"}},
            "HOLD": {"violates": set(), "satisfies": set()},
        },
        exists_clean=True,
        description="Four actions, one unlawful (DEFECT), three lawful",
    ),
    EChoiceProbeScenario(
        scenario_id="PROBE_C",
        feasible_actions=["SHARE", "HOARD", "WAIT"],
        apcm={
            "SHARE": {"violates": set(), "satisfies": {"P_PREFER_COOPERATION"}},
            "HOARD": {"violates": {"P_NO_HOARD"}, "satisfies": set()},
            "WAIT": {"violates": set(), "satisfies": set()},
        },
        exists_clean=True,
        description="Three actions, one unlawful (HOARD), two lawful",
    ),
    EChoiceProbeScenario(
        scenario_id="PROBE_D",
        feasible_actions=["ACT_ALPHA", "ACT_BETA", "ACT_GAMMA", "ACT_DELTA"],
        apcm={
            "ACT_ALPHA": {"violates": set(), "satisfies": set()},
            "ACT_BETA": {"violates": set(), "satisfies": set()},
            "ACT_GAMMA": {"violates": set(), "satisfies": set()},
            "ACT_DELTA": {"violates": set(), "satisfies": set()},
        },
        exists_clean=True,
        description="Four symmetric lawful actions (no preference bias)",
    ),
]


class EChoiceProbe:
    """
    Full-pipeline E-CHOICE probe verifier.

    Runs probe scenarios through the complete pipeline:
    J_raw (LLM) → FA → JCOMP-2.3 → Selector → Execute

    Verifies:
    1. LLM produces valid artifacts
    2. Artifacts compile successfully
    3. Distinct action templates are produced (not all same)

    Usage:
        probe = EChoiceProbe()
        report = probe.run()
        if not report.passed:
            raise RuntimeError(f"E-CHOICE probe failed: {report.failure_reason}")
    """

    def __init__(
        self,
        min_distinct_templates: int = 2,
        scenarios: Optional[List[EChoiceProbeScenario]] = None,
    ):
        """
        Initialize E-CHOICE probe.

        Args:
            min_distinct_templates: Minimum distinct action templates required
            scenarios: Custom scenarios (default: ECHOICE_PROBE_SCENARIOS)
        """
        self.min_distinct_templates = min_distinct_templates
        self.scenarios = scenarios or ECHOICE_PROBE_SCENARIOS

        # Lazy-init components
        self._agent = None
        self._compiler = None
        self._normative_state = None

    def _init_components(self):
        """Initialize LLM generator and compiler."""
        if self._agent is not None:
            return

        # Check for required environment variables
        provider = os.getenv("LLM_PROVIDER")
        model = os.getenv("LLM_MODEL")
        api_key = os.getenv("LLM_API_KEY")

        if not all([provider, model, api_key]):
            raise RuntimeError(
                "E-CHOICE probe requires LLM environment variables: "
                "LLM_PROVIDER, LLM_MODEL, LLM_API_KEY"
            )

        # Initialize normative state
        from rsa_poc.v100.state.normative import NormativeStateV100
        self._normative_state = NormativeStateV100()

        # Initialize v2.3 generator
        from rsa_poc.v230.generator import LLMGeneratorV230
        self._agent = LLMGeneratorV230(self._normative_state)

        # Collect all probe actions for valid_actions set
        probe_actions = set()
        for scenario in self.scenarios:
            probe_actions.update(scenario.feasible_actions)
        # Add common actions
        probe_actions.update({
            "COOPERATE", "DEFECT", "WAIT", "HELP", "HOLD", "SHARE", "HOARD",
            "REFUSE", "GRIDLOCK", "ACT_ALPHA", "ACT_BETA", "ACT_GAMMA", "ACT_DELTA",
        })

        # Initialize v2.3 compiler with valid actions from probe scenarios
        from rsa_poc.v230.compiler import JCOMP230, RuleMNOPThresholds
        self._compiler = JCOMP230(
            valid_actions=probe_actions,
            mnop_thresholds=RuleMNOPThresholds(),
        )

    def run(self) -> EChoiceProbeReport:
        """
        Run the E-CHOICE probe across all scenarios.

        Returns:
            EChoiceProbeReport with pass/fail status and details
        """
        self._init_components()

        results: List[EChoiceProbeResult] = []
        template_hashes: Set[str] = set()

        print("\n" + "=" * 60)
        print("E-CHOICE PROBE — Full Pipeline Verification")
        print("=" * 60)

        for scenario in self.scenarios:
            print(f"\n  Running {scenario.scenario_id}: {scenario.description}")
            result = self._run_scenario(scenario)
            results.append(result)

            if result.success and result.template_hash:
                template_hashes.add(result.template_hash)

            status = "✓ PASS" if result.success else f"✗ FAIL: {result.error_message}"
            print(f"    Result: {status}")
            if result.action_selected:
                print(f"    Action: {result.action_selected}")
            if result.latency_ms:
                print(f"    Latency: {result.latency_ms:.0f}ms")

        # Evaluate overall result
        scenarios_passed = sum(1 for r in results if r.success)
        distinct_templates = len(template_hashes)

        # Determine pass/fail
        if scenarios_passed < len(self.scenarios):
            passed = False
            failure_reason = f"Only {scenarios_passed}/{len(self.scenarios)} scenarios passed"
        elif distinct_templates < self.min_distinct_templates:
            passed = False
            failure_reason = (
                f"Only {distinct_templates} distinct templates produced, "
                f"need {self.min_distinct_templates}"
            )
        else:
            passed = True
            failure_reason = None

        report = EChoiceProbeReport(
            timestamp=datetime.now(),
            passed=passed,
            scenarios_run=len(self.scenarios),
            scenarios_passed=scenarios_passed,
            distinct_templates=distinct_templates,
            min_distinct_required=self.min_distinct_templates,
            results=results,
            failure_reason=failure_reason,
        )

        print("\n" + "-" * 60)
        if passed:
            print(f"✓ E-CHOICE PROBE PASSED")
            print(f"  {scenarios_passed}/{len(self.scenarios)} scenarios passed")
            print(f"  {distinct_templates} distinct templates produced")
        else:
            print(f"✗ E-CHOICE PROBE FAILED")
            print(f"  Reason: {failure_reason}")
        print("=" * 60 + "\n")

        return report

    def _run_scenario(self, scenario: EChoiceProbeScenario) -> EChoiceProbeResult:
        """Run a single probe scenario."""
        start_time = datetime.now()

        try:
            # Reset agent for fresh state
            self._agent.reset()

            # Set benign SAM pressure (friction_modifier=1.0)
            self._agent.set_sam_pressure_context(
                friction_modifier=1.0,
                observable_description="BENIGN (probe scenario)",
            )

            # Generate artifact via LLM
            j_raw = self._agent.generate_raw(
                feasible_actions=scenario.feasible_actions,
                apcm=scenario.apcm,
                agent_id="ECHOICE_PROBE",
                exists_clean=scenario.exists_clean,
                previous_artifact_digest=None,
            )

            # Extract action from JAF structure
            # JAF-1.1 uses action_claim.candidate_action_id
            action = None
            if "action_claim" in j_raw and isinstance(j_raw["action_claim"], dict):
                action = j_raw["action_claim"].get("candidate_action_id")
            if not action:
                # Fallback to other possible field names
                action = j_raw.get("selected_action") or j_raw.get("action_id")
            if not action:
                raise ValueError("No action selected in artifact")

            # Check action is feasible
            if action not in scenario.feasible_actions:
                raise ValueError(f"Action {action} not in feasible set")

            # Compile artifact
            is_refusal = j_raw.get("refusal_reason") is not None
            is_gridlock = j_raw.get("gridlock_state") is not None

            compile_result = self._compiler.compile(
                j_raw,
                action,
                high_friction=False,  # BENIGN
                is_refusal=is_refusal,
                is_gridlock=is_gridlock,
                friction_modifier=1.0,
            )

            if not compile_result.success:
                raise ValueError(f"Compilation failed: {compile_result.error_code}")

            # Compute artifact digest and template hash
            artifact_digest = hashlib.sha256(
                json.dumps(j_raw, default=str, sort_keys=True).encode()
            ).hexdigest()[:16]

            # Template hash is based on action + key justification structure
            template_key = {
                "action": action,
                "constraint_count": len(j_raw.get("constraint_satisfaction", [])),
                "has_refusal": is_refusal,
                "has_gridlock": is_gridlock,
            }
            template_hash = hashlib.sha256(
                json.dumps(template_key, sort_keys=True).encode()
            ).hexdigest()[:8]

            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            return EChoiceProbeResult(
                scenario_id=scenario.scenario_id,
                success=True,
                action_selected=action,
                artifact_digest=artifact_digest,
                compile_passed=True,
                error_message=None,
                template_hash=template_hash,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            return EChoiceProbeResult(
                scenario_id=scenario.scenario_id,
                success=False,
                action_selected=None,
                artifact_digest=None,
                compile_passed=False,
                error_message=str(e),
                template_hash=None,
                latency_ms=latency_ms,
            )


def run_echoice_probe(
    min_distinct: int = 2,
    fail_fast: bool = True,
) -> EChoiceProbeReport:
    """
    Run E-CHOICE probe as a pre-flight check.

    Args:
        min_distinct: Minimum distinct templates required
        fail_fast: If True, raise exception on failure

    Returns:
        EChoiceProbeReport

    Raises:
        RuntimeError: If fail_fast=True and probe fails
    """
    probe = EChoiceProbe(min_distinct_templates=min_distinct)
    report = probe.run()

    if fail_fast and not report.passed:
        raise RuntimeError(f"E-CHOICE probe failed: {report.failure_reason}")

    return report


if __name__ == "__main__":
    # Run probe as standalone script
    import sys

    try:
        report = run_echoice_probe(fail_fast=False)

        # Save report
        output_path = "/tmp/echoice_probe_report.json"
        with open(output_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"Report saved to: {output_path}")

        sys.exit(0 if report.passed else 1)

    except Exception as e:
        print(f"E-CHOICE probe error: {e}")
        sys.exit(1)
