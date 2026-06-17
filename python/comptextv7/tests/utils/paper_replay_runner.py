"""Deterministic paper replay benchmark runner.

This module intentionally avoids LLM judging, embeddings, cosine similarity,
external APIs, PDF parsing, and heavyweight dependencies. It extracts operational
state from checked-in paper fixtures, compacts that state into bounded keyword
and entity sets, reconstructs replay state from the compact form, and derives
metrics from deterministic original-vs-replay validation.
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

from src.validation.evidence import EvidenceItem, compute_evidence_survival
from src.validation.replay_failure_classifier import classify_replay_failures, merge_failure_labels

BENCHMARK_NAME = "paper_replay_bench"
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "papers"
DEFAULT_ARTIFACT_PATH = REPO_ROOT / "artifacts" / "paper_replay_results.json"

SECTION_FIELDS = (
    "problem",
    "method",
    "metrics",
    "limitations",
    "deployment_relevance",
)
TEXT_FIELDS = SECTION_FIELDS + ("baselines",)
OPERATIONAL_FIELDS = TEXT_FIELDS + ("entities", "required_entities")

FIELD_KEYWORD_BUDGETS = {
    "problem": 18,
    "method": 22,
    "metrics": 24,
    "limitations": 18,
    "deployment_relevance": 18,
    "baselines": 18,
}
PAPER_FIELD_KEYWORD_BUDGETS = {
    ("self_consolidating", "metrics"): 23,
}
FIELD_SURVIVAL_THRESHOLDS = {
    "problem": 0.60,
    "method": 0.55,
    "metrics": 0.70,
    "limitations": 0.70,
    "deployment_relevance": 0.60,
    "baselines": 0.50,
    "entities": 1.0,
    "required_entities": 1.0,
}

PAPER_SPECS = (
    {
        "paper": "PrefixGuard",
        "paper_id": "prefixguard",
        "fixture": "prefixguard_excerpt.txt",
        "required_entities": ("StepView", "AUPRC", "DFA", "WebArena", "TerminalBench"),
        "evidence": (
            {
                "id": "prefixguard_stepview_method",
                "kind": "paper_sentence",
                "locator": "method:0",
                "description": "StepView canonicalization is central to the method.",
            },
            {
                "id": "prefixguard_auprc_metrics",
                "kind": "paper_sentence",
                "locator": "metrics:0",
                "description": "AUPRC and benchmark coverage define the reported evaluation signal.",
            },
        ),
    },
    {
        "paper": "FATE",
        "paper_id": "fate",
        "fixture": "fate_excerpt.txt",
        "required_entities": (
            "workflow DAG",
            "execution state",
            "model residency",
            "prefix reuse",
            "device reachability",
        ),
        "evidence": (
            {
                "id": "fate_state_aware_method",
                "kind": "paper_sentence",
                "locator": "method:0",
                "description": "The scheduler uses future-state-aware workflow metadata.",
            },
            {
                "id": "fate_residency_metrics",
                "kind": "paper_sentence",
                "locator": "metrics:0",
                "description": "Model residency and reachability are key metrics.",
            },
        ),
    },
    {
        "paper": "Self-Consolidating Language Models",
        "paper_id": "self_consolidating",
        "fixture": "self_consolidating_excerpt.txt",
        "required_entities": ("SCoL", "SQuAD", "LongBench v2", "retrieval", "forgetting"),
        "evidence": (
            {
                "id": "scol_method_update",
                "kind": "paper_sentence",
                "locator": "method:0",
                "description": "Self-consolidation update strategy is core method evidence.",
            },
            {
                "id": "scol_forgetting_limitation",
                "kind": "paper_sentence",
                "locator": "limitations:0",
                "description": "Forgetting risk is an important limitation.",
            },
        ),
    },
)

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*")
_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]?")
_ENTITY_RE = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9]*(?:[-_][A-Z]?[A-Za-z0-9]+)*|[A-Z]{2,}[A-Za-z0-9-]*|[a-z]+\s+DAG|execution\s+state|model\s+residency|prefix\s+reuse|device\s+reachability)\b"
)
_BASELINE_KEYWORDS = (
    "baseline",
    "compares",
    "compare",
    "against",
    "rather than",
    "instead of",
    "retrieval",
    "compression",
    "memory systems",
)
_KEYWORD_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "because",
        "but",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "how",
        "in",
        "include",
        "into",
        "is",
        "it",
        "may",
        "not",
        "of",
        "on",
        "only",
        "or",
        "rather",
        "such",
        "than",
        "that",
        "the",
        "then",
        "this",
        "to",
        "what",
        "when",
        "where",
        "whether",
        "while",
        "with",
    }
)


@dataclass(frozen=True, slots=True)
class OperationalState:
    """Structured deterministic state extracted from one fixture excerpt."""

    paper: str
    paper_id: str
    title: str
    fields: dict[str, str]
    entities: tuple[str, ...]
    required_entities: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        state_fields: dict[str, object] = {field: self.fields[field] for field in TEXT_FIELDS}
        state_fields["entities"] = list(self.entities)
        state_fields["required_entities"] = list(self.required_entities)
        return {
            "paper": self.paper,
            "paper_id": self.paper_id,
            "title": self.title,
            "operational_fields": state_fields,
        }


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
    """Serialize compact JSON with stable numeric precision and key ordering."""

    return json.dumps(
        _normalize_for_json(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def stable_json_dump(value: object) -> str:
    """Serialize pretty, UTF-8 clean, sorted, newline-terminated artifact JSON."""

    return json.dumps(_normalize_for_json(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def artifact_json(value: object) -> str:
    """Backward-compatible alias for stable benchmark artifact serialization."""

    return stable_json_dump(value)


def token_count(text: str) -> int:
    """Count deterministic word-like tokens without model tokenizers."""

    return len(_WORD_RE.findall(text))


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _sentences(text: str) -> tuple[str, ...]:
    return tuple(
        _normalize_text(match.group(0))
        for match in _SENTENCE_RE.finditer(text)
        if match.group(0).strip()
    )


def _ordered_keywords(text: str) -> tuple[str, ...]:
    seen = set()
    ordered = []
    for word in _WORD_RE.findall(text):
        normalized = word.lower()
        if normalized in _KEYWORD_STOP_WORDS or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _keyword_set(text: str) -> tuple[str, ...]:
    return tuple(sorted(_ordered_keywords(text)))


def _limited_keywords(text: str, limit: int) -> tuple[str, ...]:
    return tuple(sorted(_ordered_keywords(text)[:limit]))


def normalized_keyword_overlap(original: str | Iterable[str], replayed: str | Iterable[str]) -> float:
    """Return exact deterministic keyword-set overlap from 0.0 to 1.0."""

    original_text = " ".join(original) if not isinstance(original, str) else original
    replayed_text = " ".join(replayed) if not isinstance(replayed, str) else replayed
    original_keywords = set(_keyword_set(original_text))
    if not original_keywords:
        return 0.0
    replayed_keywords = set(_keyword_set(replayed_text))
    return len(original_keywords & replayed_keywords) / len(original_keywords)


def _extract_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_section = ""
    for line in text.splitlines():
        if line.startswith("SECTION: "):
            current_section = line.removeprefix("SECTION: ").strip()
            sections[current_section] = []
        elif current_section and line.strip():
            sections[current_section].append(line.strip())
    return {field: _normalize_text(" ".join(sections.get(field, ()))) for field in SECTION_FIELDS}


def _extract_baselines(text: str) -> str:
    selected = []
    lowered_keywords = tuple(keyword.lower() for keyword in _BASELINE_KEYWORDS)
    for sentence in _sentences(text):
        lowered_sentence = sentence.lower()
        if any(keyword in lowered_sentence for keyword in lowered_keywords):
            selected.append(sentence)
    return _normalize_text(" ".join(selected))


def _canonical_entity(entity: str) -> str:
    return _normalize_text(entity).strip(".,;:()[]{}")


def _entity_present(entity: str, text: str) -> bool:
    return entity.lower() in text.lower()


def _extract_entities(text: str, required_entities: Iterable[str]) -> tuple[str, ...]:
    entities = {_canonical_entity(entity) for entity in required_entities if _entity_present(entity, text)}
    for match in _ENTITY_RE.finditer(text):
        entity = _canonical_entity(match.group(0))
        if len(entity) > 1 and entity.lower() not in _KEYWORD_STOP_WORDS:
            entities.add(entity)
    return tuple(sorted(entities, key=lambda value: value.lower()))


def _compress_entities(entities: tuple[str, ...], required_entities: tuple[str, ...]) -> tuple[str, ...]:
    required = {_canonical_entity(entity) for entity in required_entities}
    retained = {entity for entity in entities if entity in required}
    optional = [entity for entity in entities if entity not in retained]
    optional_budget = max(1, round(len(optional) * 0.80))
    retained.update(optional[:optional_budget])
    return tuple(sorted(retained, key=lambda value: value.lower()))



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


def _section_sentences(text: str) -> dict[str, tuple[str, ...]]:
    sections: dict[str, list[str]] = {}
    current_section = ""
    for line in text.splitlines():
        if line.startswith("SECTION: "):
            current_section = line.removeprefix("SECTION: ").strip()
            sections[current_section] = []
        elif current_section and line.strip():
            sections[current_section].append(line.strip())
    return {field: tuple(_sentences(" ".join(sections.get(field, ())))) for field in SECTION_FIELDS}


def _resolve_paper_evidence(
    *,
    excerpt: str,
    replayed_state: dict[str, object],
    evidence: tuple[EvidenceItem, ...],
) -> tuple[dict[str, object], dict[str, object], tuple[str, ...]]:
    original_by_id: dict[str, object] = {}
    replayed_by_id: dict[str, object] = {}
    evidence_ids: list[str] = []
    section_sentences = _section_sentences(excerpt)
    replayed_fields = replayed_state["operational_fields"]
    assert isinstance(replayed_fields, dict)

    for item in evidence:
        evidence_ids.append(item.id)
        if item.kind == "paper_line" and item.locator.startswith("line:"):
            line_index = int(item.locator.removeprefix("line:"))
            lines = [line.strip() for line in excerpt.splitlines() if line.strip()]
            if 0 <= line_index < len(lines):
                original_by_id[item.id] = lines[line_index]
            continue

        if item.kind != "paper_sentence" or ":" not in item.locator:
            continue
        section, sentence_index_text = item.locator.split(":", 1)
        sentence_index = int(sentence_index_text)
        sentences = section_sentences.get(section, ())
        if 0 <= sentence_index < len(sentences):
            original_by_id[item.id] = sentences[sentence_index]
        if section in replayed_fields:
            replayed_by_id[item.id] = replayed_fields[section]

    return original_by_id, replayed_by_id, tuple(evidence_ids)


def _paper_evidence_match(original: object, replayed: object) -> bool:
    return normalized_keyword_overlap(str(original), str(replayed)) >= 0.60

def _load_fixture(spec: dict[str, object]) -> str:
    return (FIXTURE_ROOT / str(spec["fixture"])).read_text(encoding="utf-8")


def extract_operational_state(spec: dict[str, object], excerpt: str) -> OperationalState:
    """Extract structured operational fields using headers and exact matching."""

    title = next(
        line.removeprefix("TITLE: ").strip()
        for line in excerpt.splitlines()
        if line.startswith("TITLE: ")
    )
    sections = _extract_sections(excerpt)
    fields = {field: " ".join(_keyword_set(value)) for field, value in sections.items()}
    fields["baselines"] = " ".join(_keyword_set(_extract_baselines(excerpt)))
    required_entities = tuple(
        _canonical_entity(entity)
        for entity in spec["required_entities"]
        if _entity_present(str(entity), excerpt)
    )
    entities = _extract_entities(excerpt, required_entities)
    return OperationalState(
        paper=str(spec["paper"]),
        paper_id=str(spec["paper_id"]),
        title=title,
        fields=fields,
        entities=entities,
        required_entities=tuple(sorted(required_entities, key=lambda value: value.lower())),
    )


def compact_operational_state(state: OperationalState) -> dict[str, object]:
    """Build a compact replay representation from bounded operational state."""

    compact_fields = {
        field: list(
            _limited_keywords(
                state.fields[field],
                PAPER_FIELD_KEYWORD_BUDGETS.get((state.paper_id, field), FIELD_KEYWORD_BUDGETS[field]),
            )
        )
        for field in TEXT_FIELDS
    }
    compact_fields["entities"] = list(_compress_entities(state.entities, state.required_entities))
    compact_fields["required_entities"] = list(state.required_entities)
    return {
        "f": compact_fields,
        "p": state.paper_id,
    }


def replay_compact_state(compact: dict[str, object], original_state: dict[str, object]) -> dict[str, object]:
    """Reconstruct replay state from compact keyword/entity fields."""

    compact_fields = compact["f"]
    assert isinstance(compact_fields, dict)
    replay_fields: dict[str, object] = {
        field: " ".join(str(keyword) for keyword in compact_fields[field]) for field in TEXT_FIELDS
    }
    replay_fields["entities"] = list(compact_fields["entities"])
    replay_fields["required_entities"] = list(compact_fields["required_entities"])
    replayed = {
        "paper": original_state["paper"],
        "paper_id": compact["p"],
        "title": original_state["title"],
        "operational_fields": replay_fields,
    }
    return json.loads(canonical_json(replayed))


def _retention_rate(original_entities: list[str], replayed_entities: list[str]) -> float:
    if not original_entities:
        return 0.0
    replayed = set(replayed_entities)
    return len([entity for entity in original_entities if entity in replayed]) / len(original_entities)


def field_survived(field: str, original_value: object, replayed_value: object) -> bool:
    """Return deterministic field-survival status used by replay consistency."""

    threshold = FIELD_SURVIVAL_THRESHOLDS[field]
    if isinstance(original_value, list) and isinstance(replayed_value, list):
        if field == "required_entities":
            return bool(original_value) and original_value == replayed_value
        return bool(original_value) and _retention_rate(original_value, replayed_value) >= threshold
    if isinstance(original_value, str) and isinstance(replayed_value, str):
        return bool(original_value) and normalized_keyword_overlap(original_value, replayed_value) >= threshold
    return False


def validate_replay(
    *,
    paper: str,
    excerpt: str,
    original_state: dict[str, object],
    compact_representation: dict[str, object],
    replayed_state: dict[str, object],
    evidence: tuple[EvidenceItem, ...] = (),
) -> dict[str, object]:
    """Derive replay metrics from original-vs-replayed operational state."""

    original_fields = original_state["operational_fields"]
    replayed_fields = replayed_state["operational_fields"]
    assert isinstance(original_fields, dict)
    assert isinstance(replayed_fields, dict)

    original_entities = list(original_fields["entities"])
    replayed_entities = list(replayed_fields["entities"])

    section_survivals = [
        field_survived(field, original_fields[field], replayed_fields[field]) for field in TEXT_FIELDS
    ]
    surviving_operational_fields = sum(
        1 for field in OPERATIONAL_FIELDS if field_survived(field, original_fields[field], replayed_fields[field])
    )
    total_operational_fields = len(OPERATIONAL_FIELDS)

    original_token_count = token_count(excerpt)
    compact_text = canonical_json(compact_representation)
    replay_text = canonical_json(replayed_state)
    compact_token_count = token_count(compact_text)
    replay_token_count = token_count(replay_text)

    original_evidence, replayed_evidence, evidence_ids = _resolve_paper_evidence(
        excerpt=excerpt,
        replayed_state=replayed_state,
        evidence=evidence,
    )
    evidence_result = compute_evidence_survival(
        original_events=original_evidence,
        reconstructed_events=replayed_evidence,
        evidence_ids=evidence_ids,
        matches=_paper_evidence_match,
        evidence_criticalities={item.id: item.criticality for item in evidence},
    )

    metrics = {
        "paper": paper,
        "evidence_survival_rate": evidence_result.evidence_survival_rate,
        "high_critical_evidence_survival_rate": evidence_result.high_critical_evidence_survival_rate,
        "evidence_survived": evidence_result.evidence_survived,
        "evidence_total": evidence_result.evidence_total,
        "has_evidence": evidence_result.has_evidence,
        "entity_retention_rate": normalize_float(_retention_rate(original_entities, replayed_entities)),
        "section_survival_rate": normalize_float(sum(section_survivals) / len(section_survivals)),
        "limitation_survival_rate": normalize_float(
            normalized_keyword_overlap(str(original_fields["limitations"]), str(replayed_fields["limitations"]))
        ),
        "metric_survival_rate": normalize_float(
            normalized_keyword_overlap(str(original_fields["metrics"]), str(replayed_fields["metrics"]))
        ),
        "compression_ratio": normalize_float(original_token_count / compact_token_count) if compact_token_count else 0.0,
        "replay_consistency": normalize_float(surviving_operational_fields / total_operational_fields),
        "original_token_count": original_token_count,
        "compact_token_count": compact_token_count,
        "replay_token_count": replay_token_count,
    }
    classifier_metrics = {**metrics, "has_high_critical_evidence": evidence_result.has_high_critical_evidence}
    metrics["failure_labels"] = classify_replay_failures(classifier_metrics)
    return metrics


def run_paper_replay() -> list[ReplayRun]:
    """Run all paper fixtures in stable target-paper order."""

    runs = []
    for spec in PAPER_SPECS:
        excerpt = _load_fixture(spec)
        state = extract_operational_state(spec, excerpt)
        original_state = json.loads(canonical_json(state.as_dict()))
        compact = json.loads(canonical_json(compact_operational_state(state)))
        replayed = replay_compact_state(compact, original_state)
        artifact_row = validate_replay(
            paper=state.paper,
            excerpt=excerpt,
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


def build_aggregate(papers: list[dict[str, object]]) -> dict[str, object]:
    """Compute deterministic aggregate metrics from paper rows."""

    paper_count = len(papers)
    if paper_count == 0:
        return {
            "avg_compression_ratio": 0.0,
            "avg_entity_retention_rate": 0.0,
            "avg_evidence_survival_rate": 0.0,
            "avg_high_critical_evidence_survival_rate": 0.0,
            "failure_labels": [],
            "avg_limitation_survival_rate": 0.0,
            "avg_metric_survival_rate": 0.0,
            "avg_replay_consistency": 0.0,
            "avg_section_survival_rate": 0.0,
            "paper_count": 0,
        }

    def average(field: str) -> float:
        values = [float(row[field]) for row in papers]
        return normalize_float(sum(values) / paper_count)

    return {
        "avg_compression_ratio": average("compression_ratio"),
        "avg_entity_retention_rate": average("entity_retention_rate"),
        "avg_evidence_survival_rate": average("evidence_survival_rate"),
        "avg_high_critical_evidence_survival_rate": average("high_critical_evidence_survival_rate"),
        "failure_labels": merge_failure_labels(papers),
        "avg_limitation_survival_rate": average("limitation_survival_rate"),
        "avg_metric_survival_rate": average("metric_survival_rate"),
        "avg_replay_consistency": average("replay_consistency"),
        "avg_section_survival_rate": average("section_survival_rate"),
        "paper_count": paper_count,
    }


def build_paper_replay_artifact() -> dict[str, object]:
    """Build the public benchmark artifact schema."""

    papers = [run.artifact_row for run in run_paper_replay()]
    return {
        "benchmark": BENCHMARK_NAME,
        "aggregate": build_aggregate(papers),
        "papers": papers,
    }


def write_paper_replay_artifact(path: Path = DEFAULT_ARTIFACT_PATH) -> dict[str, object]:
    artifact = build_paper_replay_artifact()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dump(artifact), encoding="utf-8")
    return artifact


if __name__ == "__main__":
    write_paper_replay_artifact()
