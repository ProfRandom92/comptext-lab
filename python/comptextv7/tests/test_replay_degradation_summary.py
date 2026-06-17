from src.validation.replay_failure_classifier import (
    BLOCKER_DETACHMENT,
    CONSTRAINT_DRIFT,
    EVIDENCE_LOSS,
    HIGH_CRITICAL_EVIDENCE_LOSS,
    REPLAY_FAILURE_LABELS,
)
from tests.utils.replay_degradation_summary import (
    SEVERITY_CRITICAL,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    classify_replay_degradation_severity,
    render_replay_degradation_summary,
    summarize_replay_degradation_artifact,
)


def _counts(*labels: str) -> dict[str, int]:
    label_set = set(labels)
    return {label: (1 if label in label_set else 0) for label in REPLAY_FAILURE_LABELS}


def _artifact() -> dict[str, object]:
    return {
        "benchmark": "iterative_replay_degradation_bench",
        "config": {"max_cycles": 3},
        "runs": [
            {
                "collapse_cycle": None,
                "collapsed": False,
                "cycles": [
                    {
                        "cycle": 1,
                        "failure_labels": [],
                        "failure_mode_counts": _counts(),
                        "operational_drift_rate": 0.0,
                        "replay_consistency": 1.0,
                    },
                    {
                        "cycle": 2,
                        "failure_labels": [CONSTRAINT_DRIFT],
                        "failure_mode_counts": _counts(CONSTRAINT_DRIFT),
                        "operational_drift_rate": 0.25,
                        "replay_consistency": 0.75,
                    },
                ],
                "fixture_id": "zeta_trace",
                "fixture_kind": "agent_trace",
                "stop_reason": "max_cycles",
            },
            {
                "collapse_cycle": 3,
                "collapsed": True,
                "cycles": [
                    {
                        "cycle": 3,
                        "failure_labels": [EVIDENCE_LOSS, HIGH_CRITICAL_EVIDENCE_LOSS],
                        "failure_mode_counts": _counts(EVIDENCE_LOSS, HIGH_CRITICAL_EVIDENCE_LOSS),
                        "operational_drift_rate": 0.5,
                        "replay_consistency": 0.5,
                    }
                ],
                "fixture_id": "alpha_paper",
                "fixture_kind": "paper",
                "stop_reason": "min_replay_consistency",
            },
        ],
    }


def test_replay_degradation_summary_output_is_deterministic() -> None:
    artifact = _artifact()
    assert render_replay_degradation_summary(artifact) == render_replay_degradation_summary(artifact)
    assert summarize_replay_degradation_artifact(artifact) == summarize_replay_degradation_artifact(artifact)


def test_replay_degradation_summary_formatting_is_stable() -> None:
    rendered = render_replay_degradation_summary(_artifact())
    assert rendered.endswith("\n")
    assert "# Iterative Replay Degradation CI Summary\n" in rendered
    assert "Severity: CRITICAL\n" in rendered
    assert "| total fixtures | 2 |" in rendered
    assert "| collapse rate | 0.500000 |" in rendered
    assert "| average replay consistency | 0.625000 |" in rendered
    assert "| average operational drift rate | 0.375000 |" in rendered
    assert "| highest collapse cycle observed | 3 |" in rendered
    assert (
        "| fixture_id | fixture_kind | collapsed | collapse_cycle | final_cycle | final_replay_consistency | "
        "final_operational_drift_rate | stop_reason | failure_labels |"
    ) in rendered
    assert rendered.index("| zeta_trace | agent_trace |") < rendered.index("| alpha_paper | paper |")


def test_replay_degradation_summary_handles_empty_artifact() -> None:
    rendered = render_replay_degradation_summary({"runs": []})
    summary = summarize_replay_degradation_artifact({"runs": []})
    assert summary["severity"] == SEVERITY_INFO
    assert summary["total_fixtures"] == 0
    assert summary["collapsed_fixtures"] == 0
    assert summary["collapse_rate"] == 0.0
    assert summary["average_replay_consistency"] is None
    assert summary["average_operational_drift_rate"] is None
    assert summary["highest_collapse_cycle_observed"] is None
    assert "| average replay consistency | N/A |" in rendered
    assert "| average operational drift rate | N/A |" in rendered
    assert "| N/A | N/A | false | N/A | N/A | N/A | N/A | N/A | none |" in rendered


def test_replay_degradation_summary_tolerates_additive_fields() -> None:
    artifact = _artifact()
    artifact["artifact_version"] = "future-compatible"
    artifact["runs"][0]["review_note"] = "ignored additive run metadata"
    artifact["runs"][0]["cycles"][-1]["extra_metric"] = 0.123456

    summary = summarize_replay_degradation_artifact(artifact)
    rendered = render_replay_degradation_summary(artifact)

    assert summary["total_fixtures"] == 2
    assert summary["failure_mode_counts"][CONSTRAINT_DRIFT] == 1
    assert "extra_metric" not in rendered
    assert "| zeta_trace | agent_trace |" in rendered


def test_replay_degradation_summary_severity_classification() -> None:
    assert (
        classify_replay_degradation_severity(
            collapsed_fixtures=0,
            average_replay_consistency=1.0,
            average_operational_drift_rate=0.0,
            failure_mode_counts=_counts(),
        )
        == SEVERITY_INFO
    )
    assert (
        classify_replay_degradation_severity(
            collapsed_fixtures=0,
            average_replay_consistency=1.0,
            average_operational_drift_rate=0.0,
            failure_mode_counts=_counts(BLOCKER_DETACHMENT),
        )
        == SEVERITY_WARNING
    )
    assert (
        classify_replay_degradation_severity(
            collapsed_fixtures=0,
            average_replay_consistency=0.999999,
            average_operational_drift_rate=0.0,
            failure_mode_counts=_counts(),
        )
        == SEVERITY_WARNING
    )
    assert (
        classify_replay_degradation_severity(
            collapsed_fixtures=1,
            average_replay_consistency=1.0,
            average_operational_drift_rate=0.0,
            failure_mode_counts=_counts(),
        )
        == SEVERITY_CRITICAL
    )


def test_replay_degradation_summary_aggregates_failure_counts() -> None:
    summary = summarize_replay_degradation_artifact(_artifact())
    assert summary["failure_mode_counts"] == {
        EVIDENCE_LOSS: 1,
        HIGH_CRITICAL_EVIDENCE_LOSS: 1,
        CONSTRAINT_DRIFT: 1,
        BLOCKER_DETACHMENT: 0,
    }
    rendered = render_replay_degradation_summary(_artifact())
    assert (
        "| aggregated failure_mode_counts | "
        "EVIDENCE_LOSS=1, HIGH_CRITICAL_EVIDENCE_LOSS=1, CONSTRAINT_DRIFT=1, BLOCKER_DETACHMENT=0 |"
    ) in rendered


def test_local_ci_entrypoint_default_output_paths_are_stable() -> None:
    from scripts.generate_iterative_replay_degradation_artifacts import (
        DEFAULT_ARTIFACT_PATH,
        DEFAULT_SUMMARY_PATH,
        stable_output_path,
    )

    assert (
        stable_output_path(DEFAULT_ARTIFACT_PATH)
        == "artifacts/iterative_replay_degradation_results.json"
    )
    assert (
        stable_output_path(DEFAULT_SUMMARY_PATH)
        == "artifacts/iterative_replay_degradation_results.summary.md"
    )


def test_local_ci_entrypoint_generates_artifact_and_summary(tmp_path) -> None:
    import json

    from scripts.generate_iterative_replay_degradation_artifacts import (
        generate_replay_degradation_ci_artifacts,
    )

    artifact_path = tmp_path / "iterative_replay_degradation_results.json"
    summary_path = tmp_path / "iterative_replay_degradation_results.summary.md"

    paths = generate_replay_degradation_ci_artifacts(
        artifact_path=artifact_path,
        summary_path=summary_path,
    )

    assert paths.artifact_path == artifact_path
    assert paths.summary_path == summary_path
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    summary = summary_path.read_text(encoding="utf-8")
    assert artifact["benchmark"] == "iterative_replay_degradation_bench"
    assert artifact["runs"]
    assert summary.startswith("# Iterative Replay Degradation CI Summary\n")
    assert "| total fixtures |" in summary


def test_local_ci_entrypoint_exit_behavior_is_stable(tmp_path, capsys) -> None:
    from scripts.generate_iterative_replay_degradation_artifacts import main

    artifact_path = tmp_path / "degradation.json"
    summary_path = tmp_path / "degradation.summary.md"

    assert (
        main(
            [
                "--artifact-path",
                str(artifact_path),
                "--summary-path",
                str(summary_path),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()

    assert captured.out == (
        f"artifact_path={artifact_path.resolve().as_posix()}\n"
        f"summary_path={summary_path.resolve().as_posix()}\n"
    )
    assert captured.err == ""
    assert artifact_path.is_file()
    assert summary_path.is_file()


def test_replay_degradation_comparison_markdown_is_stable_and_ordered() -> None:
    from tests.utils.iterative_replay_degradation_runner import build_comparative_replay_degradation_artifact

    artifact = build_comparative_replay_degradation_artifact()
    rendered = render_replay_degradation_summary(artifact)

    assert rendered == render_replay_degradation_summary(artifact)
    assert rendered.startswith("# Iterative Replay Degradation CI Summary\n")
    assert "## Compression profile comparison" in rendered
    assert (
        "| profile | collapse_rate | average_replay_consistency | average_operational_drift_rate | "
        "average_evidence_survival_rate | aggregated_failure_labels |"
    ) in rendered
    assert rendered.index("| CONSERVATIVE |") < rendered.index("| BALANCED |") < rendered.index("| AGGRESSIVE |")
    assert "| CONSERVATIVE | 0.000000 | 0.895833 | 0.104167 | 0.916667 | EVIDENCE_LOSS |" in rendered
    assert (
        "| BALANCED | 0.000000 | 0.250000 | 0.750000 | 0.166667 | "
        "EVIDENCE_LOSS,CONSTRAINT_DRIFT |"
    ) in rendered
    assert (
        "| AGGRESSIVE | 0.000000 | 0.125000 | 0.875000 | 0.083333 | "
        "EVIDENCE_LOSS,CONSTRAINT_DRIFT,BLOCKER_DETACHMENT |"
    ) in rendered


def test_replay_degradation_comparison_tolerates_additive_schema_fields() -> None:
    from tests.utils.iterative_replay_degradation_runner import build_comparative_replay_degradation_artifact

    artifact = build_comparative_replay_degradation_artifact()
    artifact["artifact_version"] = "future-compatible"
    artifact["profiles"][0]["aggregate"]["future_metric"] = 1.0
    artifact["profiles"][0]["runs"][0]["future_run_field"] = "ignored"

    rendered = render_replay_degradation_summary(artifact)

    assert "future_metric" not in rendered
    assert "future_run_field" not in rendered
    assert "| CONSERVATIVE | 0.000000 | 0.895833 |" in rendered


def test_replay_sensitivity_markdown_is_stable_and_ordered() -> None:
    from tests.utils.iterative_replay_degradation_runner import build_iterative_replay_degradation_artifact

    artifact = build_iterative_replay_degradation_artifact()
    rendered = render_replay_degradation_summary(artifact)

    assert rendered == render_replay_degradation_summary(artifact)
    assert "## Replay sensitivity analysis" in rendered
    assert (
        "| case_id | max_context_units | max_families | max_bursts | replay_window_seconds | "
        "replay_cycles | compression_budget_scale | replay_consistency | operational_drift_rate | "
        "evidence_survival_rate | collapse_rate | aggregated_failure_labels |"
    ) in rendered
    assert rendered.index("| baseline_budget |") < rendered.index("| budget_scale_0_75 |")
    assert rendered.index("| budget_scale_0_75 |") < rendered.index("| budget_scale_0_50 |")
    assert rendered.index("| budget_scale_0_50 |") < rendered.index("| extended_replay_cycles |")
    assert (
        "| baseline_budget | 96 | 24 | 24 | 900 | 3 | 1.000000 | 0.708333 | "
        "0.291667 | 0.750000 | 0.000000 | EVIDENCE_LOSS |"
    ) in rendered
