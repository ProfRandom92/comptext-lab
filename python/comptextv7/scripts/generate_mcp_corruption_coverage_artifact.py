"""Generate deterministic MCP corruption corpus coverage artifact."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.validation.contract_validator import ContractValidator
from src.validation.failure_taxonomy import FAILURE_TAXONOMY

MANIFEST_PATH = REPO_ROOT / "artifacts" / "mcp_trace_corruption_manifest.json"
MATERIALIZED_ROOT = REPO_ROOT / "fixtures" / "mcp_trace_replay_corruptions"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "mcp_corruption_coverage.json"
REQUIRED_FILES = ("trace.json", "dependency_graph.json", "state.json")


def _repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _load_json(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"missing required file: {_repo_relative(path)}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON in {_repo_relative(path)}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"expected JSON object in {_repo_relative(path)}")
    return data


def _load_contracts(contracts_dir: Path) -> list[dict[str, object]]:
    if not contracts_dir.exists():
        raise RuntimeError(f"missing contracts directory: {_repo_relative(contracts_dir)}")
    contracts: list[dict[str, object]] = []
    for path in sorted(contracts_dir.glob("*.json")):
        contract = _load_json(path)
        contracts.append(contract)
    if not contracts:
        raise RuntimeError(f"no contracts found in {_repo_relative(contracts_dir)}")
    return contracts


def _load_fixture_document(fixture_dir: Path) -> dict[str, object]:
    doc: dict[str, object] = {}
    for name in REQUIRED_FILES:
        path = fixture_dir / name
        key = "events" if name == "trace.json" else name.removesuffix(".json")
        parsed = _load_json(path)
        if name == "trace.json":
            events = parsed.get("events")
            if events is None:
                events = []
            if not isinstance(events, list):
                raise RuntimeError(f"trace missing 'events' list: {_repo_relative(path)}")
            for event in events:
                if not isinstance(event, dict):
                    raise RuntimeError(f"malformed event in trace: {_repo_relative(path)}")
            doc["events"] = events
        else:
            doc[key] = parsed
    return doc


def _validate_entry_structure(entry: dict[str, object]) -> None:
    required = ("corruption_id", "source_fixture", "operator", "expected_failure_label")
    for field in required:
        value = entry.get(field)
        if not isinstance(value, str) or not value:
            raise RuntimeError(f"invalid corruption entry field '{field}': {entry}")


def generate_mcp_corruption_coverage_artifact(output_path: Path = OUTPUT_PATH) -> dict[str, object]:
    manifest = _load_json(MANIFEST_PATH)
    corruptions = manifest.get("corruptions")
    if corruptions is None:
        corruptions = []
    if not isinstance(corruptions, list):
        raise RuntimeError(f"manifest corruptions must be a list: {_repo_relative(MANIFEST_PATH)}")
    for corruption in corruptions:
        if not isinstance(corruption, dict):
            raise RuntimeError(f"malformed corruption in manifest: {_repo_relative(MANIFEST_PATH)}")

    validator = ContractValidator()
    operator_counter: Counter[str] = Counter()
    family_counter: Counter[str] = Counter()
    label_counter: Counter[str] = Counter()
    records: list[dict[str, object]] = []

    for raw_entry in sorted(corruptions, key=lambda item: str(item.get("corruption_id", ""))):
        _validate_entry_structure(raw_entry)

        corruption_id = str(raw_entry["corruption_id"])
        source_fixture = str(raw_entry["source_fixture"])
        operator = str(raw_entry["operator"])
        expected_failure_label = str(raw_entry["expected_failure_label"])

        if expected_failure_label not in FAILURE_TAXONOMY:
            raise RuntimeError(f"expected_failure_label not registered in FAILURE_TAXONOMY: {expected_failure_label}")

        fixture_family = Path(source_fixture).name
        operator_slug = corruption_id.split("::", maxsplit=1)
        if len(operator_slug) != 2 or not operator_slug[1]:
            raise RuntimeError(f"invalid corruption_id format: {corruption_id}")
        materialized_fixture = f"fixtures/mcp_trace_replay_corruptions/{fixture_family}/{operator_slug[1]}"

        source_original = REPO_ROOT / source_fixture / "original"
        materialized_dir = REPO_ROOT / materialized_fixture
        contracts_dir = source_original / "contracts"

        original_doc = _load_fixture_document(source_original)
        reconstructed_doc = _load_fixture_document(materialized_dir)
        contracts = _load_contracts(contracts_dir)
        results = validator.validate_contracts(original=original_doc, reconstructed=reconstructed_doc, contracts=contracts)

        observed_labels = sorted({r.failure_label for r in results if (not r.passed and r.failure_label is not None)})
        failing_contracts = sorted(r.contract_id for r in results if not r.passed)
        expected_emitted = expected_failure_label in observed_labels
        adapter_gap = not expected_emitted
        if adapter_gap:
            raise RuntimeError(
                f"adapter gap detected for {corruption_id}: expected label {expected_failure_label} not emitted"
            )

        evidence_keys = sorted(
            {
                key
                for r in results
                if not r.passed
                for key in r.deterministic_evidence
            }
        )

        records.append(
            {
                "corruption_id": corruption_id,
                "source_fixture": source_fixture,
                "materialized_fixture": materialized_fixture,
                "operator": operator,
                "expected_failure_label": expected_failure_label,
                "observed_failure_labels": observed_labels,
                "native_contract_covered": expected_emitted,
                "adapter_gap": adapter_gap,
                "contracts_evaluated": len(contracts),
                "failing_contracts": failing_contracts,
                "deterministic_evidence_keys": evidence_keys,
            }
        )

        operator_counter[operator] += 1
        family_counter[fixture_family] += 1
        label_counter[expected_failure_label] += 1

    total = len(records)
    native_covered = sum(1 for r in records if r["native_contract_covered"])
    adapter_gaps = sum(1 for r in records if r["adapter_gap"])
    coverage_ratio = 0.0 if total == 0 else native_covered / total

    if adapter_gaps != 0 or native_covered != total:
        raise RuntimeError(f"coverage invariant failed: native_covered={native_covered}, total={total}, adapter_gaps={adapter_gaps}")

    artifact: dict[str, object] = {
        "artifact_name": "mcp_corruption_coverage",
        "schema_version": "1.0",
        "deterministic": True,
        "source_manifest": "artifacts/mcp_trace_corruption_manifest.json",
        "coverage_summary": {
            "total_corruptions": total,
            "native_contract_covered": native_covered,
            "adapter_gaps": adapter_gaps,
            "operator_count": len(operator_counter),
            "fixture_family_count": len(family_counter),
            "failure_label_count": len(label_counter),
            "coverage_ratio": coverage_ratio,
        },
        "operator_coverage": dict(sorted(operator_counter.items())),
        "fixture_family_coverage": dict(sorted(family_counter.items())),
        "failure_label_coverage": dict(sorted(label_counter.items())),
        "entries": records,
    }

    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


if __name__ == "__main__":
    generate_mcp_corruption_coverage_artifact()
