"""Deterministic entrypoint for replay semantic integrity artifact regeneration."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.validation.contract_validator import ContractType, ContractValidator, Layer

MANIFEST_PATH = REPO_ROOT / "fixtures" / "manifest.json"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "replay_semantic_integrity_results.json"

ARTIFACT_ID = "replay_semantic_integrity_results_v1"
LEVELS = ("baseline", "mild", "moderate", "severe")
COMMITMENT_CLASS_ORDER = (
    "evidence",
    "constraints",
    "dependencies",
    "recovery_paths",
    "tool_order",
    "capability_boundaries",
    "governance_or_policy",
    "invariants",
)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _family_order_and_counts() -> tuple[list[str], dict[str, int]]:
    manifest = _load_json(MANIFEST_PATH)
    fixtures = manifest["fixtures"]
    family_order: list[str] = []
    fixture_counts: dict[str, int] = {}

    for entry in fixtures:
        family = entry["family"]
        if family not in fixture_counts:
            family_order.append(family)
            fixture_counts[family] = 0
        fixture_counts[family] += 1

    return family_order, fixture_counts


def _class_for_contract(contract_id: str, contract_type: ContractType, layer: Layer) -> str:
    contract = contract_id.lower()

    if any(token in contract for token in ("capability", "boundary")):
        return "capability_boundaries"
    if any(token in contract for token in ("policy", "governance", "approval")):
        return "governance_or_policy"
    if any(token in contract for token in ("recovery", "rollback", "escalation")):
        return "recovery_paths"
    if any(token in contract for token in ("dependency", "causal", "chain")):
        return "dependencies"
    if any(token in contract for token in ("order", "ordering", "sequence", "tool_call_order")):
        return "tool_order"
    if any(token in contract for token in ("invariant", "orphan")):
        return "invariants"
    if any(token in contract for token in ("evidence",)):
        return "evidence"
    if any(token in contract for token in ("constraint", "validation")):
        return "constraints"

    if contract_type == ContractType.CAUSALITY:
        return "dependencies"
    if contract_type == ContractType.REACHABILITY:
        return "recovery_paths"
    if contract_type == ContractType.ORDERING:
        return "governance_or_policy" if layer == Layer.GOVERNANCE else "tool_order"
    if contract_type == ContractType.INVARIANT:
        return "invariants"

    return "constraints"


def generate_replay_semantic_integrity_artifact(output_path: Path = OUTPUT_PATH) -> Path:
    manifest = _load_json(MANIFEST_PATH)
    fixtures = manifest["fixtures"]
    family_order, fixture_counts = _family_order_and_counts()

    families_payload: list[dict[str, object]] = []
    total_fixture_count = 0

    for family in family_order:
        family_fixtures = [entry for entry in fixtures if entry["family"] == family]
        points = sorted(family_fixtures, key=lambda entry: LEVELS.index(entry["degradation_level"]))

        commitment_classes: dict[str, dict[str, object]] = {
            commitment_class: {"passed": 0, "failed": 0, "failure_labels": set()}
            for commitment_class in COMMITMENT_CLASS_ORDER
        }

        for fixture_entry in points:
            fixture_path = REPO_ROOT / str(fixture_entry["path"])
            original: dict[str, Any] = {
                **_load_json(fixture_path / "original/trace.json"),
                **_load_json(fixture_path / "original/state.json"),
                "dependency_graph": _load_json(fixture_path / "original/dependency_graph.json"),
            }
            reconstructed: dict[str, Any] = {
                **_load_json(fixture_path / "reconstructed/trace.json"),
                **_load_json(fixture_path / "reconstructed/state.json"),
                "dependency_graph": _load_json(fixture_path / "reconstructed/dependency_graph.json"),
            }
            contracts_dir = fixture_path / "original/contracts"
            contracts_by_id = {
                contract["contract_id"]: contract for contract in (_load_json(path) for path in sorted(contracts_dir.glob("*.json")))
            }
            contracts = [contracts_by_id[contract_id] for contract_id in fixture_entry["contracts"]]
            results = ContractValidator().validate_contracts(original=original, reconstructed=reconstructed, contracts=contracts)

            for result in results:
                commitment_class = _class_for_contract(result.contract_id, result.contract_type, result.layer)
                if not result.passed:
                    commitment_classes[commitment_class]["failed"] += 1
                    if result.failure_label is not None:
                        commitment_classes[commitment_class]["failure_labels"].add(result.failure_label)
                else:
                    commitment_classes[commitment_class]["passed"] += 1

        serializable_classes: dict[str, dict[str, object]] = {}
        for commitment_class in COMMITMENT_CLASS_ORDER:
            values = commitment_classes[commitment_class]
            serializable_classes[commitment_class] = {
                "passed": values["passed"],
                "failed": values["failed"],
                "failure_labels": sorted(values["failure_labels"]),
            }

        families_payload.append(
            {
                "family": family,
                "fixture_count": fixture_counts[family],
                "levels": list(LEVELS),
                "commitment_classes": serializable_classes,
            }
        )
        total_fixture_count += fixture_counts[family]

    payload = {
        "artifact_id": ARTIFACT_ID,
        "generated_by": "ReplaySemanticIntegrityArtifactGenerator",
        "version": "1.0",
        "evaluation_mode": "deterministic",
        "llm_judges": "none",
        "external_apis": "none",
        "families": families_payload,
        "global_summary": {
            "family_count": len(families_payload),
            "fixture_count": total_fixture_count,
            "deterministic_evaluation": True,
            "llm_judges": "none",
            "external_apis": "none",
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    output_path = generate_replay_semantic_integrity_artifact()
    print(output_path.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
