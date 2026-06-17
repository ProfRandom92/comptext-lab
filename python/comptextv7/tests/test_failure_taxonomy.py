from __future__ import annotations

import json
from pathlib import Path

from src.validation.failure_taxonomy import BANNED_FUZZY_TERMS, FAILURE_TAXONOMY


ROOT = Path(__file__).resolve().parent.parent


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_fixture_failure_labels() -> set[str]:
    labels: set[str] = set()
    for path in sorted((ROOT / "fixtures").glob("**/expected/failures.json")):
        payload = _load_json(path)
        if not isinstance(payload, dict):
            continue
        for key in ("expected_failures", "allowed_failures", "disallowed_failures"):
            values = payload.get(key, [])
            if isinstance(values, list):
                labels.update(str(value) for value in values)
    return labels


def _collect_artifact_failure_labels() -> set[str]:
    labels: set[str] = set()
    for path in sorted((ROOT / "artifacts").glob("*.json")):
        payload = _load_json(path)

        def walk(value: object) -> None:
            if isinstance(value, dict):
                for key, nested in value.items():
                    if key == "failure_labels" and isinstance(nested, list):
                        labels.update(str(item) for item in nested)
                    walk(nested)
            elif isinstance(value, list):
                for nested in value:
                    walk(nested)

        walk(payload)
    return labels


def test_fixture_expected_failure_labels_are_registered() -> None:
    fixture_labels = _collect_fixture_failure_labels()
    missing = sorted(label for label in fixture_labels if label not in FAILURE_TAXONOMY)
    assert not missing, f"fixture labels missing from failure taxonomy: {missing}"


def test_artifact_failure_labels_are_registered() -> None:
    artifact_labels = _collect_artifact_failure_labels()
    missing = sorted(label for label in artifact_labels if label not in FAILURE_TAXONOMY)
    assert not missing, f"artifact labels missing from failure taxonomy: {missing}"


def test_registered_labels_have_required_operational_fields() -> None:
    required_fields = (
        "operational_meaning",
        "observable_trigger",
        "contract_or_invariant_type",
        "severity_class",
        "non_goal",
    )
    for label, spec in FAILURE_TAXONOMY.items():
        for field in required_fields:
            value = spec.get(field, "")
            assert isinstance(value, str) and value.strip(), f"label {label} missing required field {field}"


def test_registered_labels_do_not_use_banned_fuzzy_terms() -> None:
    for label in FAILURE_TAXONOMY:
        normalized = label.lower()
        for banned in BANNED_FUZZY_TERMS:
            assert banned not in normalized, f"label '{label}' contains banned fuzzy term '{banned}'"


def test_capability_security_expansion_labels_are_registered() -> None:
    expected_labels = {
        "CAPABILITY_BOUNDARY_LOSS",
        "UNAUTHORIZED_CAPABILITY_PATH",
        "APPROVAL_GATE_LOSS",
        "POLICY_ENFORCEMENT_GAP",
    }
    missing = sorted(label for label in expected_labels if label not in FAILURE_TAXONOMY)
    assert not missing, f"expected capability/security labels missing from taxonomy: {missing}"
