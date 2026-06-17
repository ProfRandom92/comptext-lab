"""Deterministic iterative replay degradation benchmark prototype.

The runner reuses checked-in replay fixtures and existing deterministic replay
helpers. It performs bounded compress/replay cycles, compares each cycle back to
the original fixture state, and emits stable per-cycle degradation metrics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Literal

if __package__:
    from tests.utils._import_root import ensure_repo_root_on_path
else:
    from _import_root import ensure_repo_root_on_path

ensure_repo_root_on_path()

from src.core.adaptive_policy import CompressionProfile, get_params
from src.validation.replay_failure_classifier import REPLAY_FAILURE_LABELS, classify_replay_failures
from tests.utils import agent_trace_replay_runner as agent_runner
from tests.utils import paper_replay_runner as paper_runner

BENCHMARK_NAME = "iterative_replay_degradation_bench"
DEFAULT_MAX_CYCLES = 3
DEFAULT_ARTIFACT_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "iterative_replay_degradation_results.json"
COMPARATIVE_PROFILES: tuple[CompressionProfile, ...] = ("CONSERVATIVE", "BALANCED", "AGGRESSIVE")


@dataclass(frozen=True, slots=True)
class ReplaySensitivityCase:
    """Deterministic fixture-bound parameter surface for replay sensitivity review."""

    case_id: str
    max_context_units: int
    max_families: int
    max_bursts: int
    replay_window_seconds: int
    replay_cycles: int
    compression_budget_scale: float
    trend_expectation: str

    def as_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "compression_budget_scale": normalize_float(self.compression_budget_scale),
            "max_bursts": self.max_bursts,
            "max_context_units": self.max_context_units,
            "max_families": self.max_families,
            "replay_cycles": self.replay_cycles,
            "replay_window_seconds": self.replay_window_seconds,
            "trend_expectation": self.trend_expectation,
        }


SENSITIVITY_CASES: tuple[ReplaySensitivityCase, ...] = (
    ReplaySensitivityCase(
        case_id="baseline_budget",
        max_context_units=96,
        max_families=24,
        max_bursts=24,
        replay_window_seconds=900,
        replay_cycles=3,
        compression_budget_scale=1.0,
        trend_expectation="internal fixture baseline with the widest sensitivity budget",
    ),
    ReplaySensitivityCase(
        case_id="budget_scale_0_75",
        max_context_units=72,
        max_families=18,
        max_bursts=18,
        replay_window_seconds=675,
        replay_cycles=3,
        compression_budget_scale=0.75,
        trend_expectation="moderate budget pressure should not improve degradation metrics over baseline",
    ),
    ReplaySensitivityCase(
        case_id="budget_scale_0_50",
        max_context_units=48,
        max_families=12,
        max_bursts=12,
        replay_window_seconds=450,
        replay_cycles=3,
        compression_budget_scale=0.5,
        trend_expectation="stronger budget pressure should preserve monotonic or explainable degradation",
    ),
    ReplaySensitivityCase(
        case_id="extended_replay_cycles",
        max_context_units=96,
        max_families=24,
        max_bursts=24,
        replay_window_seconds=900,
        replay_cycles=5,
        compression_budget_scale=1.0,
        trend_expectation="cycle-only extension checks whether additional deterministic replays accumulate drift",
    ),
)

FixtureKind = Literal["agent_trace", "paper"]


@dataclass(frozen=True, slots=True)
class IterativeReplayConfig:
    """Bounded deterministic stop/collapse settings."""

    max_cycles: int = DEFAULT_MAX_CYCLES
    min_replay_consistency: float = 0.0
    min_high_critical_evidence_survival_rate: float = 0.0
    max_operational_drift_rate: float = 1.0
    fatal_failure_modes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "fatal_failure_modes": list(self.fatal_failure_modes),
            "max_cycles": self.max_cycles,
            "max_operational_drift_rate": normalize_float(self.max_operational_drift_rate),
            "min_high_critical_evidence_survival_rate": normalize_float(
                self.min_high_critical_evidence_survival_rate
            ),
            "min_replay_consistency": normalize_float(self.min_replay_consistency),
        }


def normalize_float(value: float) -> float:
    """Return a finite float rounded for stable benchmark artifacts."""

    if not math.isfinite(value):
        raise ValueError(f"non-finite iterative replay value: {value!r}")
    return round(float(value), 6)


def _normalize_for_json(value: object) -> object:
    if isinstance(value, float):
        return normalize_float(value)
    if isinstance(value, dict):
        return {str(key): _normalize_for_json(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_normalize_for_json(item) for item in value]
    return value


def canonical_json(value: object) -> str:
    """Serialize compact JSON with stable key ordering and numeric precision."""

    return json.dumps(_normalize_for_json(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_json_dump(value: object) -> str:
    """Serialize pretty, sorted, newline-terminated artifact JSON."""

    return json.dumps(_normalize_for_json(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def artifact_json(value: object) -> str:
    """Backward-compatible alias for stable benchmark artifact serialization."""

    return stable_json_dump(value)


def _validate_config(config: IterativeReplayConfig) -> None:
    if config.max_cycles < 1:
        raise ValueError("max_cycles must be at least 1")
    for field in (
        "min_replay_consistency",
        "min_high_critical_evidence_survival_rate",
        "max_operational_drift_rate",
    ):
        value = getattr(config, field)
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{field} must be between 0.0 and 1.0")


def _failure_mode_counts(failure_labels: list[str]) -> dict[str, int]:
    label_set = set(failure_labels)
    return {label: (1 if label in label_set else 0) for label in REPLAY_FAILURE_LABELS}


def _cycle_metrics(row: dict[str, object], cycle: int) -> dict[str, object]:
    operational_drift_rate = float(row.get("operational_drift_rate", 1.0 - float(row["replay_consistency"])))
    classifier_metrics = {
        **row,
        "blocker_survival_rate": row.get("blocker_survival_rate", 1.0),
        "constraint_survival_rate": row.get("constraint_survival_rate", 1.0),
        "operational_drift_rate": operational_drift_rate,
        "has_high_critical_evidence": bool(row.get("has_high_critical_evidence", False)),
    }
    failure_labels = classify_replay_failures(classifier_metrics)
    return {
        "blocker_survival_rate": normalize_float(float(classifier_metrics["blocker_survival_rate"])),
        "constraint_survival_rate": normalize_float(float(classifier_metrics["constraint_survival_rate"])),
        "cycle": cycle,
        "evidence_survival_rate": normalize_float(float(row["evidence_survival_rate"])),
        "failure_labels": failure_labels,
        "failure_mode_counts": _failure_mode_counts(failure_labels),
        "has_high_critical_evidence": bool(classifier_metrics["has_high_critical_evidence"]),
        "high_critical_evidence_survival_rate": normalize_float(
            float(row["high_critical_evidence_survival_rate"])
        ),
        "operational_drift_rate": normalize_float(operational_drift_rate),
        "replay_consistency": normalize_float(float(row["replay_consistency"])),
    }


def _profile_limit(length: int, profile: CompressionProfile, budget_name: Literal["max_families", "max_bursts"]) -> int:
    """Return a deterministic retained-item count for a compression profile."""

    if length <= 0:
        return 0
    profile_budget = getattr(get_params(profile), budget_name)
    baseline_budget = getattr(get_params("CONSERVATIVE"), budget_name)
    return min(length, max(1, math.ceil(length * profile_budget / baseline_budget)))


def _profiled_list(values: object, profile: CompressionProfile, budget_name: Literal["max_families", "max_bursts"]) -> object:
    if not isinstance(values, list):
        return values
    return values[: _profile_limit(len(values), profile, budget_name)]


def apply_compression_profile_to_compact(
    compact: dict[str, object],
    *,
    fixture_kind: FixtureKind,
    profile: CompressionProfile,
) -> dict[str, object]:
    """Apply deterministic profile budgets to an existing compact replay payload.

    The default iterative runner remains unchanged; comparative mode uses this
    fixture-bound pruning layer to evaluate how the checked-in replay fixtures
    degrade under progressively smaller profile budgets.
    """

    if profile == "CONSERVATIVE":
        return json.loads(canonical_json(compact))

    profiled = json.loads(canonical_json(compact))
    fields = profiled.get("f")
    assert isinstance(fields, dict)

    if fixture_kind == "agent_trace":
        for key, value in list(fields.items()):
            if key == "t":
                fields[key] = _profiled_list(value, profile, "max_bursts")
            elif key != "a":
                fields[key] = _profiled_list(value, profile, "max_families")
    else:
        for key, value in list(fields.items()):
            if key != "required_entities":
                fields[key] = _profiled_list(value, profile, "max_families")

    return json.loads(canonical_json(profiled))


def _scaled_limit(value: int, scale: float) -> int:
    return max(0, math.floor(value * scale))


def _validate_sensitivity_case(sensitivity_case: ReplaySensitivityCase) -> None:
    if sensitivity_case.replay_cycles < 1:
        raise ValueError("replay_cycles must be at least 1")
    if (
        not math.isfinite(sensitivity_case.compression_budget_scale)
        or sensitivity_case.compression_budget_scale <= 0.0
    ):
        raise ValueError("compression_budget_scale must be finite and positive")
    for field in (
        "max_context_units",
        "max_families",
        "max_bursts",
        "replay_window_seconds",
    ):
        if getattr(sensitivity_case, field) < 0:
            raise ValueError(f"{field} must be non-negative")


def _limit_list(values: object, limit: int) -> object:
    if not isinstance(values, list):
        return values
    return values[: max(0, limit)]


def _apply_context_unit_limit(fields: dict[str, object], max_context_units: int) -> None:
    remaining = max_context_units
    for key in sorted(fields):
        value = fields[key]
        if not isinstance(value, list):
            continue
        if remaining <= 0:
            fields[key] = []
            continue
        fields[key] = value[:remaining]
        remaining -= len(fields[key])


def apply_sensitivity_case_to_compact(
    compact: dict[str, object],
    *,
    fixture_kind: FixtureKind,
    sensitivity_case: ReplaySensitivityCase,
) -> dict[str, object]:
    """Apply deterministic replay/compression sensitivity budgets to a compact payload."""

    _validate_sensitivity_case(sensitivity_case)
    adjusted = json.loads(canonical_json(compact))
    fields = adjusted.get("f")
    assert isinstance(fields, dict)

    family_limit = _scaled_limit(sensitivity_case.max_families, sensitivity_case.compression_budget_scale)
    burst_limit = _scaled_limit(sensitivity_case.max_bursts, sensitivity_case.compression_budget_scale)
    context_limit = _scaled_limit(sensitivity_case.max_context_units, sensitivity_case.compression_budget_scale)
    window_burst_limit = _scaled_limit(
        burst_limit,
        min(1.0, sensitivity_case.replay_window_seconds / get_params("CONSERVATIVE").window_seconds),
    )

    if fixture_kind == "agent_trace":
        for key, value in list(fields.items()):
            if key == "t":
                fields[key] = _limit_list(value, min(burst_limit, window_burst_limit))
            elif key != "a":
                fields[key] = _limit_list(value, family_limit)
    else:
        for key, value in list(fields.items()):
            fields[key] = _limit_list(value, family_limit)

    _apply_context_unit_limit(fields, context_limit)
    return json.loads(canonical_json(adjusted))

def _collapse_reason(cycle: dict[str, object], config: IterativeReplayConfig) -> str | None:
    labels = cycle["failure_labels"]
    assert isinstance(labels, list)
    for label in config.fatal_failure_modes:
        if label in labels:
            return f"fatal_failure_mode:{label}"
    if float(cycle["replay_consistency"]) < config.min_replay_consistency:
        return "min_replay_consistency"
    if (
        bool(cycle["has_high_critical_evidence"])
        and float(cycle["high_critical_evidence_survival_rate"])
        < config.min_high_critical_evidence_survival_rate
    ):
        return "min_high_critical_evidence_survival_rate"
    if float(cycle["operational_drift_rate"]) > config.max_operational_drift_rate:
        return "max_operational_drift_rate"
    return None


def _agent_state_from_replayed(replayed_state: dict[str, object]) -> agent_runner.OperationalState:
    fields = replayed_state["operational_fields"]
    assert isinstance(fields, dict)
    return agent_runner.OperationalState(trace=str(replayed_state["trace"]), fields=fields)


def _paper_state_from_replayed(replayed_state: dict[str, object]) -> paper_runner.OperationalState:
    fields = replayed_state["operational_fields"]
    assert isinstance(fields, dict)
    return paper_runner.OperationalState(
        paper=str(replayed_state["paper"]),
        paper_id=str(replayed_state["paper_id"]),
        title=str(replayed_state["title"]),
        fields={field: str(fields[field]) for field in paper_runner.TEXT_FIELDS},
        entities=tuple(str(entity) for entity in fields["entities"]),
        required_entities=tuple(str(entity) for entity in fields["required_entities"]),
    )


def _run_agent_case(
    spec: dict[str, object],
    config: IterativeReplayConfig,
    profile: CompressionProfile | None = None,
    sensitivity_case: ReplaySensitivityCase | None = None,
) -> dict[str, object]:
    trace, raw_trace = agent_runner._load_fixture(spec)
    original = agent_runner.extract_operational_state(trace)
    original_state = json.loads(agent_runner.canonical_json(original.as_dict()))
    evidence = agent_runner._evidence_items(spec)
    current_state = original
    cycles: list[dict[str, object]] = []
    collapsed = False
    collapse_cycle: int | None = None
    stop_reason = "max_cycles"

    for cycle_index in range(1, config.max_cycles + 1):
        compact = json.loads(agent_runner.canonical_json(agent_runner.compact_operational_state(current_state)))
        if profile is not None:
            compact = apply_compression_profile_to_compact(compact, fixture_kind="agent_trace", profile=profile)
        if sensitivity_case is not None:
            compact = apply_sensitivity_case_to_compact(
                compact,
                fixture_kind="agent_trace",
                sensitivity_case=sensitivity_case,
            )
        replayed = agent_runner.replay_compact_state(compact)
        row = agent_runner.validate_replay(
            trace_name=original.trace,
            raw_trace=raw_trace,
            original_state=original_state,
            compact_representation=compact,
            replayed_state=replayed,
            evidence=evidence,
        )
        cycle = _cycle_metrics(row, cycle_index)
        cycles.append(cycle)
        reason = _collapse_reason(cycle, config)
        if reason is not None:
            collapsed = True
            collapse_cycle = cycle_index
            stop_reason = reason
            break
        current_state = _agent_state_from_replayed(replayed)

    return json.loads(
        canonical_json(
            {
                "collapse_cycle": collapse_cycle,
                "collapsed": collapsed,
                "cycles": cycles,
                "fixture_id": original.trace,
                "fixture_kind": "agent_trace",
                "stop_reason": stop_reason,
            }
        )
    )


def _run_paper_case(
    spec: dict[str, object],
    config: IterativeReplayConfig,
    profile: CompressionProfile | None = None,
    sensitivity_case: ReplaySensitivityCase | None = None,
) -> dict[str, object]:
    excerpt = paper_runner._load_fixture(spec)
    original = paper_runner.extract_operational_state(spec, excerpt)
    original_state = json.loads(paper_runner.canonical_json(original.as_dict()))
    evidence = paper_runner._evidence_items(spec)
    current_state = original
    cycles: list[dict[str, object]] = []
    collapsed = False
    collapse_cycle: int | None = None
    stop_reason = "max_cycles"

    for cycle_index in range(1, config.max_cycles + 1):
        compact = json.loads(paper_runner.canonical_json(paper_runner.compact_operational_state(current_state)))
        if profile is not None:
            compact = apply_compression_profile_to_compact(compact, fixture_kind="paper", profile=profile)
        if sensitivity_case is not None:
            compact = apply_sensitivity_case_to_compact(
                compact,
                fixture_kind="paper",
                sensitivity_case=sensitivity_case,
            )
        replayed = paper_runner.replay_compact_state(compact, original_state)
        row = paper_runner.validate_replay(
            paper=original.paper,
            excerpt=excerpt,
            original_state=original_state,
            compact_representation=compact,
            replayed_state=replayed,
            evidence=evidence,
        )
        cycle = _cycle_metrics(row, cycle_index)
        cycles.append(cycle)
        reason = _collapse_reason(cycle, config)
        if reason is not None:
            collapsed = True
            collapse_cycle = cycle_index
            stop_reason = reason
            break
        current_state = _paper_state_from_replayed(replayed)

    return json.loads(
        canonical_json(
            {
                "collapse_cycle": collapse_cycle,
                "collapsed": collapsed,
                "cycles": cycles,
                "fixture_id": original.paper_id,
                "fixture_kind": "paper",
                "stop_reason": stop_reason,
            }
        )
    )


def run_iterative_replay_degradation(
    *,
    config: IterativeReplayConfig | None = None,
    fixture_kinds: tuple[FixtureKind, ...] = ("agent_trace", "paper"),
    profile: CompressionProfile | None = None,
    sensitivity_case: ReplaySensitivityCase | None = None,
) -> list[dict[str, object]]:
    """Run bounded iterative replay cycles over existing checked-in fixtures."""

    resolved_config = config or IterativeReplayConfig()
    _validate_config(resolved_config)
    runs: list[dict[str, object]] = []
    if "agent_trace" in fixture_kinds:
        runs.extend(
            _run_agent_case(spec, resolved_config, profile, sensitivity_case)
            for spec in agent_runner.TRACE_SPECS
        )
    if "paper" in fixture_kinds:
        runs.extend(
            _run_paper_case(spec, resolved_config, profile, sensitivity_case)
            for spec in paper_runner.PAPER_SPECS
        )
    return runs


def build_iterative_replay_degradation_artifact(
    *,
    config: IterativeReplayConfig | None = None,
    fixture_kinds: tuple[FixtureKind, ...] = ("agent_trace", "paper"),
) -> dict[str, object]:
    """Build the public iterative replay degradation artifact in memory."""

    resolved_config = config or IterativeReplayConfig()
    _validate_config(resolved_config)
    runs = run_iterative_replay_degradation(config=resolved_config, fixture_kinds=fixture_kinds)
    return json.loads(
        canonical_json(
            {
                "benchmark": BENCHMARK_NAME,
                "config": resolved_config.as_dict(),
                "runs": runs,
                "sensitivity_analysis": build_replay_sensitivity_analysis_artifact(
                    fixture_kinds=fixture_kinds
                ),
            }
        )
    )


def aggregate_replay_degradation_runs(runs: list[dict[str, object]]) -> dict[str, object]:
    """Compute deterministic comparative aggregate fields for a set of runs."""

    total_fixtures = len(runs)
    collapsed_fixtures = sum(1 for run in runs if bool(run.get("collapsed", False)))
    collapse_rate = normalize_float(collapsed_fixtures / total_fixtures) if total_fixtures else 0.0
    final_cycles = [run["cycles"][-1] for run in runs if isinstance(run.get("cycles"), list) and run["cycles"]]

    def average(field: str) -> float | None:
        values = [float(cycle[field]) for cycle in final_cycles if isinstance(cycle.get(field), int | float)]
        return normalize_float(sum(values) / len(values)) if values else None

    failure_counts = {label: 0 for label in REPLAY_FAILURE_LABELS}
    for cycle in final_cycles:
        counts = cycle.get("failure_mode_counts", {})
        if not isinstance(counts, dict):
            continue
        for label in REPLAY_FAILURE_LABELS:
            count = counts.get(label, 0)
            failure_counts[label] += count if isinstance(count, int) and not isinstance(count, bool) else 0

    return {
        "aggregated_failure_labels": [label for label in REPLAY_FAILURE_LABELS if failure_counts[label] > 0],
        "average_evidence_survival_rate": average("evidence_survival_rate"),
        "average_operational_drift_rate": average("operational_drift_rate"),
        "average_replay_consistency": average("replay_consistency"),
        "collapse_rate": collapse_rate,
    }


def sensitivity_aggregate_from_runs(runs: list[dict[str, object]]) -> dict[str, object]:
    """Compute reviewer-facing sensitivity metrics using stable field names."""

    aggregate = aggregate_replay_degradation_runs(runs)
    return {
        "aggregated_failure_labels": aggregate["aggregated_failure_labels"],
        "collapse_rate": aggregate["collapse_rate"],
        "evidence_survival_rate": aggregate["average_evidence_survival_rate"],
        "operational_drift_rate": aggregate["average_operational_drift_rate"],
        "replay_consistency": aggregate["average_replay_consistency"],
    }


def final_failure_labels_by_fixture(runs: list[dict[str, object]]) -> dict[str, list[str]]:
    """Return compact final-cycle failure labels keyed by deterministic fixture id."""

    labels_by_fixture: dict[str, list[str]] = {}
    for run in sorted(
        runs,
        key=lambda item: (str(item.get("fixture_kind", "")), str(item.get("fixture_id", ""))),
    ):
        cycles = run.get("cycles", [])
        if not isinstance(cycles, list) or not cycles:
            continue
        final_cycle = cycles[-1]
        if not isinstance(final_cycle, dict):
            continue
        raw_labels = final_cycle.get("failure_labels", [])
        if not isinstance(raw_labels, list):
            raw_labels = []
        labels_by_fixture[str(run.get("fixture_id", ""))] = [
            label for label in REPLAY_FAILURE_LABELS if label in raw_labels
        ]
    return labels_by_fixture


def build_replay_sensitivity_analysis_artifact(
    *,
    fixture_kinds: tuple[FixtureKind, ...] = ("agent_trace", "paper"),
    sensitivity_cases: tuple[ReplaySensitivityCase, ...] = SENSITIVITY_CASES,
) -> dict[str, object]:
    """Build an additive deterministic sensitivity-analysis surface."""

    cases = []
    for case_order, sensitivity_case in enumerate(sensitivity_cases, start=1):
        _validate_sensitivity_case(sensitivity_case)
        config = IterativeReplayConfig(max_cycles=sensitivity_case.replay_cycles)
        _validate_config(config)
        runs = run_iterative_replay_degradation(
            config=config,
            fixture_kinds=fixture_kinds,
            sensitivity_case=sensitivity_case,
        )
        cases.append(
            {
                "aggregate": sensitivity_aggregate_from_runs(runs),
                "case_order": case_order,
                "final_failure_labels_by_fixture": final_failure_labels_by_fixture(runs),
                "fixture_count": len(runs),
                "parameters": sensitivity_case.as_dict(),
            }
        )
    return json.loads(
        canonical_json(
            {
                "benchmark": f"{BENCHMARK_NAME}_sensitivity_analysis",
                "cases": cases,
                "scope": "fixture-bound deterministic replay sensitivity analysis",
            }
        )
    )

def build_comparative_replay_degradation_artifact(
    *,
    config: IterativeReplayConfig | None = None,
    fixture_kinds: tuple[FixtureKind, ...] = ("agent_trace", "paper"),
) -> dict[str, object]:
    """Build a deterministic fixture-bound profile comparison artifact."""

    resolved_config = config or IterativeReplayConfig()
    _validate_config(resolved_config)
    profiles = []
    for profile in COMPARATIVE_PROFILES:
        runs = run_iterative_replay_degradation(
            config=resolved_config,
            fixture_kinds=fixture_kinds,
            profile=profile,
        )
        profiles.append(
            {
                "aggregate": aggregate_replay_degradation_runs(runs),
                "compression_params": asdict(get_params(profile)),
                "profile": profile,
                "runs": runs,
            }
        )
    return json.loads(
        canonical_json(
            {
                "benchmark": f"{BENCHMARK_NAME}_profile_comparison",
                "config": resolved_config.as_dict(),
                "profiles": profiles,
            }
        )
    )


def write_iterative_replay_degradation_artifact(path: Path = DEFAULT_ARTIFACT_PATH) -> dict[str, object]:
    """Opt-in writer for local/CI runs; tests do not call this by default."""

    artifact = build_iterative_replay_degradation_artifact()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dump(artifact), encoding="utf-8")
    return artifact


if __name__ == "__main__":
    write_iterative_replay_degradation_artifact()
