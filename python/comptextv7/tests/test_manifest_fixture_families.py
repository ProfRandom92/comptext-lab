from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from src.validation.admissibility_scorer import AdmissibilityScorer
from src.validation.contract_validator import ContractValidator


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "fixtures" / "manifest.json"
REQUIRED_LEVELS = ("baseline", "mild", "moderate", "severe")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_manifest_entries() -> list[dict[str, object]]:
    manifest = _load_json(MANIFEST_PATH)
    fixtures = manifest["fixtures"]
    assert isinstance(fixtures, list)
    return sorted(
        fixtures,
        key=lambda entry: (
            str(entry["family"]),
            REQUIRED_LEVELS.index(str(entry["degradation_level"])),
            str(entry["fixture_id"]),
        ),
    )


def _group_by_family(entries: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for entry in entries:
        grouped[str(entry["family"])].append(entry)
    return {
        family: sorted(
            grouped[family],
            key=lambda entry: REQUIRED_LEVELS.index(str(entry["degradation_level"])),
        )
        for family in sorted(grouped)
    }


def _load_validation_payload(fixture_root: Path) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    original = {
        **_load_json(fixture_root / "original" / "trace.json"),
        **_load_json(fixture_root / "original" / "state.json"),
        "dependency_graph": _load_json(fixture_root / "original" / "dependency_graph.json"),
    }
    reconstructed = {
        **_load_json(fixture_root / "reconstructed" / "trace.json"),
        **_load_json(fixture_root / "reconstructed" / "state.json"),
        "dependency_graph": _load_json(fixture_root / "reconstructed" / "dependency_graph.json"),
    }
    contracts = [_load_json(path) for path in sorted((fixture_root / "original" / "contracts").glob("*.json"))]
    return original, reconstructed, contracts


def test_manifest_fixture_families_have_expected_levels_and_unique_ids_paths() -> None:
    family_groups = _group_by_family(_load_manifest_entries())

    for family in sorted(family_groups):
        entries = family_groups[family]
        assert [str(entry["degradation_level"]) for entry in entries] == list(REQUIRED_LEVELS)

        paths = [str(entry["path"]) for entry in entries]
        fixture_ids = [str(entry["fixture_id"]) for entry in entries]
        assert len(paths) == len(set(paths)), f"Duplicate fixture paths in family '{family}'"
        assert len(fixture_ids) == len(set(fixture_ids)), f"Duplicate fixture_ids in family '{family}'"

        levels = {str(entry["degradation_level"]): entry for entry in entries}
        assert levels["baseline"]["expected_admissible"] is True
        assert levels["severe"]["expected_admissible"] is False


def test_manifest_entries_are_structurally_consistent_with_expected_files() -> None:
    for entry in _load_manifest_entries():
        fixture_root = ROOT / str(entry["path"])
        contracts_dir = fixture_root / "original" / "contracts"

        assert fixture_root.exists(), f"Missing fixture directory: {fixture_root}"
        assert (fixture_root / "expected" / "admissibility.json").exists()
        assert (fixture_root / "expected" / "failures.json").exists()
        assert contracts_dir.exists()

        for contract_id in sorted(entry["contracts"]):
            assert (contracts_dir / f"{contract_id}.json").exists(), f"Missing contract file for {contract_id}"

        failures = _load_json(fixture_root / "expected" / "failures.json")
        assert sorted(entry["expected_failure_labels"]) == sorted(failures.get("expected_failures", []))


def test_baseline_and_severe_fixture_behavior_matches_manifest_expectations() -> None:
    family_groups = _group_by_family(_load_manifest_entries())
    validator = ContractValidator()
    scorer = AdmissibilityScorer()

    for family in sorted(family_groups):
        levels = {str(entry["degradation_level"]): entry for entry in family_groups[family]}

        baseline = levels["baseline"]
        baseline_root = ROOT / str(baseline["path"])
        baseline_original, baseline_reconstructed, baseline_contracts = _load_validation_payload(baseline_root)
        baseline_results = validator.validate_contracts(
            original=baseline_original,
            reconstructed=baseline_reconstructed,
            contracts=baseline_contracts,
        )
        baseline_score = scorer.score(baseline_results, expected_admissible=bool(baseline["expected_admissible"]))

        assert baseline_score.observed_admissible is True
        assert all(result.passed for result in baseline_results)

        severe = levels["severe"]
        severe_root = ROOT / str(severe["path"])
        severe_original, severe_reconstructed, severe_contracts = _load_validation_payload(severe_root)
        severe_results = validator.validate_contracts(
            original=severe_original,
            reconstructed=severe_reconstructed,
            contracts=severe_contracts,
        )
        severe_score = scorer.score(severe_results, expected_admissible=bool(severe["expected_admissible"]))

        assert severe_score.observed_admissible is False
        assert any(not result.passed for result in severe_results)

        expected_failure_labels = sorted(severe["expected_failure_labels"])
        observed_failure_labels = sorted({result.failure_label for result in severe_results if result.failure_label is not None})
        assert observed_failure_labels == expected_failure_labels
