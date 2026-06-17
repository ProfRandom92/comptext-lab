from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "fixtures" / "manifest.json"
ALLOWED_DEGRADATION_LEVELS = ["baseline", "mild", "moderate", "severe"]
EXPECTED_FIXTURE_ORDER = [
    "coding_workflow_pr_review_v1",
    "coding_workflow_pr_review_mild_v1",
    "coding_workflow_pr_review_moderate_v1",
    "coding_workflow_pr_review_degraded_v1",
    "incident_response_page_triage_v1",
    "incident_response_page_triage_mild_v1",
    "incident_response_page_triage_moderate_v1",
    "incident_response_page_triage_degraded_v1",
    "cross_domain_operational_dependency_workflow_v1",
    "cross_domain_operational_dependency_workflow_mild_v1",
    "cross_domain_operational_dependency_workflow_moderate_v1",
    "cross_domain_operational_dependency_workflow_degraded_v1",
    "mcp_trace_replay_v1",
    "mcp_trace_replay_mild_v1",
    "mcp_trace_replay_moderate_v1",
    "mcp_trace_replay_degraded_v1",
]


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_manifest() -> dict:
    return _load_json(MANIFEST_PATH)


def test_manifest_is_json_serializable_and_sorted() -> None:
    manifest = _load_manifest()
    json.dumps(manifest, sort_keys=True)

    fixture_ids = [entry["fixture_id"] for entry in manifest["fixtures"]]
    assert fixture_ids == EXPECTED_FIXTURE_ORDER


def test_manifest_paths_exist() -> None:
    manifest = _load_manifest()
    required_paths = [
        Path("original/trace.json"),
        Path("original/state.json"),
        Path("original/dependency_graph.json"),
        Path("original/contracts"),
        Path("reconstructed/trace.json"),
        Path("reconstructed/state.json"),
        Path("reconstructed/dependency_graph.json"),
        Path("expected/admissibility.json"),
        Path("expected/failures.json"),
        Path("README.md"),
    ]

    for entry in manifest["fixtures"]:
        fixture_dir = ROOT / entry["path"]
        assert fixture_dir.exists(), f"Missing fixture directory: {fixture_dir}"
        for rel_path in required_paths:
            assert (fixture_dir / rel_path).exists(), f"Missing path: {fixture_dir / rel_path}"


def test_manifest_matches_fixture_admissibility_metadata() -> None:
    manifest = _load_manifest()

    for entry in manifest["fixtures"]:
        admissibility = _load_json(ROOT / entry["path"] / "expected" / "admissibility.json")
        assert entry["fixture_id"] == admissibility["fixture_id"]
        assert entry["fixture_version"] == admissibility["fixture_version"]
        assert entry["expected_admissible"] == admissibility["expected_admissible"]
        assert entry["expected_failure_labels"] == sorted(admissibility.get("expected_failure_labels", []))


def test_manifest_contracts_match_contract_files() -> None:
    manifest = _load_manifest()

    for entry in manifest["fixtures"]:
        contracts_dir = ROOT / entry["path"] / "original" / "contracts"
        contract_ids = []
        for contract_file in sorted(contracts_dir.glob("*.json")):
            contract_ids.append(_load_json(contract_file)["contract_id"])
        assert sorted(contract_ids) == entry["contracts"]


def test_manifest_expected_failure_labels_match_failures_file() -> None:
    manifest = _load_manifest()

    for entry in manifest["fixtures"]:
        failures = _load_json(ROOT / entry["path"] / "expected" / "failures.json")
        assert entry["expected_failure_labels"] == sorted(failures.get("expected_failures", []))


def test_benchmark_artifact_references_only_manifest_fixtures() -> None:
    manifest = _load_manifest()
    benchmark = _load_json(ROOT / "artifacts" / "layered_admissibility_results.json")

    manifest_index = {
        entry["fixture_id"]: {
            "fixture_version": entry["fixture_version"],
            "path": entry["path"],
        }
        for entry in manifest["fixtures"]
    }

    for point in benchmark["points"]:
        fixture_id = point["fixture_id"]
        assert fixture_id in manifest_index
        assert point["fixture_version"] == manifest_index[fixture_id]["fixture_version"]
        assert point["fixture_path"] == manifest_index[fixture_id]["path"]


def test_degradation_levels_are_known_and_unique_per_family() -> None:
    manifest = _load_manifest()
    family_to_levels: dict[str, set[str]] = {}

    for entry in manifest["fixtures"]:
        level = entry["degradation_level"]
        family = entry["family"]
        assert level in ALLOWED_DEGRADATION_LEVELS
        family_to_levels.setdefault(family, set())
        assert level not in family_to_levels[family]
        family_to_levels[family].add(level)


def test_no_unregistered_fixture_directories() -> None:
    manifest = _load_manifest()
    registered_paths = {entry["path"] for entry in manifest["fixtures"]}

    discovered_fixture_paths = {
        str(path.parent.parent.relative_to(ROOT)).replace("\\", "/")
        for path in (ROOT / "fixtures").glob("*/expected/admissibility.json")
    }

    assert discovered_fixture_paths.issubset(registered_paths)
