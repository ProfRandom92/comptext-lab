from __future__ import annotations

from src.core.adaptive_policy import CompressionParams, ReplayMetrics, get_params, select_profile
from src.validation.evidence import EvidenceItem, compute_evidence_survival, exact_normalized_match
from src.validation.replay_failure_classifier import (
    BLOCKER_DETACHMENT,
    CONSTRAINT_DRIFT,
    EVIDENCE_LOSS,
    HIGH_CRITICAL_EVIDENCE_LOSS,
    classify_replay_failures,
)
from tests.utils.agent_trace_replay_runner import _resolve_agent_evidence
from tests.utils.paper_replay_runner import _paper_evidence_match, _resolve_paper_evidence


def test_paper_evidence_survival_rate_on_synthetic_fixture() -> None:
    excerpt = """PAPER_ID: synthetic
TITLE: Synthetic Paper

SECTION: problem
The system must preserve explicit audit evidence during replay.

SECTION: method
Deterministic compression stores audit evidence and replay state.

SECTION: metrics
Evidence survival is measured without model judging.

SECTION: limitations
Missing annotated facts must reduce the evidence metric.

SECTION: deployment_relevance
Reviewers can inspect deterministic artifacts.
"""
    replayed_state = {
        "operational_fields": {
            "method": "deterministic compression stores audit evidence replay state",
            "metrics": "unrelated latency only",
        }
    }
    evidence = (
        EvidenceItem("method_evidence", "paper_sentence", "method:0"),
        EvidenceItem("metrics_evidence", "paper_sentence", "metrics:0"),
    )

    original, replayed, evidence_ids = _resolve_paper_evidence(
        excerpt=excerpt,
        replayed_state=replayed_state,
        evidence=evidence,
    )
    result = compute_evidence_survival(
        original_events=original,
        reconstructed_events=replayed,
        evidence_ids=evidence_ids,
        matches=_paper_evidence_match,
    )

    assert result.has_evidence is True
    assert result.evidence_total == 2
    assert result.evidence_survived == 1
    assert result.evidence_survival_rate == 0.5
    assert result.missing_evidence_ids == ("metrics_evidence",)


def test_agent_evidence_survival_rate_on_synthetic_trace() -> None:
    original_state = {
        "operational_fields": {
            "active_task": "task-002 Add deterministic replay evidence",
            "unresolved_blockers": ["Confirm pytest remains green"],
        }
    }
    replayed_state = {
        "operational_fields": {
            "active_task": "task-002 Add deterministic replay evidence",
            "unresolved_blockers": [],
        }
    }
    evidence = (
        EvidenceItem("active_task", "agent_event", "event:active_task"),
        EvidenceItem("blockers", "agent_event", "event:unresolved_blockers"),
    )

    original, replayed, evidence_ids = _resolve_agent_evidence(
        original_state=original_state,
        replayed_state=replayed_state,
        evidence=evidence,
    )
    result = compute_evidence_survival(
        original_events=original,
        reconstructed_events=replayed,
        evidence_ids=evidence_ids,
        matches=exact_normalized_match,
    )

    assert result.has_evidence is True
    assert result.evidence_total == 2
    assert result.evidence_survived == 1
    assert result.evidence_survival_rate == 0.5
    assert result.missing_evidence_ids == ("blockers",)


def test_empty_evidence_set_is_marked_not_applicable() -> None:
    result = compute_evidence_survival(
        original_events={},
        reconstructed_events={},
        evidence_ids=(),
    )

    assert result.has_evidence is False
    assert result.evidence_total == 0
    assert result.evidence_survived == 0
    assert result.evidence_survival_rate == 0.0
    assert result.high_critical_evidence_survival_rate == 0.0
    assert result.has_high_critical_evidence is False
    assert result.missing_evidence_ids == ()


def test_select_profile_ignores_evidence_rate_when_no_evidence_is_annotated() -> None:
    metrics = ReplayMetrics(
        compression_ratio=1.35,
        reduction_percent=26.0,
        replay_consistency=1.0,
        constraint_survival=1.0,
        blocker_survival=1.0,
        evidence_survival_rate=0.0,
        has_evidence=False,
    )

    assert select_profile(metrics) == "AGGRESSIVE"


def test_select_profile_allows_aggressive_when_quality_is_high_and_reduction_modest() -> None:
    metrics = ReplayMetrics(
        compression_ratio=1.35,
        reduction_percent=26.0,
        replay_consistency=1.0,
        constraint_survival=1.0,
        blocker_survival=1.0,
        evidence_survival_rate=1.0,
        has_evidence=True,
    )

    assert select_profile(metrics) == "AGGRESSIVE"


def test_select_profile_falls_back_to_conservative_on_evidence_loss() -> None:
    metrics = ReplayMetrics(
        compression_ratio=1.35,
        reduction_percent=26.0,
        replay_consistency=1.0,
        constraint_survival=1.0,
        blocker_survival=1.0,
        evidence_survival_rate=0.90,
        has_evidence=True,
    )

    assert select_profile(metrics) == "CONSERVATIVE"


def test_high_critical_evidence_survival_rate_tracks_high_loss() -> None:
    result = compute_evidence_survival(
        original_events={"critical": "preserve this", "medium": "can degrade"},
        reconstructed_events={"critical": "lost", "medium": "can degrade"},
        evidence_ids=("critical", "medium"),
        evidence_criticalities={"critical": "HIGH", "medium": "MEDIUM"},
    )

    assert result.has_evidence is True
    assert result.has_high_critical_evidence is True
    assert result.evidence_total == 2
    assert result.evidence_survived == 1
    assert result.evidence_survival_rate == 0.5
    assert result.high_critical_evidence_survival_rate == 0.0
    assert result.missing_evidence_ids == ("critical",)


def test_high_critical_evidence_survival_rate_is_zero_when_no_high_evidence() -> None:
    result = compute_evidence_survival(
        original_events={"low": "preserved", "medium": "preserved"},
        reconstructed_events={"low": "preserved", "medium": "preserved"},
        evidence_ids=("low", "medium"),
        evidence_criticalities={"low": "LOW", "medium": "MEDIUM"},
    )

    assert result.has_evidence is True
    assert result.has_high_critical_evidence is False
    assert result.evidence_survival_rate == 1.0
    assert result.high_critical_evidence_survival_rate == 0.0


def test_evidence_item_defaults_to_medium_for_backward_compatible_fixtures() -> None:
    item = EvidenceItem("legacy", "agent_event", "event:active_task")
    result = compute_evidence_survival(
        original_events={"legacy": "same"},
        reconstructed_events={"legacy": "same"},
        evidence_ids=(item.id,),
        evidence_criticalities={item.id: item.criticality},
    )

    assert item.criticality == "MEDIUM"
    assert result.has_high_critical_evidence is False
    assert result.high_critical_evidence_survival_rate == 0.0


def test_select_profile_falls_back_to_conservative_on_high_critical_evidence_loss() -> None:
    metrics = ReplayMetrics(
        compression_ratio=1.35,
        reduction_percent=26.0,
        replay_consistency=1.0,
        constraint_survival=1.0,
        blocker_survival=1.0,
        evidence_survival_rate=0.99,
        has_evidence=True,
        high_critical_evidence_survival_rate=0.0,
        has_high_critical_evidence=True,
    )

    assert select_profile(metrics) == "CONSERVATIVE"


def test_select_profile_ignores_high_rate_when_no_high_evidence_is_annotated() -> None:
    metrics = ReplayMetrics(
        compression_ratio=1.35,
        reduction_percent=26.0,
        replay_consistency=1.0,
        constraint_survival=1.0,
        blocker_survival=1.0,
        evidence_survival_rate=1.0,
        has_evidence=True,
        high_critical_evidence_survival_rate=0.0,
        has_high_critical_evidence=False,
    )

    assert select_profile(metrics) == "AGGRESSIVE"


def test_select_profile_uses_balanced_when_quality_is_good_but_already_compressed() -> None:
    metrics = ReplayMetrics(
        compression_ratio=2.25,
        reduction_percent=55.5,
        replay_consistency=1.0,
        constraint_survival=1.0,
        blocker_survival=1.0,
        evidence_survival_rate=1.0,
        has_evidence=True,
    )

    assert select_profile(metrics) == "BALANCED"


def test_get_params_returns_stable_profile_parameters() -> None:
    assert get_params("CONSERVATIVE") == CompressionParams(
        window_seconds=900,
        max_families=12,
        max_bursts=24,
        use_sparse_micro_frames=False,
    )
    assert get_params("BALANCED") == CompressionParams(
        window_seconds=600,
        max_families=8,
        max_bursts=16,
        use_sparse_micro_frames=True,
    )
    assert get_params("AGGRESSIVE") == CompressionParams(
        window_seconds=300,
        max_families=5,
        max_bursts=10,
        use_sparse_micro_frames=True,
    )


def test_replay_failure_classifier_returns_no_labels_for_clean_metrics() -> None:
    assert classify_replay_failures(
        {
            "has_evidence": True,
            "evidence_survived": 2,
            "evidence_total": 2,
            "evidence_survival_rate": 1.0,
            "has_high_critical_evidence": True,
            "high_critical_evidence_survival_rate": 1.0,
            "constraint_survival_rate": 1.0,
            "blocker_survival_rate": 1.0,
        }
    ) == []


def test_replay_failure_classifier_labels_evidence_loss() -> None:
    assert classify_replay_failures(
        {
            "has_evidence": True,
            "evidence_survived": 1,
            "evidence_total": 2,
            "evidence_survival_rate": 0.5,
            "constraint_survival_rate": 1.0,
            "blocker_survival_rate": 1.0,
        }
    ) == [EVIDENCE_LOSS]


def test_replay_failure_classifier_labels_high_critical_evidence_loss() -> None:
    assert classify_replay_failures(
        {
            "has_evidence": True,
            "evidence_survived": 1,
            "evidence_total": 2,
            "evidence_survival_rate": 0.5,
            "has_high_critical_evidence": True,
            "high_critical_evidence_survival_rate": 0.0,
            "constraint_survival_rate": 1.0,
            "blocker_survival_rate": 1.0,
        }
    ) == [EVIDENCE_LOSS, HIGH_CRITICAL_EVIDENCE_LOSS]


def test_replay_failure_classifier_labels_constraint_drift() -> None:
    assert classify_replay_failures(
        {
            "has_evidence": False,
            "evidence_survival_rate": 0.0,
            "constraint_survival_rate": 0.75,
            "blocker_survival_rate": 1.0,
        }
    ) == [CONSTRAINT_DRIFT]


def test_replay_failure_classifier_labels_blocker_detachment() -> None:
    assert classify_replay_failures(
        {
            "has_evidence": False,
            "evidence_survival_rate": 0.0,
            "constraint_survival_rate": 1.0,
            "blocker_survival_rate": 0.5,
        }
    ) == [BLOCKER_DETACHMENT]
