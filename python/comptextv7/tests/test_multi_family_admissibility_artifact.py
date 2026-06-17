from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_multi_family_admissibility_artifact import (
    ARTIFACT_ID,
    generate_multi_family_admissibility_artifact,
)

ARTIFACT_PATH = Path("artifacts/multi_family_admissibility_results.json")
SINGLE_FAMILY_ARTIFACT_PATH = Path("artifacts/layered_admissibility_results.json")
EXPECTED_FAMILIES = ["coding_workflow_pr_review", "cross_domain_operational_dependency_workflow", "incident_response_page_triage", "mcp_trace_replay"]
EXPECTED_LEVEL_ORDER = ["baseline", "mild", "moderate", "severe"]
MANIFEST_PATH = Path("fixtures/manifest.json")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_level_index() -> dict[str, str]:
    manifest = _load_json(MANIFEST_PATH)
    return {entry["fixture_id"]: entry["degradation_level"] for entry in manifest["fixtures"]}


def test_script_output_matches_committed_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "multi_family_admissibility_results.json"
    generate_multi_family_admissibility_artifact(output_path)

    assert _load_json(output_path) == _load_json(ARTIFACT_PATH)


def test_artifact_has_stable_schema_no_time_or_environment_fields() -> None:
    payload = _load_json(ARTIFACT_PATH)
    assert payload["artifact_id"] == ARTIFACT_ID
    assert set(payload.keys()) == {"artifact_id", "generated_by", "version", "families"}


def test_families_are_sorted_and_expected_families_present() -> None:
    payload = _load_json(ARTIFACT_PATH)
    families = payload["families"]
    names = [entry["family"] for entry in families]

    assert names == sorted(names)
    assert names == EXPECTED_FAMILIES


def test_each_family_curve_has_four_points_and_standard_level_order() -> None:
    payload = _load_json(ARTIFACT_PATH)

    fixture_to_level = _manifest_level_index()

    for family_payload in payload["families"]:
        points = family_payload["curve"]["points"]
        assert len(points) == 4
        levels = [fixture_to_level[point["fixture_id"]] for point in points]
        assert levels == EXPECTED_LEVEL_ORDER


def test_coding_workflow_curve_remains_compatible_with_single_family_artifact() -> None:
    multi_family = _load_json(ARTIFACT_PATH)
    single_family = _load_json(SINGLE_FAMILY_ARTIFACT_PATH)

    coding_family = next(entry for entry in multi_family["families"] if entry["family"] == "coding_workflow_pr_review")
    assert coding_family["curve"] == single_family


def test_repeated_generation_is_stable(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    generate_multi_family_admissibility_artifact(first)
    generate_multi_family_admissibility_artifact(second)

    assert _load_json(first) == _load_json(second)
