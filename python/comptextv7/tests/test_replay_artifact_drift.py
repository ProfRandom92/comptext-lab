"""Drift tests for committed deterministic replay artifacts and summaries."""

from scripts.validate_replay_artifact_drift import run_drift_checks


def test_committed_replay_artifacts_and_published_values_match_generators() -> None:
    failures = run_drift_checks()
    assert not failures, "\n\n".join(failure.format() for failure in failures)
