"""Deterministic agent trace replay benchmark runner.

This module is deliberately replay-focused rather than agentic. It does not
plan, execute tools, call external APIs, score semantics, build embeddings, or
judge with an LLM. It extracts operational continuity fields from checked-in
multi-step agent traces, compacts those fields into a replay-safe form,
reconstructs the state, and derives deterministic metrics from exact field
survival.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from pathlib import Path
from typing import Iterable

if __package__:
    from tests.utils._import_root import ensure_repo_root_on_path
else:
    from _import_root import ensure_repo_root_on_path

ensure_repo_root_on_path()

from src.validation.evidence import EvidenceItem, compute_evidence_survival, exact_normalized_match
from src.validation.replay_failure_classifier import classify_replay_failures, merge_failure_labels

BENCHMARK_NAME = "agent_trace_replay_bench"
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "agent_traces"
DEFAULT_ARTIFACT_PATH = REPO_ROOT / "artifacts" / "agent_trace_replay_results.json"

TRACE_SPECS = (
    {
        "trace": "coding_agent_trace",
        "fixture": "coding_agent_trace.json",
        "evidence": (
            {
                "id": "coding_active_task",
                "kind": "agent_event",
                "locator": "event:active_task",
                "description": "The active coding task must survive replay.",
            },
            {
                "id": "coding_unresolved_blockers",
                "kind": "agent_event",
                "locator": "event:unresolved_blockers",
                "description": "Unresolved blockers must remain visible after replay.",
            },
        ),
    },
    {
        "trace": "ci_failure_trace",
        "fixture": "ci_failure_trace.json",
        "evidence": (
            {
                "id": "ci_constraints",
                "kind": "agent_event",
                "locator": "event:constraints",
                "description": "CI recovery constraints must survive replay.",
            },
            {
                "id": "ci_recovery_actions",
                "kind": "agent_event",
                "locator": "event:recovery_actions",
                "description": "Recovery actions must remain reconstructable.",
            },
        ),
    },
    {
        "trace": "workflow_recovery_trace",
        "fixture": "workflow_recovery_trace.json",
        "evidence": (
            {
                "id": "workflow_tool_sequence",
                "kind": "agent_event",
                "locator": "event:tool_sequence",
                "description": "Tool ordering is evidence for workflow continuity.",
            },
            {
                "id": "workflow_dependencies",
                "kind": "agent_event",
                "locator": "event:dependencies",
                "description": "Dependency records must survive replay.",
            },
        ),
    },
)

OPERATIONAL_FIELDS = (
    "active_task",
    "constraints",
    "architecture_nodes",
    "dependencies",
    "tool_sequence",
    "unresolved_blockers",
    "deployment_requirements",
    "recovery_actions",
)

_SEQUENCE_FIELDS = frozenset({"constraints", "architecture_nodes", "tool_sequence", "unresolved_blockers", "deployment_requirements", "recovery_actions"})
_RECORD_FIELDS = frozenset({"dependencies"})
_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*")
_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class OperationalState:
    """Structured deterministic operational state extracted from one trace."""

    trace: str
    fields: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {"trace": self.trace, "operational_fields": {field: self.fields[field] for field in OPERATIONAL_FIELDS}}


@dataclass(frozen=True, slots=True)
class ReplayRun:
    """Full replay data used by tests; the artifact emits only metrics."""

    artifact_row: dict[str, object]
    original_state: dict[str, object]
    compact_representation: dict[str, object]
    replayed_state: dict[str, object]


def normalize_float(value: float) -> float:
    """Return a finite float rounded for stable benchmark artifacts."""

    if not math.isfinite(value):
        raise ValueError(f"non-finite benchmark value: {value!r}")
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
    """Backward-compatible alias for benchmark artifact serialization."""

    return stable_json_dump(value)


def token_count(text: str) -> int:
    """Count deterministic word-like tokens without model tokenizers."""

    return len(_WORD_RE.findall(text))


def _normalize_text(text: object) -> str:
    return _SPACE_RE.sub(" ", str(text)).strip()


def _evidence_items(spec: dict[str, object]) -> tuple[EvidenceItem, ...]:
    evidence = spec.get("evidence", ())
    assert isinstance(evidence, tuple)
    return tuple(
        EvidenceItem(
            id=str(item["id"]),
            kind=str(item["kind"]),
            locator=str(item["locator"]),
            description=str(item.get("description", "")),
            criticality=str(item.get("criticality", "MEDIUM")),
        )
        for item in evidence
        if isinstance(item, dict)
    )


def _resolve_agent_evidence(
    *,
    original_state: dict[str, object],
    replayed_state: dict[str, object],
    evidence: tuple[EvidenceItem, ...],
) -> tuple[dict[str, object], dict[str, object], tuple[str, ...]]:
    original_fields = original_state["operational_fields"]
    replayed_fields = replayed_state["operational_fields"]
    assert isinstance(original_fields, dict)
    assert isinstance(replayed_fields, dict)

    original_by_id: dict[str, object] = {}
    replayed_by_id: dict[str, object] = {}
    evidence_ids: list[str] = []
    for item in evidence:
        evidence_ids.append(item.id)
        if item.kind != "agent_event" or not item.locator.startswith("event:"):
            continue
        event_name = item.locator.removeprefix("event:")
        if event_name in original_fields:
            original_by_id[item.id] = original_fields[event_name]
        if event_name in replayed_fields:
            replayed_by_id[item.id] = replayed_fields[event_name]

    return original_by_id, replayed_by_id, tuple(evidence_ids)


def _load_fixture(spec: dict[str, object]) -> tuple[dict[str, object], str]:
    path = FIXTURE_ROOT / spec["fixture"]
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw), raw


def _active_task(tasks: Iterable[object]) -> str:
    normalized_tasks = [task for task in tasks if isinstance(task, dict)]
    for status in ("active", "in_progress", "pending", "completed"):
        for task in normalized_tasks:
            if _normalize_text(task.get("status", "")).lower() == status:
                return _normalize_text(f"{task.get('id', '')} {task.get('title', '')} {task.get('details', '')}")
    raise ValueError("trace fixture must include at least one task")


def _string_list(values: Iterable[object]) -> list[str]:
    return [_normalize_text(value) for value in values if _normalize_text(value)]


def _architecture_nodes(values: Iterable[object]) -> list[str]:
    nodes = []
    for value in values:
        if not isinstance(value, dict):
            continue
        node = _normalize_text(value.get("node", ""))
        role = _normalize_text(value.get("role", ""))
        if node and role:
            nodes.append(f"{node}: {role}")
    return sorted(nodes, key=str.lower)


def _dependencies(values: Iterable[object]) -> list[dict[str, str]]:
    dependencies = []
    for value in values:
        if not isinstance(value, dict):
            continue
        record = {
            "detail": _normalize_text(value.get("detail", "")),
            "from": _normalize_text(value.get("from", "")),
            "id": _normalize_text(value.get("id", "")),
            "to": _normalize_text(value.get("to", "")),
            "type": _normalize_text(value.get("type", "")),
        }
        if all(record.values()):
            dependencies.append(record)
    return sorted(dependencies, key=lambda item: (item["id"].lower(), item["from"].lower(), item["to"].lower()))


def _tool_sequence(values: Iterable[object]) -> list[str]:
    calls = [value for value in values if isinstance(value, dict)]
    calls.sort(key=lambda item: int(item.get("index", 0)))
    sequence = []
    for call in calls:
        tool = _normalize_text(call.get("tool", ""))
        command = _normalize_text(call.get("command", ""))
        result = _normalize_text(call.get("result", ""))
        if tool and command and result:
            sequence.append(f"{tool}::{command}::{result}")
    return sequence


def extract_operational_state(trace: dict[str, object]) -> OperationalState:
    """Extract required operational fields with exact field access and sorting."""

    fields: dict[str, object] = {
        "active_task": _active_task(trace.get("tasks", [])),
        "constraints": sorted(_string_list(trace.get("constraints", [])), key=str.lower),
        "architecture_nodes": _architecture_nodes(trace.get("architecture_references", [])),
        "dependencies": _dependencies(trace.get("dependencies", [])),
        "tool_sequence": _tool_sequence(trace.get("tool_calls", [])),
        "unresolved_blockers": sorted(_string_list(trace.get("unresolved_blockers", [])), key=str.lower),
        "deployment_requirements": sorted(_string_list(trace.get("deployment_requirements", [])), key=str.lower),
        "recovery_actions": sorted(_string_list(trace.get("recoveries", [])), key=str.lower),
    }
    return OperationalState(trace=_normalize_text(trace["trace"]), fields=fields)


def compact_operational_state(state: OperationalState) -> dict[str, object]:
    """Build compact replay representation from operational state only."""

    fields = state.fields
    return {
        "f": {
            "a": fields["active_task"],
            "ar": fields["architecture_nodes"],
            "b": fields["unresolved_blockers"],
            "c": fields["constraints"],
            "d": fields["dependencies"],
            "dr": fields["deployment_requirements"],
            "r": fields["recovery_actions"],
            "t": fields["tool_sequence"],
        },
        "v": 1,
        "x": state.trace,
    }


def replay_compact_state(compact: dict[str, object]) -> dict[str, object]:
    """Reconstruct operational state from compact replay keys."""

    compact_fields = compact["f"]
    assert isinstance(compact_fields, dict)
    replayed = {
        "trace": compact["x"],
        "operational_fields": {
            "active_task": compact_fields["a"],
            "architecture_nodes": compact_fields["ar"],
            "constraints": compact_fields["c"],
            "dependencies": compact_fields["d"],
            "deployment_requirements": compact_fields["dr"],
            "recovery_actions": compact_fields["r"],
            "tool_sequence": compact_fields["t"],
            "unresolved_blockers": compact_fields["b"],
        },
    }
    return json.loads(canonical_json(replayed))


def _sequence_survival_rate(original: list[object], replayed: list[object]) -> float:
    if not original:
        return 0.0
    return len([item for item in original if item in replayed]) / len(original)


def _field_survived(field: str, original_value: object, replayed_value: object) -> bool:
    if field == "active_task":
        return bool(original_value) and original_value == replayed_value
    if field in _SEQUENCE_FIELDS and isinstance(original_value, list) and isinstance(replayed_value, list):
        return bool(original_value) and original_value == replayed_value
    if field in _RECORD_FIELDS and isinstance(original_value, list) and isinstance(replayed_value, list):
        return bool(original_value) and original_value == replayed_value
    return False


def validate_replay(
    *,
    trace_name: str,
    raw_trace: str,
    original_state: dict[str, object],
    compact_representation: dict[str, object],
    replayed_state: dict[str, object],
    evidence: tuple[EvidenceItem, ...] = (),
) -> dict[str, object]:
    """Derive deterministic replay metrics from original-vs-replayed state."""

    original_fields = original_state["operational_fields"]
    replayed_fields = replayed_state["operational_fields"]
    assert isinstance(original_fields, dict)
    assert isinstance(replayed_fields, dict)

    surviving_operational_fields = sum(
        1 for field in OPERATIONAL_FIELDS if _field_survived(field, original_fields[field], replayed_fields[field])
    )
    total_operational_fields = len(OPERATIONAL_FIELDS)
    lost_operational_fields = total_operational_fields - surviving_operational_fields

    original_token_count = token_count(raw_trace)
    compact_token_count = token_count(canonical_json(compact_representation))
    replay_token_count = token_count(canonical_json(replayed_state))

    original_evidence, replayed_evidence, evidence_ids = _resolve_agent_evidence(
        original_state=original_state,
        replayed_state=replayed_state,
        evidence=evidence,
    )
    evidence_result = compute_evidence_survival(
        original_events=original_evidence,
        reconstructed_events=replayed_evidence,
        evidence_ids=evidence_ids,
        matches=exact_normalized_match,
        evidence_criticalities={item.id: item.criticality for item in evidence},
    )

    metrics = {
        "blocker_survival_rate": normalize_float(
            _sequence_survival_rate(list(original_fields["unresolved_blockers"]), list(replayed_fields["unresolved_blockers"]))
        ),
        "compact_token_count": compact_token_count,
        "compression_ratio": normalize_float(original_token_count / compact_token_count) if compact_token_count else 0.0,
        "constraint_survival_rate": normalize_float(
            _sequence_survival_rate(list(original_fields["constraints"]), list(replayed_fields["constraints"]))
        ),
        "dependency_survival_rate": normalize_float(
            _sequence_survival_rate(list(original_fields["dependencies"]), list(replayed_fields["dependencies"]))
        ),
        "evidence_survival_rate": evidence_result.evidence_survival_rate,
        "high_critical_evidence_survival_rate": evidence_result.high_critical_evidence_survival_rate,
        "evidence_survived": evidence_result.evidence_survived,
        "evidence_total": evidence_result.evidence_total,
        "has_evidence": evidence_result.has_evidence,
        "operational_drift_rate": normalize_float(lost_operational_fields / total_operational_fields),
        "original_token_count": original_token_count,
        "replay_consistency": normalize_float(surviving_operational_fields / total_operational_fields),
        "replay_token_count": replay_token_count,
        "tool_sequence_survival_rate": normalize_float(
            _sequence_survival_rate(list(original_fields["tool_sequence"]), list(replayed_fields["tool_sequence"]))
        ),
        "trace": trace_name,
    }
    classifier_metrics = {**metrics, "has_high_critical_evidence": evidence_result.has_high_critical_evidence}
    metrics["failure_labels"] = classify_replay_failures(classifier_metrics)
    return metrics


def run_agent_trace_replay() -> list[ReplayRun]:
    """Run all agent trace fixtures in stable benchmark order."""

    runs = []
    for spec in TRACE_SPECS:
        trace, raw_trace = _load_fixture(spec)
        state = extract_operational_state(trace)
        original_state = json.loads(canonical_json(state.as_dict()))
        compact = json.loads(canonical_json(compact_operational_state(state)))
        replayed = replay_compact_state(compact)
        artifact_row = validate_replay(
            trace_name=state.trace,
            raw_trace=raw_trace,
            original_state=original_state,
            compact_representation=compact,
            replayed_state=replayed,
            evidence=_evidence_items(spec),
        )
        runs.append(
            ReplayRun(
                artifact_row=json.loads(canonical_json(artifact_row)),
                original_state=original_state,
                compact_representation=compact,
                replayed_state=replayed,
            )
        )
    return runs


def build_aggregate(traces: list[dict[str, object]]) -> dict[str, object]:
    """Compute deterministic aggregate metrics from trace rows."""

    trace_count = len(traces)
    if trace_count == 0:
        return {
            "avg_blocker_survival_rate": 0.0,
            "avg_compression_ratio": 0.0,
            "avg_constraint_survival_rate": 0.0,
            "avg_dependency_survival_rate": 0.0,
            "avg_evidence_survival_rate": 0.0,
            "avg_high_critical_evidence_survival_rate": 0.0,
            "failure_labels": [],
            "avg_operational_drift_rate": 0.0,
            "avg_replay_consistency": 0.0,
            "avg_tool_sequence_survival_rate": 0.0,
            "trace_count": 0,
        }

    def average(field: str) -> float:
        return normalize_float(sum(float(row[field]) for row in traces) / trace_count)

    return {
        "avg_blocker_survival_rate": average("blocker_survival_rate"),
        "avg_compression_ratio": average("compression_ratio"),
        "avg_constraint_survival_rate": average("constraint_survival_rate"),
        "avg_dependency_survival_rate": average("dependency_survival_rate"),
        "avg_evidence_survival_rate": average("evidence_survival_rate"),
        "avg_high_critical_evidence_survival_rate": average("high_critical_evidence_survival_rate"),
        "failure_labels": merge_failure_labels(traces),
        "avg_operational_drift_rate": average("operational_drift_rate"),
        "avg_replay_consistency": average("replay_consistency"),
        "avg_tool_sequence_survival_rate": average("tool_sequence_survival_rate"),
        "trace_count": trace_count,
    }


def build_agent_trace_replay_artifact() -> dict[str, object]:
    """Build the public agent trace replay benchmark artifact schema."""

    traces = [run.artifact_row for run in run_agent_trace_replay()]
    return {"aggregate": build_aggregate(traces), "benchmark": BENCHMARK_NAME, "traces": traces}


def write_agent_trace_replay_artifact(path: Path = DEFAULT_ARTIFACT_PATH) -> dict[str, object]:
    artifact = build_agent_trace_replay_artifact()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dump(artifact), encoding="utf-8")
    return artifact


if __name__ == "__main__":
    write_agent_trace_replay_artifact()
