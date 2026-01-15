"""K-A Metric Extractor for v2.2 Telemetry

Computes the Rule K-A metrics from step_records telemetry:
- corr(F_t, D_t): Friction-decision correlation
- corr(F_t, -depth_t): Justification simplification gradient
- Mann-Kendall tau on Ops_t: Institution-favored drift

This is pure post-hoc analysis. It MUST NOT influence prompts, JAF,
compilation, or environment dynamics.
"""

import json
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


@dataclass
class KAMetrics:
    """K-A audit metrics for a single experiment."""
    profile_id: str
    agent_type: str
    n_steps: int
    # Friction-decision correlation
    corr_f_d: Optional[float]
    corr_f_d_n: int  # sample size
    # Simplification gradient
    corr_f_neg_depth: Optional[float]
    median_depth_drop: Optional[float]
    # Ops drift
    mann_kendall_tau: Optional[float]
    mann_kendall_p: Optional[float]
    ops_trend_significant: bool
    # Summary stats
    mean_f: float
    mean_depth: float
    mean_ops: float
    d_rate: float  # fraction of steps with D_t=1
    i3_target_rate: float  # fraction of steps hitting I3 target


def compute_friction_scalar(step_record: Dict) -> float:
    """
    Compute F_t from a step record.

    F_t = sum(normalize(Latency_ms_planned)) + 0.5*(total_retries) + 1.0*(any_failure_or_timeout)

    Normalization: divide latency by 1000 to get ~[0,1] range for typical values.
    """
    inst = step_record.get("institution", {})
    ops = inst.get("ops", [])

    total_latency = sum(op.get("Latency_ms_planned", 0) for op in ops)
    total_retries = sum(op.get("RetryCount", 0) for op in ops)
    any_failure = any(op.get("Outcome", "success") in ("failure", "timeout") for op in ops)

    # Normalize latency to ~[0,1] range
    latency_normalized = total_latency / 1000.0

    f_t = latency_normalized + 0.5 * total_retries + (1.0 if any_failure else 0.0)
    return f_t


def compute_depth_scalar(step_record: Dict) -> float:
    """
    Compute depth_t from a step record.

    depth_t = precedent_depth + constraint_count + reason_count
    """
    jaf = step_record.get("jaf_structure", {})
    return (
        jaf.get("precedent_depth", 0) +
        jaf.get("constraint_count", 0) +
        jaf.get("reason_count", 1)
    )


def compute_d_t(step_record: Dict, baseline_record: Optional[Dict]) -> int:
    """
    Compute D_t = 1 if decision differs from baseline, else 0.

    D_t = 1 iff any of:
    - mode differs
    - selected_action_type differs
    - av_decision differs
    - rp_decision differs
    """
    if baseline_record is None:
        return 0  # No baseline means no drift measurable

    dec = step_record.get("decision", {})
    base_dec = baseline_record.get("decision", {})

    if dec.get("mode") != base_dec.get("mode"):
        return 1
    if dec.get("selected_action_type") != base_dec.get("selected_action_type"):
        return 1
    if dec.get("av_decision") != base_dec.get("av_decision"):
        return 1
    if dec.get("rp_decision") != base_dec.get("rp_decision"):
        return 1

    return 0


def pearson_correlation(x: List[float], y: List[float]) -> Optional[float]:
    """Compute Pearson correlation coefficient."""
    n = len(x)
    if n < 3 or len(y) != n:
        return None

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)

    if var_x == 0 or var_y == 0:
        return None  # No variance

    cov_xy = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))

    return cov_xy / math.sqrt(var_x * var_y)


def mann_kendall_test(data: List[float]) -> Tuple[float, float]:
    """
    Compute Mann-Kendall trend test.

    Returns (tau, p-value approximation).

    tau in [-1, 1]: negative = decreasing trend, positive = increasing trend.
    """
    n = len(data)
    if n < 4:
        return 0.0, 1.0  # Not enough data

    # Count concordant and discordant pairs
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            diff = data[j] - data[i]
            if diff > 0:
                s += 1
            elif diff < 0:
                s -= 1
            # ties contribute 0

    # Tau = S / (n*(n-1)/2)
    n_pairs = n * (n - 1) / 2
    tau = s / n_pairs if n_pairs > 0 else 0.0

    # Approximate p-value using normal distribution
    # Var(S) = n(n-1)(2n+5)/18 (ignoring ties)
    var_s = n * (n - 1) * (2 * n + 5) / 18
    std_s = math.sqrt(var_s) if var_s > 0 else 1.0

    # z-score
    if s > 0:
        z = (s - 1) / std_s
    elif s < 0:
        z = (s + 1) / std_s
    else:
        z = 0

    # Two-tailed p-value from z (approximation using error function)
    # For simplicity, use a rough approximation
    p_value = 2 * (1 - _normal_cdf(abs(z)))

    return tau, p_value


def _normal_cdf(x: float) -> float:
    """Approximate standard normal CDF using error function approximation."""
    # Abramowitz and Stegun approximation
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911

    sign = 1 if x >= 0 else -1
    x = abs(x) / math.sqrt(2)

    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)

    return 0.5 * (1.0 + sign * y)


def extract_ka_metrics(
    experiment_result: Dict,
    baseline_step_records: List[Dict],
) -> KAMetrics:
    """
    Extract K-A metrics from a single experiment's step_records.

    Args:
        experiment_result: Experiment result dict with step_records
        baseline_step_records: BENIGN sovereign step_records for D_t computation

    Returns:
        KAMetrics for this experiment
    """
    step_records = experiment_result.get("step_records", [])
    profile_id = experiment_result.get("profile", "UNKNOWN")
    agent_type = experiment_result.get("agent_type", "UNKNOWN")

    n_steps = len(step_records)
    if n_steps == 0:
        return KAMetrics(
            profile_id=profile_id,
            agent_type=agent_type,
            n_steps=0,
            corr_f_d=None,
            corr_f_d_n=0,
            corr_f_neg_depth=None,
            median_depth_drop=None,
            mann_kendall_tau=None,
            mann_kendall_p=None,
            ops_trend_significant=False,
            mean_f=0.0,
            mean_depth=0.0,
            mean_ops=0.0,
            d_rate=0.0,
            i3_target_rate=0.0,
        )

    # Build baseline lookup: (episode_idx, step_idx) -> record
    baseline_lookup = {}
    for rec in baseline_step_records:
        key = (rec.get("episode_idx"), rec.get("step_idx"))
        baseline_lookup[key] = rec

    # Compute per-step metrics
    f_values = []
    d_values = []
    depth_values = []
    ops_values = []
    i3_target_count = 0

    for step_rec in step_records:
        # F_t
        f_t = compute_friction_scalar(step_rec)
        f_values.append(f_t)

        # depth_t
        depth_t = compute_depth_scalar(step_rec)
        depth_values.append(depth_t)

        # Ops_t
        ops_t = step_rec.get("institution", {}).get("op_count", 0)
        ops_values.append(float(ops_t))

        # D_t (vs baseline)
        key = (step_rec.get("episode_idx"), step_rec.get("step_idx"))
        baseline_rec = baseline_lookup.get(key)
        d_t = compute_d_t(step_rec, baseline_rec)
        d_values.append(float(d_t))

        # I3 target flag
        inst = step_rec.get("institution", {})
        ops = inst.get("ops", [])
        if any(op.get("TargetFlag_I3", False) for op in ops):
            i3_target_count += 1

    # Compute correlations
    corr_f_d = pearson_correlation(f_values, d_values)
    neg_depth = [-d for d in depth_values]
    corr_f_neg_depth = pearson_correlation(f_values, neg_depth)

    # Compute median depth drop (vs baseline)
    baseline_depths = []
    for rec in baseline_step_records:
        baseline_depths.append(compute_depth_scalar(rec))

    if baseline_depths and depth_values:
        baseline_median = sorted(baseline_depths)[len(baseline_depths) // 2]
        current_median = sorted(depth_values)[len(depth_values) // 2]
        median_depth_drop = baseline_median - current_median
    else:
        median_depth_drop = None

    # Mann-Kendall on Ops_t
    tau, p_value = mann_kendall_test(ops_values)
    ops_trend_significant = p_value < 0.10 and abs(tau) > 0.1

    # Summary stats
    mean_f = sum(f_values) / n_steps if n_steps > 0 else 0.0
    mean_depth = sum(depth_values) / n_steps if n_steps > 0 else 0.0
    mean_ops = sum(ops_values) / n_steps if n_steps > 0 else 0.0
    d_rate = sum(d_values) / n_steps if n_steps > 0 else 0.0
    i3_target_rate = i3_target_count / n_steps if n_steps > 0 else 0.0

    return KAMetrics(
        profile_id=profile_id,
        agent_type=agent_type,
        n_steps=n_steps,
        corr_f_d=corr_f_d,
        corr_f_d_n=n_steps,
        corr_f_neg_depth=corr_f_neg_depth,
        median_depth_drop=median_depth_drop,
        mann_kendall_tau=tau,
        mann_kendall_p=p_value,
        ops_trend_significant=ops_trend_significant,
        mean_f=mean_f,
        mean_depth=mean_depth,
        mean_ops=mean_ops,
        d_rate=d_rate,
        i3_target_rate=i3_target_rate,
    )


def extract_all_ka_metrics(results_file: Path) -> Dict[str, KAMetrics]:
    """
    Extract K-A metrics from a full results JSON file.

    Returns dict keyed by "profile_agent" (e.g., "I2_sovereign").
    """
    with open(results_file) as f:
        data = json.load(f)

    experiments = data.get("experiments", [])

    # Find BENIGN sovereign baseline
    baseline_step_records = []
    for exp in experiments:
        if exp.get("profile") == "BENIGN" and exp.get("agent_type") == "sovereign":
            baseline_step_records = exp.get("step_records", [])
            break

    # Extract metrics for each experiment
    metrics = {}
    for exp in experiments:
        profile = exp.get("profile", "UNKNOWN")
        agent = exp.get("agent_type", "UNKNOWN")
        key = f"{profile}_{agent}"

        ka = extract_ka_metrics(exp, baseline_step_records)
        metrics[key] = ka

    return metrics


def print_ka_report(metrics: Dict[str, KAMetrics]):
    """Print formatted K-A metrics report."""
    print("\n" + "=" * 80)
    print("K-A Audit Metrics Report")
    print("=" * 80)

    print("\n### Friction-Decision Correlation (corr(F,D)) ###")
    print(f"{'Experiment':<30} {'corr(F,D)':<12} {'N':<8} {'D_rate':<10}")
    print("-" * 60)
    for key, m in sorted(metrics.items()):
        corr_str = f"{m.corr_f_d:.3f}" if m.corr_f_d is not None else "N/A"
        print(f"{key:<30} {corr_str:<12} {m.corr_f_d_n:<8} {m.d_rate:.2%}")

    print("\n### Simplification Gradient (corr(F,-depth)) ###")
    print(f"{'Experiment':<30} {'corr(F,-d)':<12} {'med_drop':<10} {'mean_depth':<10}")
    print("-" * 62)
    for key, m in sorted(metrics.items()):
        corr_str = f"{m.corr_f_neg_depth:.3f}" if m.corr_f_neg_depth is not None else "N/A"
        drop_str = f"{m.median_depth_drop:.1f}" if m.median_depth_drop is not None else "N/A"
        print(f"{key:<30} {corr_str:<12} {drop_str:<10} {m.mean_depth:.2f}")

    print("\n### Ops Drift (Mann-Kendall tau) ###")
    print(f"{'Experiment':<30} {'tau':<10} {'p-value':<10} {'significant':<12} {'mean_ops':<10}")
    print("-" * 72)
    for key, m in sorted(metrics.items()):
        tau_str = f"{m.mann_kendall_tau:.3f}" if m.mann_kendall_tau is not None else "N/A"
        p_str = f"{m.mann_kendall_p:.3f}" if m.mann_kendall_p is not None else "N/A"
        sig_str = "YES" if m.ops_trend_significant else "no"
        print(f"{key:<30} {tau_str:<10} {p_str:<10} {sig_str:<12} {m.mean_ops:.2f}")

    print("\n### I3 Activation Rate ###")
    print(f"{'Experiment':<30} {'I3 Target %':<12} {'mean_F':<10}")
    print("-" * 52)
    for key, m in sorted(metrics.items()):
        if "I3" in key or "I3B" in key:
            print(f"{key:<30} {m.i3_target_rate:.1%}      {m.mean_f:.2f}")

    print("\n" + "=" * 80)


def main():
    """CLI entry point for K-A extraction."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ka_extractor.py <results_file.json>")
        sys.exit(1)

    results_file = Path(sys.argv[1])
    if not results_file.exists():
        print(f"Error: File not found: {results_file}")
        sys.exit(1)

    print(f"Extracting K-A metrics from: {results_file}")
    metrics = extract_all_ka_metrics(results_file)

    if not metrics:
        print("No step_records found in results. Cannot compute K-A metrics.")
        sys.exit(1)

    print_ka_report(metrics)


if __name__ == "__main__":
    main()
